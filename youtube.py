from urllib.request import urlopen
from unidecode import unidecode
from ytmusicapi import YTMusic
from rapidfuzz.fuzz import partial_ratio
from mutagen.easyid3 import EasyID3, ID3
from mutagen.id3 import APIC
from mutagen.flac import FLAC, Picture
from mutagen import File
from yt_dlp import YoutubeDL
import os

ytmApiClient = YTMusic()

def match_percentage(str1, str2, score_cutoff = 0):
    try:
        return partial_ratio(str1, str2, score_cutoff=score_cutoff)
    
    except:
        newStr1 = ""
        for eachLetter in str1:
            if eachLetter.isalnum() or eachLetter.isspace():
                newStr1 += eachLetter
        newStr2 = ""
        for eachLetter in str2:
            if eachLetter.isalnum() or eachLetter.isspace():
                newStr2 += eachLetter
        return partial_ratio(newStr1, newStr2, score_cutoff=score_cutoff)


def _parse_duration(duration):
    try:
        mappedIncrements = zip([1, 60, 3600], reversed(duration.split(":")))
        seconds = 0
        for multiplier, time in mappedIncrements:
            seconds += multiplier * int(time)
        return float(seconds)

    except (ValueError, TypeError, AttributeError):
        return 0.0


def _map_result_to_song_data(result):
    song_data = {}
    artists = ", ".join(map(lambda a: a["name"], result["artists"]))
    video_id = result["videoId"]
    if video_id is None:
        return {}
    song_data = {
        "name": result["title"],
        "type": result["resultType"],
        "artist": artists,
        "length": _parse_duration(result.get("duration", None)),
        "link": f"https://www.youtube.com/watch?v={video_id}",
        "position": 0,
    }

    album = result.get("album")
    if album:
        song_data["album"] = album["name"]
    return song_data


def _query_and_simplify(searchTerm, filter):
    searchResult = ytmApiClient.search(searchTerm, filter=filter)
    return list(map(_map_result_to_song_data, searchResult))

def search_and_get_best_match(songName, songArtists, songAlbumName, songDuration):
    songTitle = create_song_title(songName, songArtists)
    song_results = _query_and_simplify(songTitle, filter="songs")
    songs = order_ytm_results(song_results, songName, songArtists, songAlbumName, songDuration)

    if len(songs) != 0:
        best_result = max(songs, key=lambda k: songs[k])

        if songs[best_result] >= 80:
            return best_result

    video_results = _query_and_simplify(create_song_title(songName, songArtists), filter="videos")
    videos = order_ytm_results(video_results, songName, songArtists, songAlbumName, songDuration)
    results = {**songs, **videos}

    if len(results) == 0:
        return None

    resultItems = list(results.items())
    sortedResults = sorted(resultItems, key=lambda x: x[1], reverse=True)
    return sortedResults[0][0]


def order_ytm_results(results, songName, songArtists, songAlbumName, songDuration):
    linksWithMatchValue = {}

    for result in results:
        if result == {}:
            continue
        lowerSongName = songName.lower()
        lowerResultName = result["name"].lower()

        sentenceAWords = lowerSongName.replace("-", " ").split(" ")
        commonWord = False
        for word in sentenceAWords:
            if word != "" and word in lowerResultName:
                commonWord = True

        if not commonWord:
            continue

        artistMatchNumber = 0
        if result["type"] == "song":
            for artist in songArtists:
                if match_percentage(unidecode(artist.lower()), unidecode(result["artist"]).lower(), 85):
                    artistMatchNumber += 1
        else:
            for artist in songArtists:
                if match_percentage(unidecode(artist.lower()), unidecode(result["name"]).lower(), 85):
                    artistMatchNumber += 1
            if artistMatchNumber == 0:
                for artist in songArtists:
                    if match_percentage(unidecode(artist.lower()), unidecode(result["artist"].lower()), 85):
                        artistMatchNumber += 1

        if artistMatchNumber == 0:
            continue

        artistMatch = (artistMatchNumber / len(songArtists)) * 100

        song_title = create_song_title(songName, songArtists)
        if result["type"] == "song":
            nameMatch = round(match_percentage(unidecode(result["name"]), unidecode(songName), 60), ndigits=3)
        else:
            nameMatch = round(match_percentage(unidecode(result["name"]), unidecode(song_title), 60), ndigits=3)

        if nameMatch == 0:
            continue

        albumMatch = 0.0
        if result["type"] == "song":
            album = result.get("album")
            if album:
                albumMatch = match_percentage(album, songAlbumName)

        delta = result["length"] - songDuration
        nonMatchValue = (delta ** 2) / songDuration * 100
        timeMatch = 100 - nonMatchValue

        if result["type"] == "song":
            if album is not None:
                if (match_percentage(album.lower(), result["name"].lower()) > 95 and album.lower() != songAlbumName.lower()):
                    avgMatch = (artistMatch + nameMatch + timeMatch) / 3
                else:
                    avgMatch = (artistMatch + albumMatch + nameMatch + timeMatch) / 4
            else:
                avgMatch = (artistMatch + nameMatch + timeMatch) / 3
        else:
            avgMatch = (artistMatch + nameMatch + timeMatch) / 3
        linksWithMatchValue[result["link"]] = avgMatch
    return linksWithMatchValue

def create_song_title(songName, songArtists):
    joined_artists = ", ".join(songArtists)
    return f"{joined_artists} - {songName}"

def __get_tronc(string):
	l_encoded = len(string.encode())

	if l_encoded > 242:
		n_tronc = len(string) - l_encoded - 242
	else:
		n_tronc = 242

	return n_tronc

def yt_download(title, rawArtists, artists, album, duration, convertedFileName, __quality):
    youtubeSongUrl = search_and_get_best_match(title, rawArtists, album, float(duration))
    if youtubeSongUrl is None:
        videoId = ytmApiClient.search(f'{artists} - {title}', filter='songs')[0]['videoId']
        youtubeSongUrl = f"https://youtube.com/watch?v={videoId}"
    
    n_tronc = __get_tronc(convertedFileName)
    convertedFilePath = os.path.join('.',convertedFileName[:n_tronc]) + '.mp3'

    if __quality == 'FLAC':
        codec = 'flac'
        bitrate = '848'

        convertedFilePath = os.path.join('.',convertedFileName[:n_tronc]) + '.flac'
    
    elif __quality == 'MP3_320':
        codec = 'mp3'
        bitrate = '320'

    else:
        codec = 'mp3'
        bitrate = '128'

    ydl_opts = {
        "format" : "bestaudio",
        'noplaylist': True,
        "nocheckcertificate": True,
        "outtmpl": f"{convertedFilePath}",
        "quiet": True,
        "addmetadata": True,
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [{'key': 'FFmpegExtractAudio', 'preferredcodec': codec, 'preferredquality': bitrate}],
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(youtubeSongUrl)

    return convertedFilePath

def add_metadata(songObj, convertedFilePath, __quality):
    if __quality == 'FLAC':
        audioFile = FLAC(convertedFilePath)
    else:
        audioFile = EasyID3(convertedFilePath)
    
    audioFile.delete()

    artists = ', '.join(artist['name'] for artist in songObj['artists'])
    albumArtists = ', '.join(artist['name'] for artist in songObj['album_artists'])

    audioFile['title'] = songObj["title"]
    audioFile['discnumber'] = str(songObj["disc_number"])
    audioFile['tracknumber'] = str(songObj["track_number"])
    audioFile['artist'] = artists
    audioFile['album'] = songObj["album"]
    audioFile['albumartist'] = albumArtists
    audioFile['originaldate'] = str(songObj["release_date"][:4])
    audioFile['date'] = str(songObj["release_date"][:4])
    
    if __quality == 'FLAC':
       audioFile.save()
    else:
        audioFile.save(v2_version=3)
    

    if __quality == 'FLAC':
        audioFile = File(convertedFilePath)
        image = Picture()
        image.type = 3
        image.mime = 'image/jpeg'
        image.data = urlopen(songObj["image_url"]).read()
        audioFile.add_picture(image)
        audioFile.save()
    
    else:
        audioFile = ID3(convertedFilePath)
        audioFile['APIC'] = APIC(encoding=3,mime='image/jpeg',type=3,desc='Album Art',data = urlopen(songObj["image_url"]).read())
        audioFile.save(v2_version=3)