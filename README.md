# CLI tool to port liked songs and playlists from spotify to ytmusic. (WIP)

## Use Poetry to install dependencies in virtual environment

In the folder with `pyproject.toml` run `poetry install`.

## Spotify Client
Create a [Spotify dev app](https://developer.spotify.com/dashboard) and copy the values in an .env file:

```
SPOTIPY_CLIENT_ID=
SPOTIPY_CLIENT_SECRET=
SPOTIPY_REDIRECT_URI=https://127.0.0.1
```

## YT Music Client

Use `ytmusicapi browser` in your virtual env to create the necessary file. [Explanation](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html)
