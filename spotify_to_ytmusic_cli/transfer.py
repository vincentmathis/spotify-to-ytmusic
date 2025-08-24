from utils import normalize, ranked_matches
import spotify_client
import ytmusic_client
import questionary
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

console = Console()


def is_already_liked(track, cache):
    key = (normalize(track["title"]), tuple(normalize(track["artist"]).split()[:10]))
    for liked_title, liked_artists in cache:
        if key[0] == liked_title and any(a in liked_artists for a in key[1]):
            return True
    return False


def create_ui_elements(track_count):
    # Create a progress instance
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    )

    # Add a progress task
    task = progress.add_task("Transfering", total=track_count)

    # Create a table
    table = Table(show_header=True, header_style="bold", expand=True, box=None)
    table.add_column("Action", style="yellow", overflow="fold", ratio=1)
    table.add_column("Spotify Track", style="green", overflow="fold", ratio=2)
    table.add_column("YouTube Song", style="red", overflow="fold", ratio=2)
    table.add_column("Confidence", style="white", justify="right", width=10, no_wrap=True)

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(Panel(table, title="Data"), name="upper"),
        Layout(Panel(progress, title="Progress"), name="lower", size=3),
    )
    return layout, table, progress, task


def print_row(table, action, track_str, song_str, score):
    # FIXME table doesn't scrool
    table.add_row(action, track_str, song_str, f"{score:.0f}%")
    


def ask_user_choice(track, matches):
    """Interactive fuzzy choice when auto-match fails."""
    console.print(
        f"Could not auto-match: {track['title']} — {track['artist']}",
        style="red",
    )
    choices = []
    for r, sc in matches[:5]:
        artists = ", ".join(a["name"] for a in r.get("artists", []))
        link = f"https://music.youtube.com/watch?v={r['videoId']}"
        choices.append(f"{r['title']} — {artists} ({link}, {sc:.0f}%)")
    choices.append("Skip")

    choice = questionary.select("Pick best match:", choices).ask()
    if choice == "Skip":
        return None
    return matches[choices.index(choice)][0]


def transfer_items(
    tracks,
    mode="LIKES",  # or "PLAYLIST"
    ytm_cache=None,
    playlist_name=None,
):
    """Generic transfer loop for liked songs or a playlist."""
    layout, table, progress, task = create_ui_elements(len(tracks))

    playlist_id = None
    existing_ids = set()

    if mode == "PLAYLIST":
        # ensure playlist exists
        # FIXME doesn't find exsiting lists
        yt_playlist = ytmusic_client.get_playlist_by_name(playlist_name)
        if not yt_playlist:
            console.print(
                f"[blue]Playlist '{playlist_name}' not found on YTMusic. Creating...[/blue]"
            )
            yt_playlist = ytmusic_client.ensure_playlist_ready(playlist_name)
        playlist_id = yt_playlist["playlistId"]
        existing_ids = set(ytmusic_client.get_playlist_track_ids(playlist_id))
    with Live(layout, console=console, refresh_per_second=4, transient=False) as live:
        for track in tracks:
            progress.update(task, advance=1)
            track_str = f"{track['title']} — {track['artist']}"

            if mode == "LIKES" and is_already_liked(track, ytm_cache):
                print_row(table, "SKIPPED (already liked)", track_str, "-", 0)
                continue

            results = ytmusic_client.YTMUSIC.search(
                f"{track['title']} {track['artist']}", filter="songs"
            )
            matches = ranked_matches(track, results)
            if not matches:
                console.print(f"[red][SKIP][/red] No match for {track_str}")
                continue

            best, score = matches[0]
            best_artists = ", ".join(a["name"] for a in best["artists"])
            song_str = f"{best['title']} — {best_artists}"
            vid = best["videoId"]

            if mode == "PLAYLIST" and vid in existing_ids:
                print_row(table, "SKIPPED (already added)", track_str, song_str, score)
                continue

            if score >= 90:
                if mode == "LIKES":
                    ytmusic_client.YTMUSIC.rate_song(vid, "LIKE")
                    print_row(table, "LIKED", track_str, song_str, score)
                else:
                    if ytmusic_client.add_with_retry(playlist_id, vid, existing_ids):
                        print_row(table, "ADDED", track_str, song_str, score)
                    else:
                        print_row(table, "SKIPPED (error)", track_str, song_str, score)
            else:
                # interactive fallback
                live.stop()
                chosen = ask_user_choice(track, matches)
                live.start()

                if chosen:
                    if mode == "LIKES":
                        ytmusic_client.YTMUSIC.rate_song(chosen["videoId"], "LIKE")
                        print_row(table, "LIKED", track_str, chosen["title"], score)
                    else:
                        ytmusic_client.YTMUSIC.add_playlist_items(
                            playlist_id, [chosen["videoId"]]
                        )
                        print_row(table, "ADDED", track_str, chosen["title"], score)
                else:
                    print_row(table, "SKIPPED (manual)", track_str, "-", 0)

    # wrap up
    if mode == "LIKES":
        console.print(Panel.fit("Completed transferring liked songs.", style="green"))
    else:
        console.print(
            Panel.fit(f"Completed transferring '{playlist_name}'", style="green")
        )


# -------------------
# Public API
# -------------------
def transfer_liked_songs():
    tracks = spotify_client.get_liked_tracks()
    ytm_cache = ytmusic_client.get_liked_cache()
    transfer_items(tracks, mode="LIKES", ytm_cache=ytm_cache)


def transfer_playlist():
    playlists = spotify_client.get_playlists()
    playlist_choice = questionary.select(
        "Pick a Spotify playlist to transfer:", [p["name"] for p in playlists]
    ).ask()
    if not playlist_choice:
        raise KeyboardInterrupt
    selected_playlist = next(p for p in playlists if p["name"] == playlist_choice)
    tracks = spotify_client.get_playlist_tracks(selected_playlist["id"])
    transfer_items(tracks, mode="PLAYLIST", playlist_name=selected_playlist["name"])
