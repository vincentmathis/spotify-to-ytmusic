from ytmusicapi import YTMusic
from ytmusicapi.exceptions import YTMusicServerError
from time import sleep
from rich.console import Console

CONSOLE = Console()
YTMUSIC = YTMusic("browser.json")


def get_liked_cache():
    with CONSOLE.status(
        "[bold green]Fetching YT Music likes...[/bold green]", spinner="dots"
    ):
        liked = YTMUSIC.get_liked_songs(limit=5000)["tracks"]
        CONSOLE.print(f"[green]Found {len(liked)} liked songs on YT Music.[/green]")
        cache = set()
        for item in liked:
            title = item["title"].lower()
            artists = tuple(a["name"].lower() for a in item.get("artists", []))
            cache.add((title, artists))
    return cache


def get_playlist_by_name(name):
    """Return YT playlist dict if exists, else None"""
    playlists = YTMUSIC.get_library_playlists(limit=500)
    for p in playlists:
        if p["title"].lower() == name.lower():
            return p
    return None


def ensure_playlist_ready(name, description=""):
    """
    Return {'playlistId': ..., 'title': ...} for an existing or newly created playlist.
    Works around YTMUSIC.create_playlist() returning either a string or a dict,
    and waits until get_playlist succeeds (eventual consistency).
    """
    p = get_playlist_by_name(name)
    if p:
        return {"playlistId": p["playlistId"], "title": p["title"]}

    res = YTMUSIC.create_playlist(name, description)
    playlistId = res if isinstance(res, str) else res["playlistId"]

    # Poll for readiness
    for delay in (0.5, 1, 2, 3, 5):
        try:
            res = YTMUSIC.get_playlist(playlistId, limit=1)
            return {"playlistId": res["id"], "title": res["title"]}
        except Exception:
            sleep(delay)
    raise Exception("Couldn't get YT Music Playlist")
    return None


def add_with_retry(playlist_id, vid, existing_ids):
    """
    Add a single video to a playlist with retries.
    - Updates existing_ids on success.
    - If a 409 occurs, refreshes existing_ids and skips if already present.
    """
    backoff = [0, 0.5, 1, 2]
    for i, delay in enumerate(backoff, start=1):
        try:
            YTMUSIC.add_playlist_items(playlist_id, [vid])
            existing_ids.add(vid)
            return True
        except YTMusicServerError as e:
            msg = str(e)
            if "409" in msg:
                # Likely duplicate or race; refresh and skip if present
                refreshed = get_playlist_track_ids(playlist_id)
                existing_ids.clear()
                existing_ids.update(refreshed)
                if vid in existing_ids:
                    return False  # already there; treat as success/skip
            if i == len(backoff):
                raise
            sleep(delay)
    return False


def get_playlist_track_ids(playlist_id):
    """Return set of videoIds already in a YT playlist"""
    tracks = YTMUSIC.get_playlist(playlist_id, limit=1000)["tracks"]
    return {t["videoId"] for t in tracks if "videoId" in t}
