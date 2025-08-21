from utils import normalize, best_match
from ytmusic_client import (
    get_playlist_by_name,
    ensure_playlist_ready,
    get_playlist_track_ids,
)
import questionary
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


# -------------------
# Helpers
# -------------------
def is_already_liked(song, cache):
    key = (normalize(song["title"]), tuple(normalize(song["artist"]).split()[:10]))
    for liked_title, liked_artists in cache:
        if key[0] == liked_title and any(a in liked_artists for a in key[1]):
            return True
    return False


def make_progress_table():
    t = Table(show_header=True, header_style="bold", expand=True, box=None)
    t.add_column("Action", style="yellow", overflow="fold", ratio=1)
    t.add_column("Spotify", style="green", overflow="fold", ratio=2)
    t.add_column("YouTube Music", style="red", overflow="fold", ratio=2)
    t.add_column("Confidence", style="white", justify="right", width=10, no_wrap=True)
    return t


def print_row(table, action, spotify_song, ytmusic_song, score):
    table.add_row(action, spotify_song, ytmusic_song, f"{score:.0f}%")


# TODO deduplication
# FIXME after live.stop(), questionary, live.start() the live table janks around 
# -------------------
# Transfer functions
# -------------------
def transfer_liked_songs(ytmusic, songs, ytm_cache):
    for song in songs:
        if is_already_liked(song, ytm_cache):
            console.print(f"[yellow][SKIP][/yellow] {song['title']} already liked")
            continue
        query = f"{song['title']} {song['artist']}"
        results = ytmusic.search(query, filter="songs")

    table = make_progress_table()
    with Live(table, console=console, refresh_per_second=4, transient=False) as live:
        for song in songs:
            query = f"{song['title']} {song['artist']}"
            results = ytmusic.search(query, filter="songs")
            best, score = best_match(song, results)
            if not best or "videoId" not in best:
                console.print(
                    f"[red][SKIP][/red] No match for {song['title']} — {song['artist']}"
                )
                continue

            best_artists = ", ".join(a["name"] for a in best["artists"])
            spotify_song = f"{song['title']} — {song['artist']}"
            ytmusic_song = f"{best['title']} — {best_artists}"

            vid = best["videoId"]
            if is_already_liked(song, ytm_cache):
                print_row(
                    table, "SKIPPED (already liked)", spotify_song, ytmusic_song, score
                )
                continue
            if score >= 85:
                ytmusic.rate_song(vid, "LIKE")
                print_row(table, "LIKED", spotify_song, ytmusic_song, score)
            else:
                # interactive fallback
                live.stop()

                console.print(
                    Panel.fit(
                        f"Could not auto-match: {song['title']} — {song['artist']}",
                        style="red",
                    )
                )

                choices = []
                for r in results[:5]:
                    if "videoId" not in r:
                        continue
                    artists = ", ".join(a["name"] for a in r.get("artists", []))
                    link = f"https://music.youtube.com/watch?v={r['videoId']}"
                    choices.append(f"{r['title']} — {artists} ({link})")
                choices.append("Skip")
                choice = questionary.select("Pick best match:", choices).ask()

                live.start()

                if choice != "Skip":
                    chosen = results[choices.index(choice)]
                    ytmusic.rate_song(chosen["videoId"], "LIKE")
                    print_row(table, "LIKED", spotify_song, chosen["title"], score)
                else:
                    print_row(
                        table, "SKIPPED (manually)", spotify_song, "none chosen", 0
                    )

    console.print(
        Panel.fit(
            "Completed transferring liked songs.",
            style="green",
        )
    )


def transfer_playlist(ytmusic, playlist_name, tracks):
    # Check or create YT playlist
    yt_playlist = get_playlist_by_name(ytmusic, playlist_name)
    if not yt_playlist:
        console.print(
            f"[blue]Playlist '{playlist_name}' not found on YTMusic. Creating...[/blue]"
        )
        yt_playlist = ensure_playlist_ready(ytmusic, playlist_name)

    playlist_id = yt_playlist["playlistId"]
    existing_ids = get_playlist_track_ids(ytmusic, playlist_id)
    console.print(
        f"[cyan]Spotify playlist '{playlist_name}' has {len(tracks)} tracks.[/cyan]"
    )
    console.print(
        f"[cyan]YTMusic playlist '{playlist_name}' has {len(existing_ids)} tracks.[/cyan]"
    )

    table = make_progress_table()
    with Live(table, console=console, refresh_per_second=4, transient=False) as live:
        for song in tracks:
            query = f"{song['title']} {song['artist']}"
            results = ytmusic.search(query, filter="songs")
            best, score = best_match(song, results)
            if not best or "videoId" not in best:
                console.print(
                    f"[red][SKIP][/red] No match for {song['title']} — {song['artist']}"
                )
                continue

            best_artists = ", ".join(a["name"] for a in best["artists"])
            spotify_song = f"{song['title']} — {song['artist']}"
            ytmusic_song = f"{best['title']} — {best_artists}"

            vid = best["videoId"]
            if vid in existing_ids:
                print_row(
                    table, "SKIPPED (already exists)", spotify_song, ytmusic_song, score
                )
                continue
            if score >= 85:
                ytmusic.add_playlist_items(playlist_id, [vid])
                print_row(table, "ADDED", spotify_song, ytmusic_song, score)
            else:
                # interactive fallback
                live.stop()

                console.print(
                    Panel.fit(
                        f"Could not auto-match: {song['title']} — {song['artist']}",
                        style="red",
                    )
                )

                choices = []
                for r in results[:5]:
                    if "videoId" not in r:
                        continue
                    artists = ", ".join(a["name"] for a in r.get("artists", []))
                    link = f"https://music.youtube.com/watch?v={r['videoId']}"
                    choices.append(f"{r['title']} — {artists} ({link})")
                choices.append("Skip")
                choice = questionary.select("Pick best match:", choices).ask()

                live.start()

                if choice != "Skip":
                    chosen = results[choices.index(choice)]
                    ytmusic.add_playlist_items(playlist_id, [chosen["videoId"]])
                    print_row(table, "ADDED", spotify_song, chosen["title"], score)
                else:
                    print_row(
                        table, "SKIPPED (manually)", spotify_song, "none chosen", score
                    )
                    console.print("[yellow][SKIPPED][/yellow]")

    console.print(
        Panel.fit(
            f"Completed transferring {playlist_name}",
            style="green",
        )
    )
