"""
main.py — Create Spotify playlists from a long message, one playlist per chunk.

Usage:
    python main.py            # full run: creates new playlists
    python main.py --test     # test mode: reuses TEST_PLAYLIST_IDS instead
"""

import argparse
import base64

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import (
    IMAGES_FOLDER, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES,
    TEST_PLAYLIST_IDS,
)
from image_registry import (
    load_log, is_used, append_entry, delete_image, compute_phash,
)
from message_processor import build_playlist_specs


def get_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    ))


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


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
    args = parser.parse_args()

    sp = get_client()
    log = load_log()

    message = input("Message: ").strip()
    if not message:
        print("Empty message, nothing to do.")
        return

    specs = build_playlist_specs(message)
    images = get_available_images(log)

    print(f"\nMessage length: {len(message)} chars")
    print(f"Chunks created: {len(specs)}")
    for i, spec in enumerate(specs, start=1):
        print(f"  [{i}] title='{spec['title']}'  desc_len={len(spec['description'])}")
    print(f"Unused images available: {len(images)}")
    print()

    if len(images) < len(specs):
        print(f"Need {len(specs)} unused images, only {len(images)} available.")
        return

    if args.test:
        if len(specs) > len(TEST_PLAYLIST_IDS):
            print(f"Test mode: need {len(specs)} playlist IDs, "
                  f"only {len(TEST_PLAYLIST_IDS)} configured in config.py.")
            return
        targets = [{"id": pid, "title": f"TEST-{i+1}"}
                   for i, pid in enumerate(TEST_PLAYLIST_IDS[:len(specs)])]
        print(f"TEST MODE: using {len(targets)} existing playlists\n")
    else:
        targets = []
        for spec in specs:
            playlist = sp.current_user_playlist_create(
                name=spec["title"],
                public=True,
                description=spec["description"],
            )
            targets.append({"id": playlist["id"], "title": spec["title"]})

    # Upload covers and log every image used
    for spec, target, image in zip(specs, targets, images):
        # In test mode, also update the description of the existing playlist
        if args.test:
            sp.playlist_change_details(
                target["id"],
                name=target["title"],
                description=spec["description"],
            )

        sp.playlist_upload_cover_image(target["id"], encode_image(image))

        append_entry({
            "file": image.name,
            "phash": compute_phash(image),
            "playlist_id": target["id"],
            "title": target["title"],
        })

        delete_image(image)
        print(f"'{target['title']}' ← {image.name}  (logged, deleted)")

    print("\nDone. Check used_images.json to verify the log.")


if __name__ == "__main__":
    main()
