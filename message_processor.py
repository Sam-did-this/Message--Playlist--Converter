"""
message_processor.py — Turns one long message into a sequence of
(title, description) pairs, one per playlist.

Rules:
  - The message is split into chunks of at most DESC_MAX characters.
  - Each chunk becomes the description of one playlist.
  - The title is generated as 'Part N' by default, or uses a custom
    prefix if you supply one.

The function returns a list of dicts, each with 'title' and 'description'.
main.py iterates over that list and creates one playlist per item.
"""

from config import TITLE_MAX, DESC_MAX


def split_message(message, size=DESC_MAX):
    """Split a message into chunks of at most `size` characters."""
    if not message:
        return []
    return [message[i:i + size] for i in range(0, len(message), size)]


def build_playlist_specs(message, title_prefix="Part"):
    """
    Return a list of dicts: [{'title': ..., 'description': ...}, ...]

    Each description is at most DESC_MAX characters.
    Each title is at most TITLE_MAX characters (numbered sequentially).
    """
    chunks = split_message(message, DESC_MAX)
    specs = []
    total = len(chunks)

    for i, chunk in enumerate(chunks, start=1):
        if total == 1:
            title = title_prefix
        else:
            title = f"{title_prefix} {i}"

        # Enforce TITLE_MAX even if the prefix is unusually long
        title = title[:TITLE_MAX]
        specs.append({"title": title, "description": chunk})

    return specs
