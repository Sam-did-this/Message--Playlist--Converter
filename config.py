"""
config.py — Single source for environment variables and shared constants.

Everything that reads from .env goes through here, so if a variable name
changes, you only fix it in one spot.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root, regardless of where the script is run from
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


# --- Spotify API ---
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
USER_ID = os.getenv("SPOTIFY_USER_ID")

# The OAuth scopes needed: upload cover images, modify public/private playlists
SCOPES = "ugc-image-upload playlist-modify-public playlist-modify-private"

#--- Test mode: You just have 2 playlists in this space, be aware ---
TEST_PLAYLIST_IDS = [
    "77iz4gOZfss5yfeNJzDejp",
    "1A0jSvBY77XgT1yFZroIsk",
]

# --- Folders ---
IMAGES_FOLDER = BASE_DIR / os.getenv("IMAGES_FOLDER", "./images").lstrip("./")
USED_LOG = BASE_DIR / "used_images.json"


# --- Length limits (from Important-values-note.txt) ---
TITLE_MAX = 200
DESC_MAX = 512
