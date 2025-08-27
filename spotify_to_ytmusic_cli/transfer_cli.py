import asyncio
import questionary
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

from transfer_core import transfer_likes, transfer_playlist
from transfer_session import TransferSession

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


async def ask_user_choice(sp, matches):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,  # default thread pool
        lambda: _ask(sp, matches)
    )


def _ask(sp, matches):
    console.print(
        Panel.fit(
            f"Low confidence match for [yellow]{sp['title']}[/yellow] — {sp['artist']}",
            style="red",
        )
    )

    choices = [
        f"{r['title']} — {', '.join(a['name'] for a in r.get('artists', []))} ({sc:.0f}%)"
        for r, sc in matches[:5]
    ] + ["Skip"]
    # FIXME doesn't show
    choice = questionary.select(
        f"Pick best match for {sp['title']} — {sp['artist']}:",
        choices
    ).ask()

    if choice == "Skip":
        return None
    return matches[choices.index(choice)][0]


async def run_transfer(session: TransferSession):
    """Consume events from session and render CLI with Rich."""
    # We don’t know total upfront → update once we get first progress
    layout, table, progress, task = create_layout(100)

    with Live(layout, console=console, refresh_per_second=4) as live:
        async def callback(ev):
            nonlocal table, progress, task

            if ev.event == "progress":
                done, total = ev.data["done"], ev.data["total"]
                if progress.tasks[task].total != total:
                    progress.update(task, total=total)
                progress.update(task, completed=done)
                live.refresh()

            elif ev.event == "match":
                sp = ev.data["spotify"]
                yt = ev.data.get("yt")
                score = ev.data.get("score", 0)
                sp_str = f"{sp['title']} — {sp['artist']}" if sp else "-"
                yt_str = (
                    f"{yt['title']} — {', '.join(a['name'] for a in yt['artists'])}"
                    if yt else "-"
                )
                table.add_row(ev.data["action"], sp_str, yt_str, f"{score}%")
                live.refresh()

            elif ev.event == "choice_required":
                chosen = await ask_user_choice(ev.data["spotify"], ev.data["matches"])
                event = session.step(chosen)
                if event:
                    await callback(event)
                    await session.run(callback)

            elif ev.event == "done":
                console.print(Panel.fit("Transfer completed!", style="green"))

        await session.run(callback)


# -------------------
# CLI Entrypoints
# -------------------
def transfer_liked_songs_cli():
    session = TransferSession(transfer_likes(auto_mode="ask"))
    asyncio.run(run_transfer(session))


def transfer_playlist_cli():
    session = TransferSession(transfer_playlist(auto_mode="ask"))
    asyncio.run(run_transfer(session))


if __name__ == "__main__":
    # Example: run likes transfer
    transfer_liked_songs_cli()
