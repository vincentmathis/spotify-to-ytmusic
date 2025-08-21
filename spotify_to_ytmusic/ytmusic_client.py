from ytmusicapi import YTMusic
# from ytmusicapi.exceptions import YTMusicServerError
from time import sleep


def get_ytmusic_client():
    return YTMusic("browser.json")


def get_liked_cache(ytmusic, limit=1000):
    liked = ytmusic.get_liked_songs(limit=limit)["tracks"]
    cache = set()
    for item in liked:
        title = item["title"].lower()
        artists = tuple(a["name"].lower() for a in item.get("artists", []))
        cache.add((title, artists))
    return cache


def get_playlist_by_name(ytmusic, name):
    """Return YT playlist dict if exists, else None"""
    playlists = ytmusic.get_library_playlists(limit=500)
    for p in playlists:
        if p["title"].lower() == name.lower():
            return p
    return None


def ensure_playlist_ready(ytmusic, name, description=""):
    """
    Return {'playlistId': ..., 'title': ...} for an existing or newly created playlist.
    Works around ytmusic.create_playlist() returning either a string or a dict,
    and waits until get_playlist succeeds (eventual consistency).
    """
    p = get_playlist_by_name(ytmusic, name)
    if p:
        return {"playlistId": p["playlistId"], "title": p["title"]}

    res = ytmusic.create_playlist(name, description)
    print(res, type(res))
    # Normalize return to dict
    if isinstance(res, str):
        playlist = {"playlistId": res, "title": name}
    else:
        playlist = {"playlistId": res["playlistId"], "title": res.get("title", name)}

    # Poll for readiness
    for delay in (0.5, 1, 2, 3, 5):
        try:
            ytmusic.get_playlist(playlist["playlistId"], limit=1)
            break
        except Exception:
            sleep(delay)
    return playlist


# def add_with_retry(ytmusic, playlist_id, vid, existing_ids):
#     """
#     Add a single video to a playlist with retries.
#     - Updates existing_ids on success.
#     - If a 409 occurs, refreshes existing_ids and skips if already present.
#     """
#     backoff = [0, 0.5, 1, 2]
#     for i, delay in enumerate(backoff, start=1):
#         try:
#             ytmusic.add_playlist_items(playlist_id, [vid])
#             existing_ids.add(vid)
#             return True
#         except YTMusicServerError as e:
#             msg = str(e)
#             if "409" in msg:
#                 # Likely duplicate or race; refresh and skip if present
#                 refreshed = get_playlist_track_ids(ytmusic, playlist_id)
#                 existing_ids.clear()
#                 existing_ids.update(refreshed)
#                 if vid in existing_ids:
#                     return False  # already there; treat as success/skip
#             if i == len(backoff):
#                 raise
#             sleep(delay)
#     return False


def get_playlist_track_ids(ytmusic, playlist_id):
    """Return set of videoIds already in a YT playlist"""
    tracks = ytmusic.get_playlist(playlist_id, limit=1000)["tracks"]
    return {t["videoId"] for t in tracks if "videoId" in t}
