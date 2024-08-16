from configparser import ConfigParser
from telegram import *
#from deezloader.deezloader import DeeLogin
import pyrebase
from youtube import *
from shutil import rmtree
import lyricsgenius as lg
from telegram.ext import *
from constants import *
from utils import *
import os
import re

config = ConfigParser()
config.read(".config.ini")
__location = "/app/"
__dir = "Songs"
path = os.path.join(__location, __dir)

#PORT = int(os.environ.get('PORT', 8443))

# Firebase Authentication
firebaseConfig = { "YOUR FIREBASE CONFIG" }

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# Deezer Configuration
__email = config['deezer_api']['email']
__password = config['deezer_api']['password']

# Enable after fix
#deez_api = DeeLogin(email = __email, password = __password)

# Genius Configuration
GENIUS_TOKEN = config['genius_api']['apiToken']
genius = lg.Genius(GENIUS_TOKEN, skip_non_songs = True, excluded_terms=["(Remix)", "(Live)"], remove_section_headers = True)

# Telegram Bot connection
API_TOKEN = config['telegram']['botToken']
bot = Bot(API_TOKEN)

def get_user_quality(user_id):
    key = db.child('quality').child(user_id).get()
    
    try:
        quality = key.val()['d_quality']
        return quality
    
    except:
        db.child('quality').child(user_id).set({"d_quality" : "MP3_128"})
        return "MP3_128"

def check_in_db(id, __quality):
    key = db.child('tracks').child(__quality).child(id).get()
    try:
        fileId = key.val()['file_id']
    except:
        fileId = None
    
    return fileId

def yt_down(chat_id, id, __quality, keyboard):
        
    songObj = create_trackObj(id)
    convertedFileName = f"{songObj['album']} CD {songObj['disc_number']} TRACK {songObj['track_number']}"
    
    try:
        convertedFilePath = yt_download(
            songObj["title"],
            [ele['name'] for ele in songObj['artists']],
            ', '.join(artist['name'] for artist in songObj['artists']),
            songObj["album"],
            songObj["duration"],
            convertedFileName,
            __quality
        )
            
        add_metadata(songObj, convertedFilePath, __quality)
        response = bot.send_audio(
            chat_id,
            caption = audio_caption,
            reply_markup = InlineKeyboardMarkup(keyboard),
            audio = open(convertedFilePath, 'rb')
        )

        os.remove(convertedFilePath)
                
        file_id = response['audio']['file_id']
        db.child("tracks").child(__quality).child(id).set({"file_id" : file_id})
        
        return bot.send_audio(
            chat_id = song_database,
            caption = f"{__quality}\n{audio_caption}",
            audio = file_id
        )

    except:
        if __quality == 'FLAC':
            bot.send_message(chat_id, "Cannot download in <b>FLAC</b>. Trying in <b>320kbps</b>", parse_mode = ParseMode.HTML)
            file_id = check_in_db(id, "MP3_320")
            if file_id is None:
                yt_down(chat_id, id, "MP3_320", keyboard)
            else:
                return bot.send_audio(
                    chat_id,
                    caption = audio_caption,
                    reply_markup = InlineKeyboardMarkup(keyboard),
                    audio = file_id
                )

        else:
            return bot.send_message(chat_id, download_error, parse_mode = ParseMode.HTML)

def deez_down(chat_id, id, keyboard):

    __quality = "MP3_128"
    
    link = "https://open.spotify.com/track/{}".format(id)
    track = deez_api.download_trackspo(
        link_track = link, 
        output_dir = 'Songs/', 
        quality_download = __quality,
        recursive_quality = True,
        method_save = 1
    )

    response = bot.send_audio(
        chat_id,
        caption = audio_caption,
        reply_markup = InlineKeyboardMarkup(keyboard),
        audio = open(track.song_path, 'rb')
    )
                    
    file_id = response['audio']['file_id']
    db.child("tracks").child(__quality).child(id).set({"file_id" : file_id})
    return bot.send_audio(
        chat_id = song_database,
        caption = f"{__quality}\n{audio_caption}",
        audio = file_id
    )

def track_provider(chat_id, id, __quality):
    
    file_id = check_in_db(id, __quality)
    keyboard = [
        [InlineKeyboardButton("View Track", callback_data = f"track:{id}"),
        InlineKeyboardButton("❌", callback_data = "close")]
    ]

    if file_id is None:
        # return bot.send_message(chat_id, download_error, parse_mode = ParseMode.HTML)

        if __quality == 'FLAC' or __quality == 'MP3_320':
           return yt_down(chat_id, id, __quality, keyboard)
       
        else:
           try:
               return deez_down(chat_id, id, keyboard)
       
           except:
               return yt_down(chat_id, id, __quality, keyboard)
    
    else:
        try:
            return bot.send_audio(
                chat_id,
                caption = audio_caption,
                reply_markup = InlineKeyboardMarkup(keyboard), 
                audio = file_id
            )
        
        except:
            # return bot.send_message(chat_id, download_error, parse_mode = ParseMode.HTML)

            try:
               return deez_down(chat_id, id, keyboard)
           
            except:
               return yt_down(chat_id, id, __quality, keyboard)
            
def track(track_id):
    data = create_trackObj(track_id)
    keyboard = []
    
    # Try for album art
    try:
        uri = f"art_download:{data['image_url'].split('https://i.scdn.co/image/')[1]}"
        keyboard.append([InlineKeyboardButton("🖼️ Download Cover Art", callback_data = uri)])
    except:
        pass

    # Try for canvas
    canvas = get_canvas(track_id)
    if canvas:
        uri = f"canvas:{canvas.split('/')[5]}:{canvas.split('/')[7].split('.')[0]}"
        keyboard.append([InlineKeyboardButton("🎥 Download Canvas", callback_data = uri)])

    keyboard.append([InlineKeyboardButton("🎵 Download Track", callback_data = f"track_download:{data['id']}")])
    keyboard.append([InlineKeyboardButton("💽 View Album : {}".format(data['album']), callback_data= f"album:{data['album_id']}")])
    for artist in data['artists']:
       keyboard.append([InlineKeyboardButton("👤 View Artist : {}".format(artist['name']), callback_data= f"artist:{artist['id']}")])
    
    if data['preview_url'] != 'None':
       keyboard.append([InlineKeyboardButton("🎧 Listen to Preview", url= f"{data['preview_url']}")])
    
    keyboard.append([InlineKeyboardButton("📃 Get Lyrics [BETA]", callback_data = f"lyrics:{data['id']}")])
    keyboard.append([InlineKeyboardButton("🔗 View on Spotify", url= f"https://open.spotify.com/track/{track_id}")])
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    caption = track_caption.format(
        data['title'],
        ', '.join(artist['name'] for artist in data['album_artists']),
        data['album'],
        data['popularity'],
        data['release_date'],
        data['is_explicit'],
        f"{int(float(data['duration'])) // 60}:{int(float(data['duration'])) % 60}",
        data['uri']
    )
    return keyboard, caption, data['image_url']

def artist(artist_id):
    data = create_artistObj(artist_id)
    keyboard = []
    try:
        keyboard.append([InlineKeyboardButton("🖼️ Download Cover Art", callback_data= f"art_download:{data['image_url'].split('https://i.scdn.co/image/')[1]}")])
    except:
        pass
    keyboard.append([InlineKeyboardButton("💽 Artist's Albums", callback_data= f"artist_albums:{data['id']}")])
    keyboard.append([InlineKeyboardButton("⭐ Top Tracks", callback_data= f"artist_top_tracks:{data['id']}")])
    keyboard.append([InlineKeyboardButton("🔗 View on Spotify", url= f"https://open.spotify.com/artist/{artist_id}")])
    caption = artist_caption.format(
        data['name'],
        '\n- '.join(genre.capitalize() for genre in data['genres']),
        data['popularity'],
        data['followers'],
        data['uri']
    )

    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard, caption, data['image_url'] 

def album(album_id):
    data = create_albumObj(album_id)
    keyboard = []
    try:
        keyboard.append([InlineKeyboardButton("🖼️ Download Cover Art", callback_data= f"art_download:{data['image_url'].split('https://i.scdn.co/image/')[1]}")])
    except:
        pass
    keyboard.append([InlineKeyboardButton("⬇️ Download Album", callback_data= f"album_download:{data['id']}")])
    keyboard.append([InlineKeyboardButton("🎶 View Album Tracks", callback_data= f"view_album_tracks:{data['id']}")])
    for artist in data['artists']:
        keyboard.append([InlineKeyboardButton("👤 View Artist : {}".format(artist['name']), callback_data= f"artist:{artist['id']}")])
        
    keyboard.append([InlineKeyboardButton("🔗 View on Spotify", url= f"https://open.spotify.com/album/{album_id}")])
    
    caption = album_caption.format(
        data['name'],
        ', '.join(artist['name'] for artist in data['artists']),
        data['popularity'],
        data['release_date'],
        data['total_tracks'],
        data['label'],
        data['uri']
    )
    
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard, caption, data['image_url']

def playlist(playlist_id):
    data = create_playlistObj(playlist_id)
    keyboard = []
    try:
        keyboard.append([InlineKeyboardButton("🖼️ Download Cover Art", callback_data= f"art_download:{data['image_url'].split('https://i.scdn.co/image/')[1]}")])
    except:
        pass
    keyboard.append([InlineKeyboardButton("🎶 Download Playlist", callback_data = f"playlist_download:{data['id']}")])
    keyboard.append([InlineKeyboardButton("🎶 View Playlist Tracks", callback_data = f"view_playlist_tracks:{data['id']}")])
    keyboard.append([InlineKeyboardButton("💽 View Owner : {}".format(data['owner']), callback_data= f"user:{data['owner_id']}")])
    keyboard.append([InlineKeyboardButton("🔗 View on Spotify", url= f"https://open.spotify.com/playlist/{playlist_id}")])
    caption = playlist_caption.format(
        data['name'],
        data['owner'],
        data['followers'],
        data['total_tracks'],
        data['is_collaborative'],
        data['uri']
    )
    
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard, caption, data['image_url']

def user(user_id):
    data = create_userObj(user_id)
    keyboard = []
    try:
        keyboard.append([InlineKeyboardButton("🖼️ Download Cover Art", callback_data= f"art_download:{data['image_url'].split('https://i.scdn.co/image/')[1]}")])
    except:
        pass
    keyboard.append([InlineKeyboardButton("🔗 View on Spotify", url= f"https://open.spotify.com/user/{user_id}")])
    caption = user_caption.format(
        data['name'],
        data['followers'],
        data['uri']
    )
    
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard, caption, data['image_url']

def view_tracks(type, id):
    keyboard = []
    count = 0
    if type == "playlist":
        data = data_fetch('playlists', id)
        for track in data['tracks']['items']:
            keyboard.append([InlineKeyboardButton(f"🎧 {track['track']['name']}", callback_data = f"track:{track['track']['id']}")])
            count += 1
    
    elif type == "album":
        data = data_fetch('albums', id)
        for track in data['tracks']['items']:
            keyboard.append([InlineKeyboardButton(f"🎧 {track['name']}", callback_data = f"track:{track['id']}")])
            count += 1
    
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return f"🎶 Found {count} tracks : ", keyboard

def top_tracks(id):
    data = data_fetch('artists', f"{id}/top-tracks?market=US")
    keyboard = []
    for track in data['tracks']:
        keyboard.append([InlineKeyboardButton(f"🎧 {track['name']}", callback_data = f"track:{track['id']}")])
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard

def artist_albums(id):
    data = data_fetch('artists', f"{id}/albums")
    keyboard = []
    for album in data['items']:
        keyboard.append([InlineKeyboardButton(f"💽 {album['name']}", callback_data = f"album:{album['id']}")])
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard

def new_releases():
    data = data_fetch('browse', 'new-releases')
    keyboard = []
    for album in data['albums']['items']:
        keyboard.append([InlineKeyboardButton(f"💽 {album['name']}", callback_data = f"album:{album['id']}")])
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard

def featured_playlists():
    data = data_fetch('browse', 'featured-playlists')
    keyboard = []
    for playlist in data['playlists']['items']:
        keyboard.append([InlineKeyboardButton(f"🎶 {playlist['name']}", callback_data = f"playlist:{playlist['id']}")])
    keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
    return keyboard

###############################################################################################

def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("👥 Official Group", url = "https://t.me/spotifydlchat"),
            InlineKeyboardButton("💾 Official Database", url = song_database_url)
        ], [
            InlineKeyboardButton("💽 New Releases", callback_data = "new_releases"), 
            InlineKeyboardButton("🎶 Featured Playlists", callback_data = "featured_playlists")
        ], [
            InlineKeyboardButton("❓ FAQ", url = "https://telegra.ph/SpotifyDL-Bot---FAQ-09-08"),
            InlineKeyboardButton("📚 GitHub", url = "https://github.com/abhilashmnair/SpotifyDL"),
            InlineKeyboardButton("📔 Help", callback_data = "help")
        ], [
            InlineKeyboardButton("💖 Donate", url = "https://buymeacoffee.com/abhilashmnair"),
            InlineKeyboardButton("😄 Feedback", url = "https://t.me/abhilashmnair")
        ], [
            InlineKeyboardButton("🛠️ Quality", callback_data = "quality")
        ]
    ]
    return update.message.reply_text(start_msg.format(update.effective_chat.full_name), reply_markup = InlineKeyboardMarkup(keyboard), parse_mode = "HTMl")

def help_command(update: Update, context):
    return update.message.reply_text(help_msg, parse_mode = "HTMl")

def donate(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("💖 Donate", url= "https://buymeacoffee.com/abhilashmnair")]
    ]

    return update.message.reply_text(donate_msg, reply_markup = InlineKeyboardMarkup(keyboard))

def quality(update: Update, context):
    user_id = update.message.from_user.id

    keyboard = [
        [InlineKeyboardButton("MP3_128", callback_data = "quality:MP3_128"),
        InlineKeyboardButton("MP3_320", callback_data = "quality:MP3_320"),
        InlineKeyboardButton("FLAC", callback_data = "quality:FLAC")],
        [InlineKeyboardButton("❌", callback_data = "close")]
    ]
    
    return update.message.reply_text(
        download_quality.format(get_user_quality(user_id)),
        reply_markup = InlineKeyboardMarkup(keyboard),
        parse_mode = "HTML")

def info(update: Update, context):
    return update.message.reply_text(info_msg, parse_mode = "HTML")

def browse(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("💽 New Releases", callback_data = "new_releases"), 
        InlineKeyboardButton("🎶 Featured Playlists", callback_data = "featured_playlists")]
    ]
    return update.message.reply_text(browse_msg, reply_markup = InlineKeyboardMarkup(keyboard), parse_mode = "HTML")

def track_search(update: Update, context):
    try:
        query = update.message.text.split('/track')[1]
        data = search_fetch_data(query, 'track')
        keyboard = []
        for track in data['tracks']['items']:
            keyboard.append(
                [InlineKeyboardButton(f"🎧 {track['name']} - {', '.join(artist['name'] for artist in track['album']['artists'])}",
                    callback_data = f"track:{track['id']}")
                ]
            )
        keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
        return update.message.reply_text('Top Results : 🔍', reply_markup = InlineKeyboardMarkup(keyboard))
    except:
        return update.message.reply_text('Query not found. Usage /track <code>query</code>', parse_mode = "HTML")

def artist_search(update: Update, context):
    try:
        query = update.message.text.split('/artist')[1]
        data = search_fetch_data(query, 'artist')
        keyboard = []
        for artist in data['artists']['items']:
            keyboard.append(
                [InlineKeyboardButton(f"👤 {artist['name']}", callback_data = f"artist:{artist['id']}")]
            )
        keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
        return update.message.reply_text('Top Results : 🔍', reply_markup = InlineKeyboardMarkup(keyboard))
    except:
        return update.message.reply_text('Query not found. Usage /artist <code>query</code>', parse_mode = "HTML")

def album_search(update: Update, context):
    try:
        query = update.message.text.split('/album')[1]
        data = search_fetch_data(query, 'album')
        keyboard = []
        for album in data['albums']['items']:
            keyboard.append(
                [InlineKeyboardButton(f"💽 {','.join(artist['name'] for artist in album['artists'])} - {album['name']}",
                    callback_data = f"album:{album['id']}")]
            )
        keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
        return update.message.reply_text('Top Results : 🔍', reply_markup = InlineKeyboardMarkup(keyboard))
    except:
        return update.message.reply_text('Query not found. Usage /album <code>query</code>', parse_mode = "HTML")

def playlist_search(update: Update, context):
    try:
        query = update.message.text.split('/playlist')[1]
        data = search_fetch_data(query, 'playlist')
        keyboard = []
        for playlist in data['playlists']['items']:
            keyboard.append(
                [InlineKeyboardButton(f"🎶 {playlist['owner']['display_name']} - {playlist['name']}",
                    callback_data = f"playlist:{playlist['id']}")]
            )
        keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
        return update.message.reply_text('Top Results : 🔍', reply_markup = InlineKeyboardMarkup(keyboard))
    except:
        return update.message.reply_text('Query not found. Usage /playlist <code>query</code>', parse_mode = "HTML")

def callback(update: Update, context):
    query = update.callback_query
    quality = get_user_quality(query.from_user.id)
    query.answer()
    if ':' in query.data:

        id = query.data.split(":")[1]
        
        if "track:" in query.data:
            keyboard, caption, image_url = track(id)
            return bot.send_photo(query.from_user.id, image_url ,caption, reply_markup= InlineKeyboardMarkup(keyboard), parse_mode = "HTML")
        
        elif "artist:" in query.data:
            keyboard, caption, image_url = artist(id)
            return bot.send_photo(query.from_user.id, image_url ,caption, reply_markup= InlineKeyboardMarkup(keyboard), parse_mode = "HTML")
        
        elif "album:" in query.data:
            keyboard, caption, image_url = album(id)
            return bot.send_photo(query.from_user.id, image_url ,caption, reply_markup= InlineKeyboardMarkup(keyboard), parse_mode = "HTML")
        
        elif "playlist:" in query.data:
            keyboard, caption, image_url = playlist(id)
            return bot.send_photo(query.from_user.id, image_url ,caption, reply_markup= InlineKeyboardMarkup(keyboard), parse_mode = "HTML")
        
        elif "user:" in query.data:
            keyboard, caption, image_url = user(id)
            return bot.send_photo(query.from_user.id, image_url ,caption, reply_markup= InlineKeyboardMarkup(keyboard), parse_mode = "HTML")
        
        elif "view_album_tracks:" in query.data:
            text, keyboard = view_tracks('album', id)
            return bot.send_message(query.from_user.id, text, reply_markup = InlineKeyboardMarkup(keyboard))
        
        elif "quality:" in query.data:
            db.child('quality').child(query.from_user.id).set({'d_quality' : id})
            
            keyboard = [
                [InlineKeyboardButton("MP3_128", callback_data = "quality:MP3_128"),
                InlineKeyboardButton("MP3_320", callback_data = "quality:MP3_320"),
                InlineKeyboardButton("FLAC", callback_data = "quality:FLAC")],
                [InlineKeyboardButton("❌", callback_data = "close")]
            ]
            
            return bot.edit_message_text(
                chat_id = query.from_user.id,
                message_id = query.message.message_id,
                text = download_quality.format(id),
                reply_markup = InlineKeyboardMarkup(keyboard),
                parse_mode = "HTML"
            )

        elif "view_playlist_tracks:" in query.data:
            text, keyboard = view_tracks('playlist', id)
            return bot.send_message(query.from_user.id, text, reply_markup = InlineKeyboardMarkup(keyboard))
        
        elif "artist_top_tracks:" in query.data:
            keyboard = top_tracks(id)
            return bot.send_message(query.from_user.id, "⭐ Top Tracks", reply_markup = InlineKeyboardMarkup(keyboard))
        
        elif "artist_albums:" in query.data:
            keyboard = artist_albums(id)
            return bot.send_message(query.from_user.id, "⭐ Top Albums", reply_markup = InlineKeyboardMarkup(keyboard))
        
        elif 'lyrics:' in query.data:
            data = create_trackObj(id)
            song = genius.search_song(f"{data['title']} - {data['artists'][0]['name']}")
            keyboard_markup = [[InlineKeyboardButton("❌", callback_data = "close")]]
            try:
                return bot.send_message(
                    query.from_user.id,
                    lyrics_caption.format(re.sub(r"[0-9]*Embed","",song.lyrics)),
                    reply_markup = InlineKeyboardMarkup(keyboard_markup),
                    parse_mode = "HTML"
                )
            except:
                return bot.send_message(
                    query.from_user.id,
                    "<b>❗ Lyrics not found ❗</b>",
                    reply_markup = InlineKeyboardMarkup(keyboard_markup),
                    parse_mode = "HTML"
                )

        elif "art_download:" in query.data:
            url = query.data.split('art_download:')[1]
            keyboard_markup = [[InlineKeyboardButton("❌", callback_data = "close")]]
            return bot.send_document(
                query.from_user.id, 
                document = "https://i.scdn.co/image/{}".format(url),
                reply_markup = InlineKeyboardMarkup(keyboard_markup)
            )
        
        elif "canvas:" in query.data:
            _, licensor, uri = query.data.split(':')
            keyboard_markup = [[InlineKeyboardButton("❌", callback_data = "close")]]
            try:
                return bot.send_video(
                    query.from_user.id,
                    "https://canvaz.scdn.co/upload/licensor/{}/video/{}.cnvs.mp4".format(licensor, uri),
                    reply_markup = InlineKeyboardMarkup(keyboard_markup)
                )
            except:
                return bot.send_video(
                    query.from_user.id,
                    "https://canvaz.scdn.co/upload/artist/{}/video/{}.cnvs.mp4".format(licensor, uri),
                    reply_markup = InlineKeyboardMarkup(keyboard_markup)
                )

        elif "track_download:" in query.data:
            bot.send_message(query.from_user.id, fetching_tracks)
            track_provider(query.from_user.id, id, quality)
            keyboard = [
                [InlineKeyboardButton("💖 Donate", url = "https://buymeacoffee.com/abhilashmnair")],
                [InlineKeyboardButton("💾 Database", url = song_database_url)]
            ]
            return bot.send_message(query.from_user.id, successful_download, reply_markup = InlineKeyboardMarkup(keyboard), parse_mode = "HTML")
        
        elif "album_download:" in query.data:
            data = data_fetch('albums', id)
            bot.send_message(query.from_user.id, fetching_tracks)
            for a_track in data['tracks']['items']:
                track_provider(query.from_user.id, a_track['id'], quality)

            keyboard = [
                [InlineKeyboardButton("💖 Donate", url = "https://buymeacoffee.com/abhilashmnair")],
                [InlineKeyboardButton("💾 Database", url = song_database_url)]
            ]
            return bot.send_message(query.from_user.id, successful_download, reply_markup = InlineKeyboardMarkup(keyboard), parse_mode = "HTML")


        elif "playlist_download:" in query.data:
            data = data_fetch('playlists', id)
            _count = 1
            bot.send_message(query.from_user.id, fetching_tracks)
            for p_track in data['tracks']['items']:
                track_provider(query.from_user.id, p_track['track']['id'], quality)
                _count += 1
                if _count > 50:
                    break
            
            keyboard = [
                [InlineKeyboardButton("💖 Donate", url = "https://buymeacoffee.com/abhilashmnair")],
                [InlineKeyboardButton("💾 Database", url = song_database_url)]
            ]
            
            return bot.send_message(query.from_user.id, successful_download, reply_markup = InlineKeyboardMarkup(keyboard), parse_mode = "HTML")
        
    elif "new_releases" == query.data:
        keyboard = new_releases()
        return bot.send_message(query.from_user.id, "💽 Newly Released Albums", reply_markup = InlineKeyboardMarkup(keyboard))
    
    elif "featured_playlists" == query.data:
        keyboard = featured_playlists()
        return bot.send_message(query.from_user.id, "🎶 Featured Playlists", reply_markup = InlineKeyboardMarkup(keyboard))

    elif "quality" == query.data:
        keyboard = [
            [InlineKeyboardButton("MP3_128", callback_data = "quality:MP3_128"),
            InlineKeyboardButton("MP3_320", callback_data = "quality:MP3_320"),
            InlineKeyboardButton("FLAC", callback_data = "quality:FLAC")],
            [InlineKeyboardButton("❌", callback_data = "close")]
        ]
    
        return bot.send_message(
            query.from_user.id,
            download_quality.format(get_user_quality(query.from_user.id)),
            reply_markup = InlineKeyboardMarkup(keyboard),
            parse_mode = "HTML"
        )

    elif "help" == query.data:
        keyboard_markup = [[InlineKeyboardButton("❌", callback_data = "close")]]
        return bot.send_message(
            query.from_user.id,
            help_msg,
            reply_markup = InlineKeyboardMarkup(keyboard_markup),
            parse_mode = "HTML"
        )

    elif "close" == query.data:
        return bot.delete_message(query.from_user.id, query.message.message_id)

    try:
        rmtree(path)
    except:
        pass

def url_query(update: Update, context):
    try:
        url = update.message.text

        if 'open.spotify.com' in url:
            if '?' in url:
                id = url.split('/')[4].split('?')[0]
            else:
                id = url.split('/')[4]
        
            if 'track' in url:
                keyboard_markup, caption, image_url = track(id)
                return update.message.reply_photo(image_url ,caption, reply_markup = InlineKeyboardMarkup(keyboard_markup), parse_mode = "HTML")

            elif 'artist' in url:
                keyboard_markup, caption, image_url = artist(id)
                return update.message.reply_photo(image_url ,caption, reply_markup = InlineKeyboardMarkup(keyboard_markup), parse_mode = "HTML")
        
            elif 'album' in url:
                keyboard_markup, caption, image_url = album(id)
                return update.message.reply_photo(image_url ,caption, reply_markup = InlineKeyboardMarkup(keyboard_markup), parse_mode = "HTML")

            elif 'playlist' in url:
                keyboard_markup, caption, image_url = playlist(id)
                return update.message.reply_photo(image_url ,caption, reply_markup = InlineKeyboardMarkup(keyboard_markup), parse_mode = "HTML")

            elif 'user' in url:
                keyboard_markup, caption, image_url = user(id)
                return update.message.reply_photo(image_url ,caption, reply_markup = InlineKeyboardMarkup(keyboard_markup), parse_mode = "HTML")

        else:
            data = search_fetch_data(url, 'track')
            keyboard = []
            for _track in data['tracks']['items']:
                keyboard.append(
                    [InlineKeyboardButton(f"🎧 {_track['name']} - {', '.join(artist['name'] for artist in _track['album']['artists'])}",
                    callback_data = f"track:{_track['id']}")]
                )
            keyboard.append([InlineKeyboardButton("❌", callback_data = "close")])
            return update.message.reply_text('Top Results : 🔍', reply_markup = InlineKeyboardMarkup(keyboard))

    except:
        return update.message.reply_text('Oops! Cannot process. See /help for available commands.')

def main():
    updater = Updater(API_TOKEN, use_context = True, workers = 32)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start, run_async = True))
    dispatcher.add_handler(CommandHandler("help", help_command, run_async = True))
    dispatcher.add_handler(CommandHandler("donate", donate, run_async = True))
    dispatcher.add_handler(CommandHandler("quality", quality, run_async = True))
    dispatcher.add_handler(CommandHandler("browse", browse, run_async = True))
    dispatcher.add_handler(CommandHandler("info", info, run_async = True))
    dispatcher.add_handler(CommandHandler("track", track_search, run_async = True))
    dispatcher.add_handler(CommandHandler("artist", artist_search, run_async = True))
    dispatcher.add_handler(CommandHandler("album", album_search, run_async = True))
    dispatcher.add_handler(CommandHandler("playlist", playlist_search, run_async = True))
    
    dispatcher.add_handler(MessageHandler(Filters.text, url_query, run_async = True))
    dispatcher.add_handler(CallbackQueryHandler(callback, run_async = True))

    updater.start_polling(drop_pending_updates=True)

    print('Polling started...')

    updater.idle()

if __name__ == '__main__':
    main()
