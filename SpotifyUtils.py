import json
import subprocess
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from colorama import init, Fore, Back, Style
import os

with open('Spotify_info.json', 'r') as f:
    data = json.load(f)

CLIENT_SECRET: str = data['client_secret'].strip()
CLIENT_ID: str = data['client_id'].strip()
REDIRECT_URI: str = data['redirect_uri'].strip()


def getPlaylistTracks(id):
    artists = []
    tracks = []
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI))
    playlistData = sp.playlist(id)
    playlistName = playlistData['name']

    trackCount = playlistData['tracks']['total']

    for _INDEX in range(0, trackCount, 100):
        result = sp.playlist_items(id, offset=_INDEX, limit=100, fields="items.track.name, items.track.artists.name")
        for item in result['items']:
            artist_names = ', '.join([artist['name'] for artist in item['track']['artists']])
            artists.append(artist_names)
            tracks.append(item['track']['name'])

    output = {
        'playlistName': playlistName,
        'artists': artists,
        'tracks': tracks,
        'total': int(trackCount)
    }
    return output


def getAlbumTracks(id: str) -> dict[str:str]:
    artists = []
    tracks = []
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI))
    albumData = sp.album(id)
    albumName = albumData['name']
    albumTrackCount = albumData['tracks']['total']

    for _INDEX in range(0, albumTrackCount, 100):
        result = sp.album_tracks(id, offset=_INDEX, limit=50)
        for item in result['items']:
            artist_names = ', '.join([artist['name'] for artist in item['artists']])
            artists.append(artist_names)
            tracks.append(item['name'])
    output = {
        'albumName': albumName,
        'artists': artists,
        'tracks': tracks,
        'total': albumTrackCount
    }
    return output


def getSavedTracks(saved_numbers):
    scope = "user-library-read"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=scope))

    count = 0
    for _INDEX in range(0, saved_numbers, 50):

        print(_INDEX)
        results = sp.current_user_saved_tracks(limit=50, offset=_INDEX)
        for _track in results['items']:
            count += 1
            print(_track['track']['name'])
        print(f'count: {count}')


def getAudioEncoding(file):
    run = subprocess.run(
        f'ffprobe -select_streams a:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "{file}"',
        shell=True, capture_output=True)
    return run.stdout.decode().strip()


def getImageFromURL(_url, output_path):
    import urllib.request
    filename = _url[_url.rfind('/') + 1:]
    extensions = ['.jpg', '.jpeg', '.png', 'webp']
    if not any(extension in extensions for extension in filename):
        filename += '.png'
    print(f'Getting {filename} from URL...')
    urllib.request.urlretrieve(_url, f'{output_path}\\{filename}')
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
    #silly
    #url = 'https://open.spotify.com/playlist/6Fo09y9qtxLyNjK4VWPE9d?si=27db522f9d414d1e'
    #house
    #url = "https://open.spotify.com/playlist/6fg55GcV1ZKcsvl8NaGbOe?si=b6f1e564623f45ae"
    #problematic names
    #url = "https://open.spotify.com/playlist/0H7ep5d4XU0aPMCUZIaOwg?si=600b82d4791c451d&pt=c566801a7663c16ad24a7e16e5f33aa4"
    url = input('Enter URL: \n').strip()
    USER_PATH: Path = Path(os.path.expanduser("~"))

    if url.find('playlist') != -1:
        data = getPlaylistTracks(url)
        playlistName = data['playlistName']
        OUTPUT_PATH = Path.joinpath(USER_PATH, 'Downloads', playlistName)
        print(OUTPUT_PATH)
        os.makedirs(Path.joinpath(USER_PATH, 'Downloads', playlistName), exist_ok=True)

        for index in range(len(data)):
            data['artists'][index] = data['artists'][index].replace('"', '')
            data['tracks'][index] = data['tracks'][index].replace('"', '')
            #print(f'{data['artists'][INDEX]} - {data['tracks'][INDEX]}')

        total_tracks = int(data['total'])
        tracks_lost = []
        tracks_downloaded = 1
        print(f'Loaded {len(data["artists"])} tracks from playlist\n')

        for INDEX in range(0, total_tracks):
            print(
                f'{Fore.CYAN}Downloading{Fore.RESET} "{artists} - {data["tracks"][INDEX]}" {Fore.LIGHTCYAN_EX}({tracks_downloaded}/{total_tracks}){Fore.RESET}')

            try:
                if file_exists_without_extension(f'{OUTPUT_PATH}\\{data['artists'][INDEX]} - {data['tracks'][INDEX]}'):
                    print(f"{Fore.YELLOW}Already downloaded, skipping...{Fore.RESET}\n")
                    tracks_downloaded += 1
                    continue
            except (Exception,):
                print(f"{Fore.YELLOW}Something went wrong! {Fore.RESET}\n")
                tracks_lost.append(f'{data['artists'][INDEX]} - {data['tracks'][INDEX]}')
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
                                               f'"{data['artists'][INDEX]} - {data['tracks'][INDEX]} video song"',
                                               shell=True, capture_output=True).stdout.decode(errors='ignore').strip()

            if downloadData.find(f'has already been downloaded') != -1:
                print(f"{Fore.RED}Already downloaded, skipping...{Fore.RESET}\n")
                tracks_downloaded += 1
                continue
            if downloadData.find(f'Downloading 0 items') != -1:
                print(f"{Fore.RED}No youtube video found! Skipping...{Fore.RESET}\n")
                tracks_lost.append(f'{data['artists'][INDEX]} - {data['tracks'][INDEX]}')
                tracks_downloaded += 1
                continue

            filePath: str = downloadData[downloadData.find('[download] Destination: ') + 24:]
            filePath: Path = Path(filePath[:filePath.find('[download]')].replace('/', '\\').strip())
            fileName = os.path.basename(filePath)

            print(f'{Fore.GREEN}Downloaded{Fore.RESET} "{fileName}"')

            encoding = getAudioEncoding(filePath)
            if encoding != str(filePath)[str(filePath).rfind('.') + 1:]:
                convertData = subprocess.run(f'ffmpeg '
                                             f'-y '
                                             f'-i '
                                             f'"{str(filePath).replace('"', '""')}" '
                                             f'"{str(filePath)[:str(filePath).rfind('.')]}.{encoding}"',
                                             shell=True, capture_output=True)
                if convertData.returncode != 0:
                    print(f'{Fore.YELLOW}Something went wrong while converting "{filePath}"\n{Fore.RESET}')
                    tracks_downloaded += 1
                    continue
                subprocess.run(f'del '
                               f'"{filePath}"',
                               shell=True, capture_output=True)
                newFilePath: Path = Path(f'{str(filePath)[:str(filePath).rfind('.')]}.{encoding}')
                subprocess.run(f'ren '
                               f'"{newFilePath}" '
                               f'"{data['artists'][INDEX]} - {data['tracks'][INDEX]}.{encoding}"',
                               shell=True)
            else:
                print(f'{Fore.GREEN}Downloaded track already has the right container!{Fore.RESET}')

            print(
                f'{Fore.GREEN}Converted{Fore.RESET} to "{data['artists'][INDEX]} - {data['tracks'][INDEX]}.{encoding}"')

            print(f'')
            tracks_downloaded += 1

        if total_tracks - len(tracks_lost) == total_tracks:
            if total_tracks > 1:
                print(f'{Fore.BLUE}Succesfully downloaded all {total_tracks} tracks!{Fore.RESET}')
            else:
                print(f'Succesfully downloaded 1 track!')
        else:
            print(
                f'{Fore.BLUE}Successfully downloaded ({total_tracks - len(tracks_lost)}/{total_tracks}) tracks\n{Fore.RESET}'
                f'Failed to download the following:\n')
            for track in tracks_lost:
                print(f'- {track}')

    elif url.find('album') != -1:
        data = getAlbumTracks(url)

        albumName = data['albumName']
        OUTPUT_PATH = Path.joinpath(USER_PATH, 'Downloads', albumName)
        print(OUTPUT_PATH)
        os.makedirs(Path.joinpath(USER_PATH, 'Downloads', albumName), exist_ok=True)

        for index in range(len(data)):
            data['artists'][index] = data['artists'][index].replace('"', '')
            data['tracks'][index] = data['tracks'][index].replace('"', '')
            # print(f'{data['artists'][INDEX]} - {data['tracks'][INDEX]}')

        total_tracks = data['total']
        tracks_lost = []
        tracks_downloaded = 1

        print(f'{Fore.GREEN}Loaded {data['total']} tracks from album; "{albumName}"\n{Fore.RESET}')

        for index in range(0, total_tracks):
            artists = data["artists"][index]
            track = data["tracks"][index]
            

            print(
                f'{Fore.CYAN}Downloading{Fore.RESET} "{artists} - {data["tracks"][index]}" {Fore.LIGHTCYAN_EX}({tracks_downloaded}/{total_tracks}){Fore.RESET}')

            try:
                if file_exists_without_extension(f'{OUTPUT_PATH}\\{artists} - {track}'):
                    print(f"{Fore.YELLOW}Already downloaded, skipping...{Fore.RESET}\n")
                    tracks_downloaded += 1
                    continue
            except (Exception,):
                print(f"{Fore.RED}Something went wrong! {Fore.RESET}\n")
                tracks_lost.append(f'{artists} - {track}')
                tracks_downloaded += 1
                continue

            downloadData = subprocess.run(f'yt-dlp '
                                               f'-P "{OUTPUT_PATH}" '
                                               f'--cookies-from-browser firefox '
                                               f'--default-search "ytsearch" '
                                               f'--merge-output-format mp4 '
                                               f'--no-mtime '
                                               f'--restrict-filenames '
                                               f'-o "%(title)s.%(ext)s" '
                                               f'-f ba '
                                               f'"{artists} - {track} video song"',
                                         shell=True, capture_output=True).stdout.decode(errors='ignore').strip()
            if downloadData.find(f'has already been downloaded') != -1:
                print(f"{Fore.RED}Already downloaded, skipping...{Fore.RESET}\n")
                tracks_downloaded += 1
                continue
            if downloadData.find(f'Downloading 0 items') != -1:
                print(f"{Fore.RED}No youtube video found! Skipping...{Fore.RESET}\n")
                tracks_lost.append(f'{artists} - {track}')
                tracks_downloaded += 1
                continue

            filePath: str = downloadData[downloadData.find('[download] Destination: ') + 24:]
            filePath: Path = Path(filePath[:filePath.find('[download]')].replace('/', '\\').strip())
            fileName = os.path.basename(filePath)

            print(f'{Fore.GREEN}Downloaded{Fore.RESET} "{fileName}"')

            encoding = getAudioEncoding(filePath)
            if encoding != str(filePath)[str(filePath).rfind('.') + 1:]:
                convertData = subprocess.run(f'ffmpeg '
                                             f'-y '
                                             f'-i '
                                             f'"{str(filePath).replace('"', '""')}" '
                                             f'"{str(filePath)[:str(filePath).rfind('.')]}.{encoding}"',
                                             shell=True, capture_output=True)
                if convertData.returncode != 0:
                    print(f'{Fore.YELLOW}Something went wrong while converting "{filePath}"\n{Fore.RESET}')
                    tracks_downloaded += 1
                    continue
                subprocess.run(f'del '
                               f'"{filePath}"',
                               shell=True, capture_output=True)
                newFilePath: Path = Path(f'{str(filePath)[:str(filePath).rfind('.')]}.{encoding}')
                subprocess.run(f'ren '
                               f'"{newFilePath}" '
                               f'"{artists} - {track}.{encoding}"',
                               shell=True)
            else:
                print(f'{Fore.GREEN}Downloaded track already has the right container!{Fore.RESET}')

            print(
                f'{Fore.GREEN}Converted{Fore.RESET} to "{artists} - {track}.{encoding}"')

            print(f'')
            tracks_downloaded += 1

        if total_tracks - len(tracks_lost) == total_tracks:
            if total_tracks > 1:
                print(f'{Fore.BLUE}Succesfully downloaded all {total_tracks} tracks!{Fore.RESET}')
            else:
                print(f'Succesfully downloaded 1 track!')
        else:
            print(
                f'{Fore.BLUE}Successfully downloaded ({total_tracks - len(tracks_lost)}/{total_tracks}) tracks\n{Fore.RESET}'
                f'Failed to download the following:\n')
            for track in tracks_lost:
                print(f'- {track}')
