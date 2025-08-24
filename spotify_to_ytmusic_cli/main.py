import os
import sys
import questionary
from platformdirs import user_config_dir
from transfer import transfer_liked_songs, transfer_playlist
from ytmusic_client import init_ytmusic_client
from spotify_client import init_spotify_client

# TODO explain setup for users in readme
# TODO typing


def init():
    config_dir = user_config_dir("spotify-to-ytmusic-cli", appauthor="vincent-mathis")
    os.makedirs(config_dir, exist_ok=True)
    init_ytmusic_client(config_dir)
    init_spotify_client(config_dir)


def main():
    init()

    try:
        choice = questionary.select(
            "What do you want to transfer?", ["Liked Songs", "Playlists", "Exit"]
        ).ask()
        if choice == "Exit" or choice is None:
            raise KeyboardInterrupt
        if choice == "Liked Songs":
            transfer_liked_songs()
        else:
            transfer_playlist()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
