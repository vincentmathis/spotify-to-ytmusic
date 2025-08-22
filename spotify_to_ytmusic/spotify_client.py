import spotipy
from spotipy.oauth2 import SpotifyOAuth
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

CONSOLE = Console()
SPOTIFY = spotipy.Spotify(
    auth_manager=SpotifyOAuth(scope="user-library-read playlist-read-private")
)


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
