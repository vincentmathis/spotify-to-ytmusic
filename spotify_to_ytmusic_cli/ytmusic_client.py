import os
import sys
import json
import time
from ytmusicapi import setup_oauth, YTMusic
from ytmusicapi.exceptions import YTMusicServerError
from rich.console import Console

console = Console()


class YtMusicClient:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        creds_path = os.path.join(config_dir, "ytmusic-oauth-creds.json")
        token_path = os.path.join(config_dir, "ytmusic-oauth-token.json")

        if not os.path.exists(creds_path):
            console.print(
                f"[red]Missing Google OAuth credentials at {creds_path}[/red]"
            )
            sys.exit(1)

        # Run OAuth flow if no token yet
        if not os.path.exists(token_path):
            creds = json.load(open(creds_path))
            setup_oauth(
                creds["installed"]["client_id"],
                creds["installed"]["client_secret"],
                token_path,
                open_browser=True,
            )

        print(token_path)
        self.client = YTMusic(auth=token_path, oauth_credentials=creds_path)

    # ---------------- Likes ----------------
    def get_liked_cache(self, limit=5000):
        with console.status("[bold green]Fetching YT Music likes...", spinner="dots"):
            liked = self.client.get_liked_songs(limit=limit)["tracks"]
        console.print(f"[green]Found {len(liked)} liked songs on YT Music[/green]")
        return {
            (
                item["title"].lower(),
                tuple(a["name"].lower() for a in item.get("artists", [])),
            )
            for item in liked
        }

    # ---------------- Playlists ----------------
    def get_playlist_by_name(self, name):
        playlists = self.client.get_library_playlists(limit=None)
        print(len(playlists))
        for p in playlists:
            print(p["title"].lower(), name.lower(), p["title"].lower() == name.lower())
            if p["title"].lower() == name.lower():
                return p
        return None

    def ensure_playlist_ready(self, name, description=""):
        p = self.get_playlist_by_name(name)
        if p:
            return {"playlistId": p["playlistId"], "title": p["title"]}
        else:
            console.print(
                f"[blue]Playlist '{name}' not found on YTMusic. Creating...[/blue]"
            )
            res = self.client.create_playlist(name, description)
            playlist_id = res if isinstance(res, str) else res["playlistId"]

        # Wait until playlist is visible
        for delay in (0.5, 1, 2, 3, 5):
            try:
                res = self.client.get_playlist(playlist_id, limit=1)
                return {"playlistId": res["id"], "title": res["title"]}
            except Exception:
                time.sleep(delay)
        raise RuntimeError("Couldn't confirm YT Music playlist creation")

    def get_playlist_track_ids(self, playlist_id):
        tracks = self.client.get_playlist(playlist_id, limit=1000)["tracks"]
        return {t["videoId"] for t in tracks if "videoId" in t}

    def add_with_retry(self, playlist_id, video_id, existing_ids):
        backoff = [0, 0.5, 1, 2]
        for delay in backoff:
            try:
                self.client.add_playlist_items(playlist_id, [video_id])
                existing_ids.add(video_id)
                return True
            except YTMusicServerError as e:
                if "409" in str(e):
                    refreshed = self.get_playlist_track_ids(playlist_id)
                    existing_ids.clear()
                    existing_ids.update(refreshed)
                    if video_id in existing_ids:
                        return False  # already there
            time.sleep(delay)
        return False

    # ---------------- Tracks ----------------
    def search_tracks(self, query: str, limit=20):
        return self.client.search(query, filter="songs", limit=limit)

    def like_song(self, video_id: str):
        return self.client.rate_song(video_id, "LIKE")

    def add_to_playlist(self, playlist_id: str, video_id: str):
        return self.client.add_playlist_items(playlist_id, [video_id])
