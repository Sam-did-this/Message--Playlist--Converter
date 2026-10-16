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

from datetime import date
from config import TITLE_MAX, DESC_MAX


def split_message(message, size=DESC_MAX):
    """Split a message into chunks of at most `size` characters."""
    message = " ".join(message.split())
    if not message:
        return []
    return [message[i:i + size] for i in range(0, len(message), size)]

def build_playlist_specs(message, title_prefix=None, full_title=None, start=1):
    chunks = split_message(message, DESC_MAX)
    specs = []
    total = len(chunks)

    if title_prefix is None:
        title_prefix = f"{date.today().isoformat()} Part"

    for i, chunk in enumerate(chunks, start=start):
        if full_title is not None:
            title = full_title
        elif total == 1 and start == 1:
            title = title_prefix
        else:
            title = f"{title_prefix} {i}"

        title = title[:TITLE_MAX]
        specs.append({"title": title, "description": chunk})

    return specs
