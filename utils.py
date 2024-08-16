from configparser import ConfigParser
import base64
import requests
from bs4 import BeautifulSoup

config = ConfigParser()
config.read(".config.ini")

placeholder_image_url = "https://i.ibb.co/51PrFy7/Green-and-black-logo-of-Spotify-at-green-background.jpg"

# Spotify End-point Authorization
tokenUrl = "https://accounts.spotify.com/api/token"
requestUrl = "https://api.spotify.com/v1/"
headers = {}
data = {}
r_data = {}

__clientId = config['spotify_api']['clientId']
__clientSecret = config['spotify_api']['clientSecret']
__refreshToken = config['spotify_api']['refresh_token']

message = f"{__clientId}:{__clientSecret}"
messageBytes = message.encode('ascii')
base64Bytes = base64.b64encode(messageBytes)
authToken = base64Bytes.decode('ascii')

headers['Authorization'] = f"Basic {authToken}"
data['grant_type'] = "client_credentials"

r_data['grant_type'] = "refresh_token"
r_data['refresh_token'] = __refreshToken

r = requests.post(tokenUrl, headers=headers, data=data)
token = r.json()['access_token']
config['spotify_api']['token'] = token

with open('.config.ini', 'w') as configfile:
    config.write(configfile)

def generate_token():
    r = requests.post(tokenUrl, headers = headers, data = r_data)
    token = r.json()['access_token']
    config['spotify_api']['token'] = token

    with open('.config.ini', 'w') as configfile:
        config.write(configfile)
    
    return token

def search_fetch_data(query,type):
    __token = config['spotify_api']['token']
    headers = { "Authorization": "Bearer " + __token }
    response = requests.get(url = "{}search?q={}&type={}&limit=10".format(requestUrl, query, type), headers = headers)
    
    if response.status_code == 401:
        __token = generate_token()
        headers = { "Authorization": "Bearer " + __token }
        response = requests.get(url = "{}search?q={}&type={}&limit=10".format(requestUrl, query, type), headers = headers)

    return response.json()

# Spotify Canvas Workaround
def get_canvas(id):
    canvas_url = "https://canvasdownloader.com/canvas?link=https://open.spotify.com/track/{}"
    canvas_headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36' }

    response = requests.get(url = canvas_url.format(id), headers = canvas_headers)
    soup = BeautifulSoup(response.text, "html.parser")

    try:
        video_tag = soup.find("video", {"id" : "canvas_vid"})
        return video_tag.source['src']
    except:
        return None

def data_fetch(endpoint, id):
    __token = config['spotify_api']['token']
    headers = { "Authorization": "Bearer " + __token }
    response = requests.get(url = "{}{}/{}".format(requestUrl, endpoint, id), headers = headers)

    if response.status_code == 401:
        __token = generate_token()
        headers = { "Authorization": "Bearer " + __token }
        response = requests.get(url = "{}{}/{}".format(requestUrl, endpoint, id), headers = headers)

    return response.json()

def create_userObj(id):
    data = data_fetch('users', id)

    if data['followers']['total'] > 1000000:
        count = f"{round(data['followers']['total'] / 1000000, ndigits=1)}m"
    elif data['followers']['total'] > 1000:
        count = f"{round(data['followers']['total'] / 1000, ndigits=1)}k"
    else:
        count = f"{round(data['followers']['total'])}"
    
    try:
        for image in data['images']:
            if image['height'] == 640:
                sp_image_url = image['url']
                break
            elif image['height'] == 300:
                sp_image_url = image['url']
                break
            else:
                sp_image_url = image['url']
                break
    except:
        sp_image_url = placeholder_image_url

    return {
        'id' : f"{data['id']}",
        'name' : f"{data['display_name']}",
        'followers' : count,
        'image_url' : sp_image_url,
        'uri' : f"{data['uri']}"
    }

def create_playlistObj(id):
    data = data_fetch('playlists', id)

    if data['followers']['total'] > 1000000:
        count = f"{round(data['followers']['total'] / 1000000, ndigits=1)}m"
    elif data['followers']['total'] > 1000:
        count = f"{round(data['followers']['total'] / 1000, ndigits=1)}k"
    else:
        count = f"{round(data['followers']['total'])}"

    try:
        for image in data['images']:
            if image['height'] == 640:
                sp_image_url = image['url']
                break
            elif image['height'] == 300:
                sp_image_url = image['url']
                break
            else:
                sp_image_url = image['url']
                break
    except:
        sp_image_url = placeholder_image_url

    return {
        'id' : f"{data['id']}",
        'is_collaborative' : f"{data['collaborative']}",
        'followers' : count,
        'name' : f"{data['name']}",
        'image_url' : sp_image_url,
        'owner' : f"{data['owner']['display_name']}",
        'owner_id' : f"{data['owner']['id']}",
        'total_tracks' : f"{data['tracks']['total']}",
        'uri' : f"{data['uri']}"
    }

def create_albumObj(id):
    data = data_fetch('albums', id)

    artists_data = []
    for ele in data['artists']:
        artists_data.append({
            'name' : ele['name'],
            'id' : ele['id']
        })
    
    try:
        for image in data['images']:
            if image['height'] == 640:
                sp_image_url = image['url']
                break
            elif image['height'] == 300:
                sp_image_url = image['url']
                break
            else:
                sp_image_url = image['url']
                break
    except:
        sp_image_url = placeholder_image_url

    return {
        'id' : f"{data['id']}",
        'album_type' : f"{data['album_type']}",
        'artists' : artists_data,
        'name' : f"{data['name']}",
        'image_url' : sp_image_url,
        'popularity' : f"{data['popularity']}",
        'release_date' : f"{data['release_date']}",
        'total_tracks' : f"{data['total_tracks']}",
        'label' : f"{data['label']}",
        'uri' : f"{data['uri']}"
    }

def create_artistObj(id):
    data = data_fetch('artists', id)

    if data['followers']['total'] > 1000000:
        count = f"{round(data['followers']['total'] / 1000000, ndigits=1)}m"
    elif data['followers']['total'] > 1000:
        count = f"{round(data['followers']['total'] / 1000, ndigits=1)}k"
    else:
        count = f"{round(data['followers']['total'])}"

    try:
        for image in data['images']:
            if image['height'] == 640:
                sp_image_url = image['url']
                break
            elif image['height'] == 300:
                sp_image_url = image['url']
                break
            else:
                sp_image_url = image['url']
                break
    except:
        sp_image_url = placeholder_image_url

    return {
        "id" : f"{data['id']}",
        "name" : f"{data['name']}",
        "genres" : data['genres'],
        "image_url" : sp_image_url,
        "popularity" : f"{data['popularity']}",
        "followers" : count,
        'uri' : f"{data['uri']}"
    }

def create_trackObj(id):
    data = data_fetch('tracks', id)

    artists_data = []
    for ele in data['artists']:
        artists_data.append({
            'name' : ele['name'],
            'id' : ele['id']
        })

    album_artists_data = []
    for ele in data['album']['artists']:
        album_artists_data.append({
            'name' : ele['name'],
            'id' : ele['id']
        })
    
    try:
        for image in data['album']['images']:
            if image['height'] == 640:
                sp_image_url = image['url']
                break
            elif image['height'] == 300:
                sp_image_url = image['url']
                break
            else:
                sp_image_url = image['url']
                break
    except:
        sp_image_url = placeholder_image_url

    return {
        "id" : f"{data['id']}",
        "title" : f"{data['name']}",
        "artists" : artists_data,
        "album_artists" : album_artists_data,
        "album" : f"{data['album']['name']}",
        "album_id" : f"{data['album']['id']}",
        "image_url" : sp_image_url,
        "track_number" : f"{data['track_number']}",
        "disc_number" : f"{data['disc_number']}",
        "release_date" : f"{data['album']['release_date']}",
        "is_explicit" : f"{data['explicit']}",
        "popularity" : f"{data['popularity']}",
        "preview_url" : f"{data['preview_url']}",
        "duration" : f"{round(data['duration_ms'] / 1000, ndigits=3)}",
        'uri' : f"{data['uri']}"
    }
