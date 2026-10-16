"""
main.py — Create Spotify playlists from a long message, one playlist per chunk.

Usage:
    python main.py --file message.txt            # recommended for long messages
    python main.py                               # paste message, then Ctrl+D
    python main.py --file message.txt --title "Para Camila"
    python main.py --test                        # reuse TEST_PLAYLIST_IDS
    python main.py --file unsent.txt --start 4   # resume after a failure
"""

import argparse
import base64
import io
import sys
import time
from pathlib import Path

import requests
import spotipy
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth

from config import (
    IMAGES_FOLDER, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES,
    TEST_PLAYLIST_IDS, TITLE_MAX, REQUEST_TIMEOUT, MAX_RETRIES,
    DELAY_BETWEEN_PLAYLISTS, COVER_MAX_BYTES,
)
from image_registry import (
    load_log, is_used, append_entry, delete_image, compute_phash,
)
from message_processor import build_playlist_specs

UNSENT_FILE = Path("unsent.txt")


def get_client():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
        ),
        requests_timeout=REQUEST_TIMEOUT,
    )


def read_message(path):
    """Read from a file (reliable for long text) or from stdin until Ctrl+D."""
    if path:
        return Path(path).read_text(encoding="utf-8").strip()
    print("Paste your message, then press Enter and Ctrl+D:")
    return sys.stdin.read().strip()


def encode_image(image_path):
    """Return a base64 JPEG under Spotify's size limit, shrinking if needed."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img.thumbnail((640, 640))
        for quality in (90, 80, 70, 60, 50):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            data = base64.b64encode(buf.getvalue())
            if len(data) <= COVER_MAX_BYTES:
                return data.decode("utf-8")
    raise ValueError(f"{image_path.name} is too big even at lowest quality")


def with_retries(fn, *args, **kwargs):
    """Call fn, retrying on timeouts, connection errors and 429/5xx."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            err = e
        except spotipy.SpotifyException as e:
            if e.http_status not in (429, 500, 502, 503, 504):
                raise
            err = e

        if attempt == MAX_RETRIES:
            raise err
        wait = 5 * attempt
        print(f"    attempt {attempt}/{MAX_RETRIES} failed "
              f"({type(err).__name__}), retrying in {wait}s...")
        time.sleep(wait)


def get_available_images(log):
    if not IMAGES_FOLDER.exists():
        return []
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    available = []
    for path in sorted(IMAGES_FOLDER.iterdir()):
        if path.is_file() and path.suffix.lower() in valid_exts:
            if not is_used(path, log):
                available.append(path)
    return available


def main():
    parser = argparse.ArgumentParser(description="Spotify playlist message splitter")
    parser.add_argument("--test", action="store_true",
                        help="Use existing TEST_PLAYLIST_IDS instead of creating new ones")
    parser.add_argument("--file", help="Read the message from this text file")
    parser.add_argument("--title",
                        help=f"Use as the whole title (max {TITLE_MAX} chars) "
                             "instead of '<date> Part N'")
    parser.add_argument("--start", type=int, default=1,
                        help="Number of the first part (used when resuming)")
    args = parser.parse_args()

    sp = get_client()
    log = load_log()

    message = read_message(args.file)
    if not message:
        print("Empty message, nothing to do.")
        return

    specs = build_playlist_specs(message, full_title=args.title, start=args.start)
    images = get_available_images(log)

    print(f"\nMessage length: {len(message)} chars")
    print(f"Chunks created: {len(specs)}")
    for i, spec in enumerate(specs, start=1):
        print(f"  [{i}] title='{spec['title']}'  desc_len={len(spec['description'])}")
    print(f"Unused images available: {len(images)}\n")

    if len(images) < len(specs):
        print(f"Need {len(specs)} unused images, only {len(images)} available.")
        return
    if args.test and len(specs) > len(TEST_PLAYLIST_IDS):
        print(f"Test mode: need {len(specs)} playlist IDs, "
              f"only {len(TEST_PLAYLIST_IDS)} configured in config.py.")
        return

    for idx, (spec, image) in enumerate(zip(specs, images)):
        part = args.start + idx
        print(f"[{idx + 1}/{len(specs)}] '{spec['title']}'")
        pid = None

        try:
            # 1. Playlist: reuse (test) or create (real run)
            if args.test:
                pid = TEST_PLAYLIST_IDS[idx]
                with_retries(sp.playlist_change_details, pid,
                             name=spec["title"], description=spec["description"])
            else:
                playlist = sp.current_user_playlist_create(
                    name=spec["title"], public=True,
                    description=spec["description"],
                )
                pid = playlist["id"]

            # 2. Cover (safe to retry: it just replaces the cover)
            with_retries(sp.playlist_upload_cover_image, pid, encode_image(image))

        except Exception as e:
            print(f"\n  FAILED on part {part}: {type(e).__name__}: {e}")
            if pid:
                print(f"  Playlist {pid} exists with its text but no cover. "
                      "Add one in the Spotify app.")
                first_unsent = idx + 1
            else:
                print("  That playlist was not created (check Spotify for a stray one).")
                first_unsent = idx

            if first_unsent < len(specs):
                remaining = "".join(s["description"] for s in specs[first_unsent:])
                UNSENT_FILE.write_text(remaining, encoding="utf-8")
                print(f"  Remaining text saved to {UNSENT_FILE}. Resume with:")
                print(f"    python main.py --file {UNSENT_FILE} --start {args.start + first_unsent}")
            sys.exit(1)

        # 3. Log and clean up only after the cover really went through
        append_entry({
            "file": image.name,
            "phash": compute_phash(image),
            "playlist_id": pid,
            "title": spec["title"],
        })
        delete_image(image)
        print(f"    done  ← {image.name}  (logged, deleted)")

        if idx < len(specs) - 1:
            time.sleep(DELAY_BETWEEN_PLAYLISTS)

    print("\nDone. Check used_images.json to verify the log.")


if __name__ == "__main__":
    main()
