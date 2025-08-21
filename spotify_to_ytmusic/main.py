import typer
from spotify_client import (
    get_spotify_client,
    get_liked_tracks,
    get_playlists,
    get_playlist_tracks,
)
from ytmusic_client import get_ytmusic_client, get_liked_cache
from transfer import transfer_liked_songs, transfer_playlist
import questionary
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer()

# TODO deduplication in liked songs and playlists

@app.command()
def transfer():
    # TODO instanciate singletons in their modules instead of calling and passing the clients from main 
    sp = get_spotify_client()
    ytmusic = get_ytmusic_client()

    choice = questionary.select(
        "What do you want to transfer?", ["Liked Songs", "Playlists"]
    ).ask()

    if choice == "Liked Songs":
        ytm_cache = get_liked_cache(ytmusic)
        tracks = get_liked_tracks(sp)
        transfer_liked_songs(ytmusic, tracks, ytm_cache)

    else:
        playlists = get_playlists(sp)
        playlist_choice = questionary.select(
            "Pick a Spotify playlist to transfer:", [p["name"] for p in playlists]
        ).ask()
        selected_playlist = next(p for p in playlists if p["name"] == playlist_choice)
        tracks = get_playlist_tracks(sp, selected_playlist["id"])
        transfer_playlist(ytmusic, selected_playlist["name"], tracks)


if __name__ == "__main__":
    app()
