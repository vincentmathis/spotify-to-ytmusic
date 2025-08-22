from transfer import transfer_liked_songs, transfer_playlist
import questionary


def transfer():
    choice = questionary.select(
        "What do you want to transfer?", ["Liked Songs", "Playlists"]
    ).ask()
    if choice == "Liked Songs":
        transfer_liked_songs()
    else:
        transfer_playlist()


if __name__ == "__main__":
    transfer()
