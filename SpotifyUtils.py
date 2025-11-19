import json
import subprocess
from hashlib import file_digest
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from colorama import init, Fore, Back, Style, just_fix_windows_console
import requests
import os
from tqdm import tqdm
from Raccoon import windowsUtilities

with open('Spotify_info.json', 'r') as f:
    data = json.load(f)

CLIENT_SECRET: str = data['client_secret'].strip()
CLIENT_ID: str = data['client_id'].strip()
REDIRECT_URI: str = data['redirect_uri'].strip()


def getPlaylistTracks(id) -> dict[str:any]:
    artistNamesList = []
    trackNamesList = []
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
            artistNamesList.append(artist_names)
            trackNamesList.append(item['track']['name'])

    output = {
        'playlistName': playlistName,
        'artists': artistNamesList,
        'tracks': trackNamesList,
        'total': trackCount
    }
    return output


def getPlaylistCoverURL(id: str) -> str:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI))
    playlistData = sp.playlist(id)
    return playlistData['images'][0]['url']


def getAlbumTracks(id: str) -> dict[str:str]:
    artistNameList = []
    trackNamesList = []
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
            artistNameList.append(artist_names)
            trackNamesList.append(item['name'])
    output = {
        'albumName': albumName,
        'artists': artistNameList,
        'tracks': trackNamesList,
        'total': albumTrackCount
    }
    return output


def getAlbumCoverURL(id: str) -> str:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI))
    albumData = sp.album(id)
    return albumData['images'][0]['url']


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


def getAudioEncoding(_file):
    run = subprocess.run(
        f'ffprobe -select_streams a:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "{_file}"',
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


def yt_dlp_search_best(query, n_results=4):
    ydl_opts = {"quiet": True, "skip_download": True, "ignore_errors": True, "no_playlist": True, "flat_playlist": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{n_results}:{query}", download=False)
        entries = info.get("entries", [])

        def getScore(entry):
            title = entry.get("title", "")
            channel = entry.get("uploader", "") or entry.get("creator", "")
            score = 0
            qnorm = re.sub(r'\W+', '', query).lower()
            if re.sub(r'\W+', '', title).lower() == qnorm:
                score += 80
            if re.search(r'\bofficial\b|\bofficial video\b|vevo', title, re.I):
                score += 20
            if re.search(re.escape(query), channel, re.I):
                score += 100
            if re.search(r'remix|sped up|slowed|slowed down|reverb|reverbed|', title) and not re.search(r'remix|sped up|slowed|slowed down|reverb|reverbed|', query):
                score -= 90
            score += min(int(entry.get("view_count") or 0) // 1000000, 10)
            return score

        if not entries:
            return None
        best = max(entries, key=getScore)
        return {
            "title": best.get("title"),
            "uploader": best.get("uploader"),
            "url": best.get("webpage_url") or f"https://www.youtube.com/watch?v={best.get('id')}",
            "view_count": best.get("view_count")
        }


def file_exists_without_extension(file_path: Path) -> bool:
    fileDirectory = file_path.parent
    pureFileName = file_path.stem

    return any(file.is_file() and file.stem == pureFileName for file in fileDirectory.iterdir())


if __name__ == '__main__':
    test = True
    #silly
    #url = 'https://open.spotify.com/playlist/6Fo09y9qtxLyNjK4VWPE9d?si=27db522f9d414d1e'
    #house
    #url = "https://open.spotify.com/playlist/6fg55GcV1ZKcsvl8NaGbOe?si=b6f1e564623f45ae"
    #problematic names
    #url = "https://open.spotify.com/playlist/0H7ep5d4XU0aPMCUZIaOwg?si=600b82d4791c451d&pt=c566801a7663c16ad24a7e16e5f33aa4"
    if not test:
        print(f'Enter URL: ')
        print(f'Enter "list" instead of an url to list the artists and tracks of an album/playlist instead.')
        url = input(f'\033[F\033[F\033[11C').strip()
        if url == 'list':
            print(f'\033[F\033[K\n\033[K')
            url = input('\033[F\033[FEnter URL to index: ')
            isInListMode = True
        else:
            print(f'\033[K')
            isInListMode = False
    else:
        choice = input('Is in List mode? (y/n): ')
        if choice == 'y':
            isInListMode = True
        else:
            isInListMode = False
        url = 'https://open.spotify.com/playlist/6Fo09y9qtxLyNjK4VWPE9d?si=27db522f9d414d1e'

    USER_PATH: Path = Path(os.path.expanduser("~"))

    if not isInListMode:
        # Check for yt-dlp and download it if not present
        def yt_dlpFileCheck():
            script_dir = Path(__file__).resolve().parent
            if windowsUtilities.file_is_in_dir('yt-dlp.exe', script_dir):
                print(f'{Fore.GREEN}Found yt-dlp!{Fore.RESET}')
            else:

                url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
                fileName = 'yt-dlp.exe'
                savePath = Path.joinpath(script_dir, fileName)

                try:
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                except (requests.exceptions.HTTPError, requests.exceptions.RequestException):
                    input(f'{Fore.RED}WARNING{Fore.RESET}\n'
                          f'Error while trying to automatically download yt-dlp. You need to download yt-dlp.exe to the directory the program was ran from before continuing.\n\n'
                          f'If yt-dlp.exe is in the correct place, press {Fore.GREEN}ENTER{Fore.RESET}')
                else:
                    total_size = int(response.headers.get("content-length", 0))
                    chunk_size = 8192

                    with open(savePath, "wb") as f, tqdm(
                            desc=fileName,
                            total=total_size,
                            unit="iB",
                            unit_scale=True,
                            unit_divisor=1024,
                    ) as bar:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            size = f.write(chunk)
                            bar.update(size)
        yt_dlpFileCheck()

        if url.find('playlist') != -1:
            data = getPlaylistTracks(url)
            artistsList = data['artists']
            tracksList = data['tracks']
            totalTracks = data['total']
            
            playlistName = data['playlistName']
            restrictedSymbols = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            playlistName_safe = playlistName
            for symbol in restrictedSymbols:
                if playlistName_safe.find(symbol) != -1:
                    playlistName_safe = playlistName_safe.replace(symbol, '#')
                    
            artistsList_safe = artistsList
            tracksList_safe = tracksList
            for index in range(totalTracks):
                for symbol in restrictedSymbols:
                    if artistsList_safe[index].find(symbol) != -1:
                        artistsList_safe[index] = artistsList_safe[index].replace(symbol, '#')
                    if tracksList_safe[index].find(symbol) != -1:
                        tracksList_safe[index] = tracksList_safe[index].replace(symbol, '#')
                    
            if playlistName_safe != playlistName:
                playlistNameWasAltered = True
            else:
                playlistNameWasAltered = False
            
            if artistsList_safe != artistsList:
                artistsListWasAltered = True
            else:
                artistsListWasAltered = False
            
            if tracksList_safe != tracksList:
                tracksListWasAltered = True
            else:
                tracksListWasAltered = False

            OUTPUT_PATH = Path.joinpath(USER_PATH, 'Downloads', playlistName_safe)
            print(f'Downloading everything to {Fore.LIGHTYELLOW_EX}{OUTPUT_PATH}{Fore.RESET}')
            os.makedirs(OUTPUT_PATH, exist_ok=True)

        
            tracks_lost = []
            tracks_downloaded = 1
            print(f'Loaded {totalTracks} tracks from playlist\n')

            for INDEX in range(totalTracks):
                trackFullName = f'{data['artists'][INDEX]} - {data['tracks'][INDEX]}'
                trackStemPath = Path.joinpath(OUTPUT_PATH, trackFullName)
                print(
                    f'{Fore.CYAN}Downloading{Fore.RESET} "{trackFullName}" {Fore.LIGHTCYAN_EX}({tracks_downloaded}/{totalTracks}){Fore.RESET}')

                try:
                    if file_exists_without_extension(trackStemPath):
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
                                                   f'"{data['artists'][INDEX]} - {data['tracks'][INDEX]} official video audio"',
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
                print(encoding)
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

            if totalTracks - len(tracks_lost) == totalTracks:
                if totalTracks > 1:
                    print(f'{Fore.BLUE}Succesfully downloaded all {totalTracks} tracks!{Fore.RESET}')
                else:
                    print(f'Succesfully downloaded 1 track!')
            else:
                print(
                    f'{Fore.BLUE}Successfully downloaded ({totalTracks - len(tracks_lost)}/{totalTracks}) tracks\n{Fore.RESET}'
                    f'Failed to download the following:\n')
                for track in tracks_lost:
                    print(f'- {track}')

            coverURL = getPlaylistCoverURL(url)
            getImageFromURL(coverURL, OUTPUT_PATH)

        elif url.find('album') != -1:
            data = getAlbumTracks(url)

            albumName = data['albumName'].replace('?', '_')

            OUTPUT_PATH = Path.joinpath(USER_PATH, 'Downloads', albumName)
            print(OUTPUT_PATH)
            os.makedirs(Path.joinpath(USER_PATH, 'Downloads', albumName), exist_ok=True)

            for index in range(len(data['tracks'])):
                data['artists'][index] = data['artists'][index].replace('"', '')
                data['tracks'][index] = data['tracks'][index].replace('"', '')
                # print(f'{data['artists'][INDEX]} - {data['tracks'][INDEX]}')

            totalTracks = data['total']
            tracks_lost = []
            tracks_downloaded = 1

            print(f'{Fore.GREEN}Loaded {data['total']} tracks from album; "{albumName}"\n{Fore.RESET}')

            for index in range(0, totalTracks):
                artists = data["artists"][index]
                track = data["tracks"][index]
                trackFullName = f'{artists} - {track}'
                trackStemPath = Path.joinpath(OUTPUT_PATH, trackFullName)
                trackPaths = []

                print(
                    f'{Fore.CYAN}Downloading{Fore.RESET} "{artists} - {data["tracks"][index]}" {Fore.LIGHTCYAN_EX}({tracks_downloaded}/{totalTracks}){Fore.RESET}')

                try:
                    if file_exists_without_extension(trackStemPath):
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
                    trackPaths.append(Path(f'{artists} - {track}.{encoding}'))
                else:
                    print(f'{Fore.GREEN}Downloaded track already has the right container!{Fore.RESET}')

                print(
                    f'{Fore.GREEN}Converted{Fore.RESET} to "{artists} - {track}.{encoding}"')

                print(f'')
                tracks_downloaded += 1

            if totalTracks - len(tracks_lost) == totalTracks:
                if totalTracks > 1:
                    print(f'{Fore.BLUE}Succesfully downloaded all {totalTracks} tracks!{Fore.RESET}')
                else:
                    print(f'Succesfully downloaded 1 track!')
            else:
                print(
                    f'{Fore.BLUE}Successfully downloaded ({totalTracks - len(tracks_lost)}/{totalTracks}) tracks\n{Fore.RESET}'
                    f'Failed to download the following:\n')
                for track in tracks_lost:
                    print(f'- {track}')
    else:

        if url.find('playlist') != -1:
            data = getPlaylistTracks(url)
            playlistName = data['playlistName']
            restrictedSymbols = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            playlistName_safe = playlistName
            for symbol in restrictedSymbols:
                if playlistName_safe.find(symbol) != -1:
                    playlistName_safe = playlistName_safe.replace(symbol, '#')

            OUTPUT_PATH = Path.joinpath(USER_PATH, 'Downloads', playlistName_safe)

            os.makedirs(OUTPUT_PATH, exist_ok=True)


            outputFilePath: Path = Path.joinpath(OUTPUT_PATH, playlistName_safe).with_suffix('.txt')
            print(outputFilePath)
            with open(outputFilePath, 'w', encoding='utf-8') as file:
                file.write(playlistName)
                file.write('\n\n')
                for index in range(data['total']):
                    data['artists'][index] = data['artists'][index]
                    data['tracks'][index] = data['tracks'][index]
                    print(f'{data['artists'][index]} - {data['tracks'][index]}')
                    file.write(f'{data['artists'][index]} - {data['tracks'][index]}')
                    file.write('\n')

            os.startfile(outputFilePath)
            coverURL = getPlaylistCoverURL(url)
            getImageFromURL(coverURL, OUTPUT_PATH)

        elif url.find('album') != -1:
            data = getAlbumTracks(url)

            albumName: str = data['albumName']
            OUTPUT_PATH = Path.joinpath(USER_PATH, 'Downloads', albumName)
            os.makedirs(OUTPUT_PATH, exist_ok=True)

            restrictedSymbols = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            albumName_safe = albumName
            for symbol in restrictedSymbols:
                if albumName_safe.find(symbol) != -1:
                    albumName_safe.replace(symbol, '#')

            outputFilePath: Path = Path.joinpath(OUTPUT_PATH, albumName_safe).with_suffix('.txt')
            print(outputFilePath)
            with open(outputFilePath, 'w', encoding='utf-8') as file:
                file.write(albumName)
                file.write('\n\n')
                for index in range(data['total']):
                    data['artists'][index] = data['artists'][index]
                    data['tracks'][index] = data['tracks'][index]
                    print(f'{data['artists'][index]} - {data['tracks'][index]}')
                    file.write(f'{data['artists'][index]} - {data['tracks'][index]}')
                    file.write('\n')

            os.startfile(outputFilePath)
            getImageFromURL(getAlbumCoverURL(url), OUTPUT_PATH)
