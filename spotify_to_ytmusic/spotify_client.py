import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_spotify_client():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="user-library-read playlist-read-private playlist-modify-private playlist-modify-public"
        )
    )


def get_liked_tracks(sp, limit=5000):
    results, offset = [], 0
    while True:
        batch = sp.current_user_saved_tracks(limit=50, offset=offset)
        items = batch["items"]
        if not items:
            break
        for item in items:
            track = item["track"]
            results.append(
                {"title": track["name"], "artist": track["artists"][0]["name"]}
            )
        offset += 50
        if len(results) >= limit:
            break
    return results


def get_playlists(sp):
    playlists, offset = [], 0
    while True:
        batch = sp.current_user_playlists(limit=50, offset=offset)
        if not batch["items"]:
            break
        playlists.extend(batch["items"])
        offset += 50
    return playlists


def get_playlist_tracks(sp, playlist_id, limit=5000):
    tracks = []
    offset = 0
    while True:
        batch = sp.playlist_items(playlist_id, limit=100, offset=offset)
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
