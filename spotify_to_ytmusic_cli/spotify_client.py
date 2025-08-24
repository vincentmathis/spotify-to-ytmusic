import os
import sys
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from rich.console import Console

CONSOLE = Console()


def init_spotify_client(config_dir):
    global SPOTIFY
    spotify_oauth_creds = os.path.join(config_dir, "spotify-oauth-creds.json")
    if not os.path.exists(spotify_oauth_creds):
        with open(spotify_oauth_creds, "w+") as json_file:
            json.dump(
                {
                    "spotipy_client_id": "",
                    "spotipy_client_secret": "",
                    "spotipy_redirect_uri": "https://127.0.0.1/callback",
                },
                json_file,
            )
    creds = json.load(open(spotify_oauth_creds))
    if creds["spotipy_client_id"] == "":
        CONSOLE.print(
            f"[red]Please enter the spotify client id and secret here: {spotify_oauth_creds}"
        )
        print("\nExiting...")
        sys.exit(0)

    spotify_oauth_token = os.path.join(config_dir, "spotify-oauth-token.json")
    spotify_oauth = SpotifyOAuth(
        creds["spotipy_client_id"],
        creds["spotipy_client_secret"],
        creds["spotipy_redirect_uri"],
        scope="user-library-read playlist-read-private",
        cache_path=spotify_oauth_token,
    )

    token_info = spotify_oauth.get_access_token(as_dict=True)
    SPOTIFY = spotipy.Spotify(auth=token_info["access_token"])


def get_liked_tracks():
    results, batch_size, offset = [], 50, 0
    with CONSOLE.status(
        "[bold green]Fetching Spotify likes...[/bold green]", spinner="dots"
    ):
        while True:
            batch = SPOTIFY.current_user_saved_tracks(limit=batch_size, offset=offset)
            items = batch["items"]
            if not items:
                break
            for item in items:
                track = item["track"]
                results.append(
                    {"title": track["name"], "artist": track["artists"][0]["name"]}
                )
            offset += batch_size
    CONSOLE.print(f"[green]Found {len(results)} liked songs on Spotify.[/green]")
    return results


def get_playlists():
    playlists, offset = [], 0
    while True:
        batch = SPOTIFY.current_user_playlists(limit=50, offset=offset)
        if not batch["items"]:
            break
        playlists.extend(batch["items"])
        offset += 50
    return playlists


def get_playlist_tracks(playlist_id, limit=5000):
    tracks = []
    offset = 0
    while True:
        batch = SPOTIFY.playlist_items(playlist_id, limit=100, offset=offset)
        items = batch["items"]
        if not items:
            break
        for item in items:
            track = item["track"]
            if track is None:  # sometimes removed tracks appear
                continue
            tracks.append(
                {
                    "title": track["name"],
                    "artist": track["artists"][0]["name"],
                }
            )
        offset += 100
        if len(tracks) >= limit:
            break
    return tracks
