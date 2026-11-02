# Playlist Message Converter

Turns a long text message into a series of Spotify playlists. Each playlist carries one chunk of the message in its description and a unique cover image, so the whole message reads as a sequence of playlists on a Spotify profile.

Built in Python with the Spotify Web API. It started as a personal project for sending a message to a friend, and it turned into a good way to test API limits, retries and failure recovery.

## Demo

![Terminal run next to the Spotify library](docs/demo-split.gif)

A 1,395 character message goes in and 3 playlists come out. On the left, the new covers appear in the Spotify library as each `[n/3] done` line prints in the terminal.

<details>
<summary>Full run, including the command</summary>

![Full terminal run](docs/demo-terminal.gif)

</details>

## Result

The demo message was split into 3 chunks (512 + 512 + 368 characters). Each chunk became the description of one playlist, with its own cover image.

**Part 1**

![Playlist part 1](docs/playlist-part-1.png)

**Part 2**

![Playlist part 2](docs/playlist-part-2.png)

**Part 3**

![Playlist part 3](docs/playlist-part-3.png)

Chunks are cut at a fixed length, so a word can be split across two playlists (parts 2 and 3 above start mid-word).

Terminal output of the same run:

```text
Message length: 1395 chars
Chunks created: 3
  [1] title='Test'  desc_len=512
  [2] title='Test'  desc_len=512
  [3] title='Test'  desc_len=368
Unused images available: 53

[1/3] 'Test'
    done ← 2026-10-27_18-30-10-11.jpg  (logged, deleted)
[2/3] 'Test'
    done ← 2026-10-27_18-30-10-12.jpg  (logged, deleted)
[3/3] 'Test'
    done ← 2026-10-27_18-30-10-13.jpg  (logged, deleted)

Done. Check used_images.json to verify the log.
```

## What it does

1. Reads a message from a `.txt`, `.docx` or `.odt` file (or pasted into the terminal).
2. Splits it into chunks of at most 512 characters.
3. Creates one playlist per chunk: the chunk goes in the description, and the title is `<date> Part N` by default (or the one you pass with `--title`).
4. Uploads a cover image to each playlist, taken from an images folder. Every image is used only once.

Example: the 1,395 character demo message above became 3 playlists, so it needed 3 unused images.

## Features

- **Input formats:** plain text, `.docx`, `.odt`, or stdin.
- **Image registry:** a perceptual hash (`imagehash`) of every used image is stored in `used_images.json`, so an image can't be reused even if it was resized or re-saved.
- **Automatic cover sizing:** covers are converted to JPEG and shrunk until they fit under the size limit.
- **Retries with backoff:** timeouts, connection errors and HTTP 429/5xx responses are retried automatically.
- **Resume after failure:** if a run fails midway, the unsent text is saved to `unsent.txt` and the script prints the exact command to continue.
- **Test mode:** `--test` reuses existing playlists instead of creating new ones.

## What this project shows

- Spotify's OAuth 2.0 Authorization Code flow, through `spotipy`.
- Working around API limits: timeouts, retries and a resumable run.
- Reading `.docx` and `.odt` files with only the standard library (`zipfile` and XML parsing).
- Image handling with Pillow, plus perceptual hashing to detect reused images.
- A command line interface built with `argparse`.

## Setup

### 1. Create a Spotify app

Create an app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard). Copy its Client ID and Client Secret, and add a redirect URI of your choice (for example `http://127.0.0.1:8888/callback`). It must match your `.env` exactly.

### 2. Install

```bash
git clone https://github.com/Sam-did-this/Message--Playlist--Converter.git
cd Message--Playlist--Converter
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

| Variable | Meaning |
|---|---|
| `SPOTIPY_CLIENT_ID` | Client ID from your Spotify app |
| `SPOTIPY_CLIENT_SECRET` | Client Secret from your Spotify app |
| `SPOTIPY_REDIRECT_URI` | Redirect URI registered in your Spotify app |
| `IMAGES_FOLDER` | Folder with your cover images (default `./images`) |
| `SPOTIFY_USER_ID` | Your Spotify user ID |

Put your cover images (`.jpg`, `.jpeg`, `.png`, `.webp`) in the images folder. You need at least one unused image per chunk.

## Usage

```bash
python main.py --file message.txt                    # recommended for long messages
python main.py                                       # paste a message, then Ctrl+D
python main.py --file message.txt --title "My title" # one custom title for every part
python main.py --test                                # reuse the playlists in TEST_PLAYLIST_IDS
python main.py --file unsent.txt --start 4           # resume after a failure
```

The first run opens a browser window for Spotify's OAuth login.

## Things to know before you run it

- **Playlists are created public.** Anyone can read the message in the descriptions. Delete the playlists in Spotify if you don't want that.
- **Used images are deleted** from the images folder after a successful upload. Work from copies.
- **Test mode:** replace `TEST_PLAYLIST_IDS` in `config.py` with playlist IDs from your own account.
- **Line breaks are collapsed.** Newlines and repeated spaces become single spaces before the message is split.
- Chunks are cut at a fixed length, so a word can be split across two playlists.
- Old `.doc` files aren't supported. Save them as `.docx` or `.odt`.

## Tech stack

Python 3, Spotify Web API (OAuth 2.0 Authorization Code Flow), `spotipy`, `Pillow`, `ImageHash`, `python-dotenv`, `requests`.

## Project layout

| File | Purpose |
|---|---|
| `main.py` | Command line entry point: reads the message, creates playlists, uploads covers, handles retries and resume |
| `message_processor.py` | Splits the message into chunks and builds each playlist's title and description |
| `image_registry.py` | Perceptual hashing and the used-images log |
| `config.py` | Environment variables and shared constants |
| `docs/` | Demo GIFs and screenshots used in this README |

## Roadmap

- Split chunks on word boundaries.
- Add a `--private` option.
- Add tests for the splitting logic.

## Status

Working. Feedback and issues are welcome.
