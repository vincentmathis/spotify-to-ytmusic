import os
import sys
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from rich.console import Console

console = Console()


class SpotifyClient:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        creds_path = os.path.join(config_dir, "spotify-oauth-creds.json")
        token_path = os.path.join(config_dir, "spotify-oauth-token.json")

        # Ensure creds file exists
        if not os.path.exists(creds_path):
            with open(creds_path, "w+") as f:
                json.dump(
                    {
                        "spotipy_client_id": "",
                        "spotipy_client_secret": "",
                        "spotipy_redirect_uri": "http://127.0.0.1:8888/callback",
                    },
                    f,
                    indent=2,
                )

        creds = json.load(open(creds_path))
        if not creds["spotipy_client_id"]:
            console.print(
                f"[red]Please enter Spotify client id/secret in {creds_path}[/red]"
            )
            sys.exit(1)

        oauth = SpotifyOAuth(
            client_id=creds["spotipy_client_id"],
            client_secret=creds["spotipy_client_secret"],
            redirect_uri=creds["spotipy_redirect_uri"],
            scope="user-library-read playlist-read-private",
            cache_path=token_path,
        )

        token_info = oauth.get_access_token(as_dict=True)
        self.client = spotipy.Spotify(auth=token_info["access_token"])

    # ---------------- Likes ----------------
    def get_liked_tracks(self, limit=5000):
        results, offset, batch_size = [], 0, 50
        with console.status("[bold green]Fetching Spotify likes...", spinner="dots"):
            while True:
                batch = self.client.current_user_saved_tracks(
                    limit=batch_size, offset=offset
                )
                items = batch["items"]
                if not items:
                    break
                for item in items:
                    track = item["track"]
                    results.append(
                        {"title": track["name"], "artist": track["artists"][0]["name"]}
                    )
                offset += batch_size
                if len(results) >= limit:
                    break
        console.print(f"[green]Found {len(results)} liked songs on Spotify[/green]")
        return results

    # ---------------- Playlists ----------------
    def get_playlists(self):
        playlists, offset = [], 0
        while True:
            batch = self.client.current_user_playlists(limit=50, offset=offset)
            if not batch["items"]:
                break
            playlists.extend(batch["items"])
            offset += 50
        return playlists

    def get_playlist_tracks(self, playlist_id, limit=5000):
        tracks, offset = [], 0
        while True:
            batch = self.client.playlist_items(playlist_id, limit=100, offset=offset)
            items = batch["items"]
            if not items:
                break
            for item in items:
                track = item["track"]
                if track:  # skip removed
                    tracks.append(
                        {"title": track["name"], "artist": track["artists"][0]["name"]}
                    )
            offset += 100
            if len(tracks) >= limit:
                break
        return tracks
