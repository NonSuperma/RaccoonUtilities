import json
import subprocess
import sys
from hashlib import file_digest
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from colorama import init, Fore, Back, Style, just_fix_windows_console
import requests
import os
from tqdm import tqdm
from Raccoon import windowsUtilities
from yt_dlp import YoutubeDL
import re


def getPlaylistData(id) -> dict[str:any]:
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


def getAlbumData(id: str) -> dict[str:str]:
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
    ydl_opts = {"quiet": True, "skip_download": True, "ignore_errors": True, "no_playlist": True, "flat_playlist": True, "cookies_from_browser": True}
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
    TEST = False

    with open('Spotify_info.json', 'r') as f:
        playlistData = json.load(f)

    CLIENT_SECRET: str = playlistData['client_secret'].strip()
    CLIENT_ID: str = playlistData['client_id'].strip()
    REDIRECT_URI: str = playlistData['redirect_uri'].strip()
    PATH_TO_USER = Path(os.path.expanduser("~"))

    #silly
    #url = 'https://open.spotify.com/playlist/6Fo09y9qtxLyNjK4VWPE9d?si=27db522f9d414d1e'
    #house
    #url = "https://open.spotify.com/playlist/6fg55GcV1ZKcsvl8NaGbOe?si=b6f1e564623f45ae"
    #problematic names
    #url = "https://open.spotify.com/playlist/0H7ep5d4XU0aPMCUZIaOwg?si=600b82d4791c451d&pt=c566801a7663c16ad24a7e16e5f33aa4"

    # Get URL
    if not TEST:
        print(f'Enter URL: ')
        print(f'Enter "list" instead of an url to list the artists and tracks of an album/playlist instead.')
        MAIN_URL = input(f'\033[F\033[F\033[11C').strip()
        if MAIN_URL == 'list':
            print(f'\033[F\033[K\n\033[K')
            MAIN_URL = input('\033[F\033[FEnter URL to index: ')
            isInListMode = True
        else:
            print(f'\033[K')
            isInListMode = False
    else:
        choice = input(f'Is in List mode?\n'
                       f'({Fore.LIGHTYELLOW_EX}Enter{Fore.RESET} for {Fore.RED}no{Fore.RESET})\n'
                       f'({Fore.LIGHTYELLOW_EX}anything{Fore.RESET} for {Fore.GREEN}yes{Fore.RESET})\n'
                       f': ')
        if choice == '':
            isInListMode = False
        else:
            isInListMode = True
        MAIN_URL = 'https://open.spotify.com/playlist/4dPBVR1KlbHeWVrKsobEiW?si=9b74502c2671409a&pt=efc74ba1627d8dc354a38d7a11542113'

# Main part

    if 'playlist' in MAIN_URL:

        print(f'Getting the playlist data...')

        playlistData = getPlaylistData(MAIN_URL)
        artistsList = playlistData['artists']
        tracksList = playlistData['tracks']
        totalTracks = playlistData['total']
        playlistName = playlistData['playlistName']

        print(f'{Fore.LIGHTGREEN_EX}Success!{Fore.RESET}')
        print(f'Processing the playlist data...')

        restrictedSymbols = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

        playlistName_safe = playlistName
        for symbol in restrictedSymbols:
            if playlistName_safe.find(symbol) != -1:
                playlistName_safe = playlistName_safe.replace(symbol, '#')
        OUTPUT_PATH = Path.joinpath(PATH_TO_USER, 'Downloads', playlistName_safe)
        os.makedirs(OUTPUT_PATH, exist_ok=True)

        listFilePath: Path = Path.joinpath(OUTPUT_PATH, playlistName_safe).with_suffix('.txt')

        if TEST:
            print(listFilePath)

        with open(listFilePath, 'w', encoding='utf-8') as file:
            file.write(playlistName)
            file.write('\n\n')
            for index in range(playlistData['total']):
                playlistData['artists'][index] = playlistData['artists'][index]
                playlistData['tracks'][index] = playlistData['tracks'][index]
                print(f'{playlistData['artists'][index]} - {playlistData['tracks'][index]}')
                file.write(f'{playlistData['artists'][index]} - {playlistData['tracks'][index]}')
                file.write('\n')

        # split for list mode
        # exits the script if list mode is True
        if isInListMode:
            os.startfile(listFilePath)
            coverURL = getPlaylistCoverURL(MAIN_URL)
            getImageFromURL(coverURL, OUTPUT_PATH)
            sys.exit()

        # Continuation if list mode is False
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

        # Create full track names with artists and track names cuz why not
        fullTrackNamesList = []
        for INDEX in range(totalTracks):
            fullTrackNamesList.append(f'{artistsList[INDEX]} - {tracksList[INDEX]}')

        lostTracks = []
        ytdlpSearchResults = []
        for INDEX in range(totalTracks):
            print(f'Serching for {Fore.LIGHTCYAN_EX}"{fullTrackNamesList[INDEX]}"{Fore.RESET} on YouTube...   ({INDEX + 1}/{totalTracks})')
            ytdlpSearchResults.append(yt_dlp_search_best(fullTrackNamesList[INDEX], 3))
            if ytdlpSearchResults[INDEX] is not None:
                print(f'Found {Fore.CYAN}"{ytdlpSearchResults[INDEX]['title']}{Fore.RESET}"')
                print(f'{Fore.LIGHTYELLOW_EX}Url{Fore.RESET}: {ytdlpSearchResults[INDEX]['url']}')
            else:
                print(f'{Fore.LIGHTRED_EX}Found nothing on YouTube!{Fore.RESET}\n'
                      f'Adding to lost tracks and moving on...')
                lostTracks.append(fullTrackNamesList[INDEX])

        ydl_opts = {
            "quiet": False,
            "f": 'ba'
        }

        with YoutubeDL(ydl_opts) as ytdl:
            for index in range(len(ytdlpSearchResults)):
                ytdl.download(ytdlpSearchResults[index]['url'])

    elif 'album' in MAIN_URL:
        ...
