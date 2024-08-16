start_msg = (
    "<b>Hi! {}</b> 👋\n"
    "This is the <b>SpotifyDL Bot</b>!\n"
    "I can help you search 🔍, listen 🎧 and download 📱 songs easily using Spotify URLs and custom queries! "
    "You can directly send Spotify URLs of tracks, playlists and albums to download them.\n---\n"
    "<b>Use Help to know about command usage.</b>"
)

browse_msg = (
    "Hey! You have selected the <b>Browse Section.</b> "
    "Discover newly released albums and featured playlists from Spotify!"
)

donate_msg = (
    "Support the developer. It would mean a lot!"
)

info_msg = (
    "<b>Deployed on Heroku</b>\nEstablished : Dec 2020\n"
    "---\n"
    "A huge thanks to @Anonimia for the library\n"
    "And thanks to all my users. 💖"
)

help_msg = (
    "<b>--- General Commands ---</b>\n"
    "/start - Start the bot\n"
    "/help - Show the commands\n"
    "/quality - Set the bot quality\n"
    "\n<b>--- Query Commands ---</b>\n"
    "/track {query} - Search track\n"
    "/artist {query} - Search artist\n"
    "/album {query} - Serach album\n"
    "/playlist {query} - Search playlist\n"
    "/browse - Discover new music!\n"
    "\n<b>--- Additional Commands ---</b>\n"
    "/info - Show the info about the bot\n"
    "/donate - Support the effort\n"
)

track_caption = (
    "🎵 <b>Title</b> : {}\n"
    "👥 <b>Artists</b> : {}\n"
    "💽 <b>Album</b> : {}\n"
    "❤️ <b>Popularity</b> : {}\n"
    "📅 <b>Release Date</b> : {}\n"
    "⚠️ <b>Explicit</b> : {}\n"
    "🕐 Duration : {}\n\n"
    "<b>URI</b> : <code>{}</code>"
)

artist_caption = (
    "👤 <b>Artist Name</b> : {}\n"
    "🎶 <b>Artist Genres</b> : \n- {}\n"
    "❤️ <b>Popularity</b> : {}\n"
    "👥 <b>Followers</b> : {}\n\n"
    "<b>URI</b> : <code>{}</code>"
)

album_caption = (
    "💽 <b>Album Name</b> : {}\n"
    "👥 <b>Album Artists</b> : {}\n"
    "❤️ <b>Popularity</b> : {}\n"
    "📅 <b>Release Date</b> : {}\n"
    "🎶 <b>Total Tracks</b> : {}\n"
    "🏷️ <b>Release Label</b> : {}\n\n"
    "<b>URI</b> : <code>{}</code>"
)

playlist_caption = (
    "🎶 <b>Playlist Name</b> : {}\n"
    "👤 <b>Playlist Owner</b> : {}\n"
    "❤️ <b>Followers</b> : {}\n"
    "🎶 <b>Total Tracks</b> : {}"
    "\n🤝 <b>Collaborative</b> : {}\n\n"
    "<b>URI</b> : <code>{}</code>\n\n"
    "<code>Note : Playlist download is limited to 50 tracks.</code>"
)

lyrics_caption = (
    "<i>{}</i>"
)

download_quality = (
    "⚙️ Download quality\n"
    "<i>Note: Some songs may not be available in given quality.</i>\n\n"
    "<code>Current quality : {}</code>")

user_caption = (
    "👤 <b>Name</b> : {}\n"
    "❤️ <b>Followers</b> : {}\n\n"
    "<b>URI</b> : <code>{}</code>"
)

successful_download  = (
    "<i>Thanks for using the bot! 💜</i>"
)

download_error = (
    "<i>Oops! Couldn't download the song!</i>"
)

fetching_tracks = (
    "Please wait, we are downloading the tracks!"
)

audio_caption = (
    "🤖 @spotifydl_mp3_bot"
)

song_database = ("@spotifydatabase")

song_database_url =("https://t.me/spotifydatabase")