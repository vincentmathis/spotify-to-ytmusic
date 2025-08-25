from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
import questionary

console = Console()


def create_layout(track_count):
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    )
    task = progress.add_task("Transferring", total=track_count)

    table = Table(show_header=True, header_style="bold", expand=True, box=None)
    table.add_column("Action", style="yellow", overflow="fold", ratio=1)
    table.add_column("Spotify Track", style="green", overflow="fold", ratio=2)
    table.add_column("YouTube Song", style="red", overflow="fold", ratio=2)
    table.add_column(
        "Confidence", style="white", justify="right", width=10, no_wrap=True
    )

    layout = Layout()
    layout.split_column(
        Layout(Panel(table, title="Data"), name="upper"),
        Layout(Panel(progress, title="Progress"), name="lower", size=3),
    )
    return layout, table, progress, task


def print_row(table, action, track_str, song_str, score):
    table.add_row(action, track_str, song_str, f"{score:.0f}%")


def ask_user_playlist(playlists):
    playlist_choice = questionary.select(
        "Pick a Spotify playlist to transfer:", [p["name"] for p in playlists]
    ).ask()
    return playlist_choice


def ask_user_choice(track, matches):
    console.print(
        f"Could not auto-match: {track['title']} — {track['artist']}", style="red"
    )
    choices = [
        f"{r['title']} — {', '.join(a['name'] for a in r.get('artists', []))} (https://music.youtube.com/watch?v={r['videoId']}, {sc:.0f}%)"
        for r, sc in matches[:10]
    ] + ["Skip"]
    choice = questionary.select("Pick best match:", choices).ask()
    return None if choice == "Skip" else matches[choices.index(choice)][0]


def show_completion_message(mode, playlist_name=None):
    msg = (
        "Completed transferring liked songs."
        if mode == "LIKES"
        else f"Completed transferring '{playlist_name}'"
    )
    text = Text(msg, justify="center")
    console.print(Panel(text, expand=True, style="green"))
