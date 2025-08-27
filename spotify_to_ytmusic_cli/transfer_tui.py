import asyncio # TODO huh?
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, ProgressBar, SelectionList
from textual.reactive import reactive
from transfer_core import transfer_likes
from transfer_session import TransferSession


class TransferApp(App):
    progress_value = reactive(0)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Static("Menu", classes="menu-title"),
                SelectionList(
                    ("Transfer Likes", "likes"),
                    ("Transfer Playlist", "playlist"),
                    ("Settings", "settings"),
                    id="menu",
                ),
                id="sidebar",
            ),
            Vertical(
                Static("Transfers", classes="panel-title"),
                DataTable(id="table"),
                ProgressBar(total=100, id="progress"),
                id="main",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        # Prepare table
        table = self.query_one("#table", DataTable)
        table.add_columns("Action", "Spotify", "YouTube", "Confidence")

        # Start transfer session
        self.session = TransferSession(transfer_likes())
        self.call_later(self.run_session)

    async def run_session(self):
        async def callback(ev):
            self.handle_event(ev)

        await self.session.run(callback)

    def handle_event(self, ev):
        table = self.query_one("#table", DataTable)
        progress = self.query_one("#progress", ProgressBar)

        if ev.event == "progress":
            done, total = ev.data["done"], ev.data["total"]
            progress.update(total=total)
            progress.progress = done

        elif ev.event == "match":
            spotify = ev.data["spotify"]
            yt = ev.data.get("yt")
            score = ev.data.get("score", 0)
            spotify_str = f"{spotify['title']} — {spotify['artist']}" if spotify else "-"
            yt_str = f"{yt['title']} — {', '.join(a['name'] for a in yt['artists'])}" if yt else "-"
            table.add_row(ev.data["action"], spotify_str, yt_str, f"{score}%")

        elif ev.event == "choice_required":
            # Instead of notify, open a modal later
            self.notify(f"Manual choice required for {ev.data['spotify']['title']}", timeout=3)

            # Example: auto-send first match to resume
            chosen = ev.data["matches"][0][0]  # pick best match
            event = self.session.step(chosen)
            if event:
                self.handle_event(event)
                self.call_later(self.run_session)

        elif ev.event == "done":
            self.notify("Transfer completed!", timeout=5)


if __name__ == "__main__":
    TransferApp().run()
