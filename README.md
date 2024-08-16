# SpotifyDL - A Telegram Bot for downloading songs

**I am NOT responsible for using this program by other people and DO NOT recommend you do this illegally or against Deezer's terms of service.**
**This project is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)**

This is the code repo for Telegram's webhook that can download songs using queries and Spotify URLs.
Special thanks to [An0nimia](https://github.com/An0nimia/) for his library

## Usage

Get all the credentials required for running the bot and update the `.config.ini` file
- [Spotify Credentials](https://developer.spotify.com/)
- [Deezer Credentials](https://developers.deezer.com/)
- [Genius API Key](https://docs.genius.com/)
- [Telegram Bot Token](https://telegram.me/BotFather)
- [Google Firebase Database](https://firebase.google.com/)

Add your Google Firebase config in `index.py`. This is used as a cache to save trackid and its url.

Run the code using
```
pip3 install -r requiremnets.txt
python3 index.py
```

`Note: This can be hosted on Heroku or other platforms. Configurations for those platforms are to be done before running the code`
