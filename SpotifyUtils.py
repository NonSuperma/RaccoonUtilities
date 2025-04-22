import json
import subprocess
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

with open('Spotify_info.json', 'r') as f:
    data = json.load(f)

CLIENT_SECRET: str = data['client_secret'].strip()
CLIENT_ID: str = data['client_id'].strip()
REDIRECT_URI: str = data['redirect_uri'].strip()

print(CLIENT_ID, REDIRECT_URI, CLIENT_SECRET)

def getPlaylistTracks(id):
    artists = []
    tracks = []
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI))
    playlistData = sp.playlist(id)

    trackCount = playlistData['tracks']['total']

    print(playlistData['name'])

    for index in range(0, trackCount, 100):
        result = sp.playlist_items(id, offset=index, limit=100, fields="items.track.name, items.track.artists.name")
        for item in result['items']:
            artist_names = ', '.join([artist['name'] for artist in item['track']['artists']])
            artists.append(artist_names)
            tracks.append(item['track']['name'])

    output = {
        'artists': artists,
        'tracks': tracks,
        'total': trackCount
    }
    return output


def getSavedTracks(saved_numbers):
    scope = "user-library-read"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=scope))

    count = 0
    for index in range(0, saved_numbers, 50):

        print(index)
        results = sp.current_user_saved_tracks(limit=50, offset=index)
        for track in results['items']:
            count += 1
            print(track['track']['name'])
        print(f'count: {count}')


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def getAudioEncoding(file):
    run = subprocess.run(f'ffprobe -select_streams a:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "{file}"', shell=True, capture_output=True)
    return run.stdout.decode().strip()


def getImageFromURL(url, output_path):
    import urllib.request
    filename = url[url.rfind('/') + 1:]
    extensions = ['.jpg', '.jpeg', '.png', 'webp']
    if not any(extension in extensions for extension in filename):
        filename += '.png'
    print(f'Getting {filename} from URL...')
    urllib.request.urlretrieve(url, f'{output_path}\\{filename}')
    print('Done!')


def getBitrate(sound_input_path):
    if len(sound_input_path) == 1:
        sound_input_path = sound_input_path[0]
        value = sp.run(
            f'ffprobe '
            f'-v quiet '
            f'-select_streams a:0 '
            f'-show_entries stream=bit_rate '
            f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
            shell=True, capture_output=True).stdout.decode().strip()
        __type = 'bitrate'
        if value == 'N/A':
            value = sp.run(
                f'ffprobe '
                f'-v quiet '
                f'-select_streams a:0 '
                f'-show_entries stream=sample_rate '
                f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
                shell=True, capture_output=True).stdout.decode().strip()
            __type = 'samplerate'

        output = {
            __type: int(value)
        }
        return output


def file_exists_without_extension(base_path):
    directory = os.path.dirname(base_path)
    base_name = os.path.basename(base_path)

    for file in os.listdir(directory or '.'):
        if os.path.splitext(file)[0] == base_name:
            return True
    return False


if __name__ == '__main__':
    #url = 'https://open.spotify.com/playlist/6Fo09y9qtxLyNjK4VWPE9d?si=27db522f9d414d1e'
    #url = "https://open.spotify.com/playlist/6fg55GcV1ZKcsvl8NaGbOe?si=b6f1e564623f45ae"
    url = input('Enter URL: \n').strip()
    OUTPUT_PATH: Path = Path(os.path.join(os.path.expanduser("~"), "Downloads"))
    if url.find('playlist') != -1:
        data = getPlaylistTracks(url)
        total_tracks = int(data['total'])
        tracks_lost = []
        tracks_downloaded = 1
        print(f'Loaded {len(data["artists"])} tracks from playlist\n')

        for index in range(0, len(data["artists"])):
            print(f'Downloading "{data["artists"][index]} - {data["tracks"][index]}" {Bcolors.OKCYAN}({tracks_downloaded}/{total_tracks}){Bcolors.ENDC}')

            if file_exists_without_extension(f'{OUTPUT_PATH}\\{data['artists'][index]} - {data['tracks'][index]}'):
                print(f"{Bcolors.WARNING}Already downloaded, skipping...{Bcolors.ENDC}\n")
                tracks_downloaded += 1
                continue


            downloadData: str = subprocess.run(f'yt-dlp '
                                               f'-P "{OUTPUT_PATH}" '
                                               f'--cookies-from-browser firefox '
                                               f'--default-search "ytsearch" '
                                               f'--merge-output-format mp4 '
                                               f'--no-mtime '
                                               f'--restrict-filenames '
                                               f'-o "%(title)s.%(ext)s" '
                                               f'-f ba '
                                               f'"{data['artists'][index]} - {data['tracks'][index]} video song"',
                                               shell=True, capture_output=True).stdout.decode(errors='ignore').strip()

            if downloadData.find(f'has already been downloaded') != -1:
                print(f"{Bcolors.WARNING}Already downloaded, skipping...{Bcolors.ENDC}\n")
                tracks_downloaded += 1
                continue
            if downloadData.find(f'Downloading 0 items') != -1:
                print(f"{Bcolors.WARNING}No youtube video found! Skipping...{Bcolors.ENDC}\n")
                tracks_lost.append(f'{data['artists'][index]} - {data['tracks'][index]}')
                tracks_downloaded += 1
                continue

            filePath = downloadData[downloadData.find('[download] Destination: ') + 24:]
            filePath: Path = Path(filePath[:filePath.find('[download]')].replace('/', '\\').strip())
            fileName = os.path.basename(filePath)

            print(f'{Bcolors.OKGREEN}Downloaded{Bcolors.ENDC} "{fileName}"')


            encoding = getAudioEncoding(filePath)
            if encoding != str(filePath)[str(filePath).rfind('.') + 1:]:
                convertData = subprocess.run(f'ffmpeg '
                               f'-i "{str(filePath).replace('"', '""')}" '
                               f'"{str(filePath)[:str(filePath).rfind('.')]}.{encoding}"'
                               , shell=True, capture_output=True)
            if convertData.returncode != 0:
                print(f'{Bcolors.FAIL}Something went wrong while converting "{filePath}"\n{Bcolors.ENDC}')
                tracks_downloaded += 1
                continue
            subprocess.run(f'del "{filePath}"', shell=True, capture_output=True)
            newFilePath = f'{str(filePath)[:str(filePath).rfind('.')]}.{encoding}'
            subprocess.run(f'ren "{newFilePath}" "{data['artists'][index]} - {data['tracks'][index]}.{encoding}"', shell=True,
                           capture_output=False)

            print(f'{Bcolors.OKGREEN}Converted{Bcolors.ENDC} to {data['artists'][index]} - {data['tracks'][index]}.{encoding}')

            print(f'')
            tracks_downloaded += 1

        if total_tracks - len(tracks_lost) == total_tracks:
            if total_tracks > 1:
                print(f'{Bcolors.OKBLUE}Succesfully downloaded all {total_tracks} tracks!{Bcolors.ENDC}')
            else:
                print(f'Succesfully downloaded 1 track!')
        else:
            print(f'{Bcolors.OKBLUE}Successfully downloaded ({total_tracks - len(tracks_lost)}/{total_tracks}) tracks\n{Bcolors.ENDC}'
                  f'Failed to download the following:\n')
            for track in tracks_lost:
                print(f'- {track}')



    elif url.find('album') != -1:
        urlType = "album"
