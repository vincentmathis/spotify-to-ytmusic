import sys
import questionary
from transfer import transfer_liked_songs, transfer_playlist


# TODO explain setup for users in readme
# TODO typing


def main():
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
