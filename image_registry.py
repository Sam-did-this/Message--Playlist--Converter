"""
image_registry.py — Converts images into hashes and maintains the used-images log.

Key behaviors:
  - compute_phash(image_path): produces a perceptual hash string (hex).
    Perceptual hashing survives resizing, recompression, and light cropping.
  - load_log() / save_log(): read and write used_images.json.
  - append_entry(entry): adds one record and flushes to disk immediately.
  - is_used(image_path, log): returns True if this image (or a variant) is logged.
  - delete_image(image_path): unlinks the file — no archive folder, no copy.

The log lives at the project root as used_images.json. It is a plain JSON
array of objects, one per image that has ever been uploaded. Each entry
contains the phash (the key used for matching), the filename, the
playlist ID it went with, and the timestamp.

Because the log is JSON, anyone with read access can inspect it. Nothing
secret is stored there — only the hash, filename, and playlist ID, all
of which are already public on Spotify's side once the playlist exists.
"""

import json
from datetime import datetime
from pathlib import Path

from PIL import Image
import imagehash

from config import USED_LOG


def compute_phash(image_path):
    """
    Return a perceptual hash string for the image, or None on failure.

    The hash is a 64-bit value rendered as 16 hex characters, e.g.
    'd4f8a2b1c0e5f9a3'. Two visually similar images produce the same
    or nearly the same string, so resizing or re-saving won't bypass
    the registry.
    """
    try:
        with Image.open(image_path) as img:
            return str(imagehash.phash(img))
    except (OSError, ValueError):
        return None


def load_log():
    """Return the log as a list of dicts. Empty list if the file doesn't exist."""
    if not USED_LOG.exists():
        return []
    try:
        return json.loads(USED_LOG.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_log(entries):
    """Write the log back to disk with stable formatting."""
    USED_LOG.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def append_entry(entry):
    """
    Add one record to the log and flush immediately.

    The entry must contain at least:
      - 'phash'       (str)   the perceptual hash
      - 'file'        (str)   original filename
      - 'playlist_id' (str)   Spotify playlist ID it was uploaded to
    'used_at' is added automatically as an ISO-8601 timestamp.
    """
    entry = dict(entry)
    entry.setdefault("used_at", datetime.now().isoformat(timespec="seconds"))
    entries = load_log()
    entries.append(entry)
    save_log(entries)


def is_used(image_path, log=None):
    """True if the image's phash already appears in the log."""
    if log is None:
        log = load_log()
    phash = compute_phash(image_path)
    if phash is None:
        return True  # unreadable = treat as used
    return any(e.get("phash") == phash for e in log)


def delete_image(image_path):
    """Remove the file from disk. No archive copy is kept."""
    try:
        Path(image_path).unlink()
        return True
    except OSError:
        return False
