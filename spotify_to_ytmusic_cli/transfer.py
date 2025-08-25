import os
from platformdirs import user_config_dir
from rich.live import Live
import ui
from spotify_client import SpotifyClient
from ytmusic_client import YtMusicClient
from utils import normalize, ranked_matches


# init clients once
config_dir = user_config_dir("spotify-to-ytmusic-cli", appauthor="vincent-mathis")
os.makedirs(config_dir, exist_ok=True)
SPOTIFY = SpotifyClient(config_dir)
YTMUSIC = YtMusicClient(config_dir)


def is_already_liked(track, cache):
    key = (normalize(track["title"]), tuple(normalize(track["artist"]).split()[:10]))
    return any(
        key[0] == liked_title and any(a in liked_artists for a in key[1])
        for liked_title, liked_artists in cache
    )


def match_track(track, live, existing_ids=None):
    results = YTMUSIC.search_tracks(f"{track['title']} {track['artist']}")
    matches = ranked_matches(track, results)
    if not matches:
        return None, 0

    best, score = matches[0]

    # Check for duplicates in playlist
    if existing_ids and best["videoId"] in existing_ids:
        return "DUPLICATE", score

    # Ask user if confidence is low
    if score < 90:
        live.stop()
        # FIXME if chosen song already in playlist, skip
        chosen = ui.ask_user_choice(track, matches)
        live.start()
        if chosen:
            return chosen, score
        return None, 0

    return best, score


def apply_action(track, best_match, score, mode, playlist_id=None, existing_ids=None):
    track_str = f"{track['title']} — {track['artist']}"
    if best_match == "DUPLICATE":
        return "SKIPPED (already added)", track_str, "-", 0

    if not best_match:
        return "SKIPPED (manual)", track_str, "-", 0

    song_str = f"{best_match['title']} — {', '.join(a['name'] for a in best_match.get('artists', []))}"
    vid = best_match["videoId"]

    if mode == "LIKES":
        YTMUSIC.like_song(vid)
        return "LIKED", track_str, song_str, score
    else:
        success = YTMUSIC.add_with_retry(playlist_id, vid, existing_ids)
        return (
            ("ADDED", track_str, song_str, score)
            if success
            else ("SKIPPED (error)", track_str, song_str, score)
        )


def transfer_items(tracks, mode="LIKES", ytm_cache=None, playlist_name=None):
    layout, table, progress, task = ui.create_layout(len(tracks))
    playlist_id = None
    existing_ids = set()

    if mode == "PLAYLIST":
        yt_playlist = YTMUSIC.ensure_playlist_ready(playlist_name)
        playlist_id = yt_playlist["playlistId"]
        existing_ids = set(YTMUSIC.get_playlist_track_ids(playlist_id))

    with Live(
        layout, console=ui.console, refresh_per_second=4, transient=False
    ) as live:
        for track in tracks:
            if mode == "LIKES" and is_already_liked(track, ytm_cache):
                ui.print_row(
                    table,
                    "SKIPPED (already liked)",
                    f"{track['title']} — {track['artist']}",
                    "-",
                    0,
                )
                continue

            best_match, score = match_track(track, live, existing_ids)
            action, track_str, song_str, score = apply_action(
                track, best_match, score, mode, playlist_id, existing_ids
            )
            ui.print_row(table, action, track_str, song_str, score)

            progress.update(task, advance=1)

    ui.show_completion_message(mode, playlist_name)


# -------------------
# Public API
# -------------------
def transfer_liked_songs():
    tracks = SPOTIFY.get_liked_tracks()
    ytm_cache = YTMUSIC.get_liked_cache()
    transfer_items(tracks, mode="LIKES", ytm_cache=ytm_cache)


def transfer_playlist():
    playlists = SPOTIFY.get_playlists()
    playlist_choice = ui.ask_user_playlist(playlists)
    if not playlist_choice:
        raise KeyboardInterrupt
    selected = next(p for p in playlists if p["name"] == playlist_choice)
    tracks = SPOTIFY.get_playlist_tracks(selected["id"])
    transfer_items(tracks, mode="PLAYLIST", playlist_name=selected["name"])
