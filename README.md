# CLI tool to port liked songs and playlists from Spotify to YT Music.

## Use Poetry to install dependencies in virtual environment

In the folder with `pyproject.toml` run `poetry install`.

When you first run the program, it will create a folder in your config directory:

|OS|Directory|
|---|---|
|Windows|`C:\Users\<user>\AppData\Local\vincent-mathis\spotify-to-ytmusic-cli\`|
|Linux|`~/.config/vincent-mathis/spotify-to-ytmusic-cli/`|

Before you continue you need to setup some files.

## Spotify Client

Create a [Spotify Dev App](https://developer.spotify.com/dashboard) and copy the client id and secret into the `spotify-oauth-creds.json` file that has been created in the config dir.

## YT Music Client

Create a [Google Cloud App](https://console.cloud.google.com/apis/credentials). Download the json file and put it in the config dir as `ytmusic-oauth-creds.json`

Under the [Audience Tab](https://console.cloud.google.com/auth/audience) you need to add yourself (your google account email) as test user because the google cloud app is unverified and unpublished.

## Finishing Setup

After creating the apps and handling the config files you can return to your terminal and finish the OAuth flow as instructed.