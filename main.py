import os
import base64
from pathlib import Path
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="ugc-image-upload playlist-modify-public playlist-modify-private"
))

spotify_user_id = os.getenv("SPOTIFY_USER_ID")

# Step 1: Create the playlist
playlist = sp.user_playlist_create(
    user=spotify_user_id,
    name="Title",
    public=True,
    description="This is a test. I'm not going to risk any crashes for song. Fuck my life."
)
playlist_id = playlist['id']
print(f"Created playlist: {playlist_id}")

# Step 2: Upload the cover image
images_folder = Path(os.getenv("IMAGES_FOLDER"))
image_path = images_folder / "keanu_reeves.jpeg"

with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

sp.playlist_upload_cover_image(playlist_id, image_data)
print("Cover image uploaded.")
