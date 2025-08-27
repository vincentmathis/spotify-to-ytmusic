import os
from spotify_to_ytmusic_cli.matching_utils import ranked_matches
from platformdirs import user_config_dir
from dataclasses import dataclass
from typing import Literal
from spotify_client import SpotifyClient
from ytmusic_client import YtMusicClient


# init clients once
config_dir = user_config_dir("spotify-to-ytmusic-cli", appauthor="vincent-mathis")
os.makedirs(config_dir, exist_ok=True)
SPOTIFY = SpotifyClient(config_dir)
YTMUSIC = YtMusicClient(config_dir)


@dataclass
class TransferEvent:
    event: Literal["progress", "match", "choice_required", "done"]
    data: dict


def like_track(sp_track, yt_track, yt_liked_cache, score):
    if yt_track["videoId"] in yt_liked_cache:
        yield TransferEvent("match", {"action": "SKIP (already liked)", "spotify": sp_track, "yt": yt_track, "score": 100})
        return
    YTMUSIC.like_track(yt_track["videoId"])
    yield TransferEvent("match", {"action": "LIKED", "spotify": sp_track, "yt": yt_track, "score": score})


def transfer_likes(auto_mode="ask"):
    sp_tracks = SPOTIFY.get_liked_tracks()
    yt_liked_cache = YTMUSIC.get_liked_cache()
    total = len(sp_tracks)

    for done, sp_track in enumerate(sp_tracks, start=1):
        results = YTMUSIC.search_tracks(f"{sp_track['title']} {sp_track['artist']}")
        matches = ranked_matches(sp_track, results)

        if not matches:
            yield TransferEvent("match", {"action": "SKIP (no match found)", "spotify": sp_track, "yt": None, "score": 0})
            yield TransferEvent("progress", {"done": done, "total": total})
            continue

        yt_best_track, score = matches[0]
        if score >= 85 or auto_mode == "auto_accept":
            yield from like_track(sp_track, yt_best_track, yt_liked_cache, score)
        elif auto_mode == "skip":
            yield TransferEvent("match", {"action": "SKIP (low score)", "spotify": sp_track, "yt": yt_best_track, "score": score})
        else:
            chosen = yield TransferEvent("choice_required", {"spotify": sp_track, "matches": matches})
            if chosen:  # UI sent a track back
                yield from like_track(sp_track, chosen, yt_liked_cache, score)
            else:
                yield TransferEvent("match", {"action": "SKIP (manual)", "spotify": sp_track, "yt": None, "score": 0})

        yield TransferEvent("progress", {"done": done, "total": total})

    yield TransferEvent("done", {"mode": "LIKES"})


def add_track(sp_track, yt_playlist_id, yt_track, yt_playlist_cache, score):
    if yt_track["videoId"] in yt_playlist_cache:
        yield TransferEvent("match", {"action": "SKIP (already in playlist)", "spotify": sp_track, "yt": yt_track, "score": 100})
        return
    success = YTMUSIC.add_track_to_playlist(yt_playlist_id, yt_track["videoId"], yt_playlist_cache)
    if success:
        yield TransferEvent("match", {"action": "ADDED", "spotify": sp_track, "yt": yt_track, "score": score})
    else:
        yield TransferEvent("match", {"action": "SKIP (error adding)", "spotify": sp_track, "yt": yt_track, "score": score})


def transfer_playlist(auto_mode="ask"):
    # TODO: UI picks this
    sp_selected_playlist = {"name": "test", "id": "test"}
    sp_tracks = SPOTIFY.get_playlist_tracks(sp_selected_playlist["id"])
    yt_playlist = YTMUSIC.ensure_playlist_ready(sp_selected_playlist["name"])
    yt_playlist_id = yt_playlist["playlistId"]
    yt_playlist_cache = YTMUSIC.get_playlist_cache(yt_playlist_id)
    total = len(sp_tracks)

    for done, sp_track in enumerate(sp_tracks, start=1):
        results = YTMUSIC.search_tracks(f"{sp_track['title']} {sp_track['artist']}")
        matches = ranked_matches(sp_track, results)

        if not matches:
            yield TransferEvent("match", {"action": "SKIP (no match found)", "spotify": sp_track, "yt": None, "score": 0})
            yield TransferEvent("progress", {"done": done, "total": total})
            continue

        yt_best_track, score = matches[0]
        if score >= 85 or auto_mode == "auto_accept":
            yield from add_track(sp_track, yt_playlist_id, yt_best_track, yt_playlist_cache, score)
        elif auto_mode == "skip":
            yield TransferEvent("match", {"action": "SKIP (low score)", "spotify": sp_track, "yt": yt_best_track, "score": score})
        else:
            chosen = yield TransferEvent("choice_required", {"spotify": sp_track, "matches": matches})
            if chosen:
                yield from add_track(sp_track, yt_playlist_id, chosen, yt_playlist_cache, score)
            else:
                yield TransferEvent("match", {"action": "SKIP (manual)", "spotify": sp_track, "yt": None, "score": 0})

        yield TransferEvent("progress", {"done": done, "total": total})

    yield TransferEvent("done", {"mode": "PLAYLIST"})
