import json
import subprocess
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def getPlaylistTracks(id):
    artists = []
    tracks = []
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="07a2b4bc36b54607872164e17f900989",
                                                   client_secret="",
                                                   redirect_uri="127.0.0.1"))
    playlistData = sp.playlist(id)
    #with open(f"playlist_Data.json", mode="w", encoding="utf-8") as write_file:
    #    json.dump(playlistData, write_file, ensure_ascii=False)
    trackCount = playlistData['tracks']['total']

    print(playlistData['name'])


    for index in range(0, trackCount, 100):
        result = sp.playlist_items(id, offset=index, limit=100, fields="items.track.name, items.track.artists.name")
        for item in result['items']:
            artist_names = ', '.join([artist['name'] for artist in item['track']['artists']])
            artists.append(artist_names)
            tracks.append(item['track']['name'])

        #with open(f"results{index}.json", mode="w", encoding="utf-8") as write_file:
        #    json.dump(result, write_file, ensure_ascii=False)
    output = {
        'artists': artists,
        'tracks': tracks
    }
    return output

def getSavedTracks(saved_numbers):
    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="07a2b4bc36b54607872164e17f900989",
                                                   client_secret="",
                                                   redirect_uri="127.0.0.1",
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


with open('data.json', 'rb') as file:
	data = json.load(file)

outputPath = 'C:\\Users\\tobia\\Downloads'


def getAudioEncoding(file):
    run = subprocess.run(f'ffprobe -select_streams a:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "{file}"', shell=True,capture_output=True)
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


data = data[0]
if data["type"] == "playlist":
	total_tracks = int(data['tracks']['total'])
	tracks_downloaded = 1
	tracks_lost = []

	p = Path(r'C:\Users\tobia\Downloads').glob('**/*')
	files = [x.name for x in p if x.is_file()]

	print(f'{data['name']}\n')

	for _object in data["tracks"]["items"]:
		trackName = _object['track']['name']

		artists = ''
		for artist in _object["track"]["artists"]:
			artists += f'{artist['name']}, '
		artists = artists[:-2]

		print(f'Downloading {artists} - {trackName}... ({tracks_downloaded}/{total_tracks})')

		for file in files:
			if file.find(f'{artists} - {trackName}') != -1:
				print(f"{Bcolors.WARNING}Already downloaded, skipping...{Bcolors.ENDC}\n")
				continue


		downloadData: str = subprocess.run(f'yt-dlp '
				   f'-P "C:\\Users\\tobia\\Downloads" '
				   f'--cookies-from-browser firefox '
				   f'--default-search "ytsearch" '
				   f'--merge-output-format mp4 '
				   f'--restrict-filenames '
				   f'--no-mtime '
				   f'-o "%(title)s.%(ext)s" '
				   f'-f ba '
				   f'"{artists} - {trackName} video song"',
				   shell=True, capture_output=True).stdout.decode(errors='ignore').strip()

		if downloadData.find(f'has already been downloaded') != -1:
			print("Already downloaded, skipping...\n")
			tracks_downloaded += 1
			continue
		if downloadData.find(f'Downloading 0 items') != -1:
			print("No youtube video found! Skipping...\n")
			print(data)
			tracks_lost.append(f'{artists} - {trackName}')
			tracks_downloaded += 1
			continue

		filePath = downloadData[downloadData.find('[download] Destination: ')+24:]
		filePath = filePath[:filePath.find('[download]')].replace('/', '\\').strip()

		if filePath.find('[') != -1:
			print(downloadData)
			input("Press Enter to Exit...")
			exit()


		print(f'Downloaded {filePath[filePath.rfind('\\')+1:]}')


		encoding = getAudioEncoding(filePath)
		if encoding != filePath[filePath.rfind('.') + 1:]:
			subprocess.run(f'ffmpeg '
						   f'-i "{filePath}" '
						   f'"{filePath[:filePath.rfind('.')]}.{encoding}"'
						   , shell=True, capture_output=True)
		subprocess.run(f'del "{filePath}"', shell=True, capture_output=True)
		newFilePath = f'{filePath[:filePath.rfind('.')]}.{encoding}'
		subprocess.run(f'ren "{newFilePath}" "{artists} - {trackName}.{encoding}"', shell=True, capture_output=False)

		print(f'Converted to {artists} - {trackName}.{encoding}')

		print(f'')
		tracks_downloaded += 1

	if total_tracks - len(tracks_lost) == total_tracks:
		if total_tracks > 1:
			print(f'Succesfully downloaded all {total_tracks} tracks!')
		else:
			print(f'Succesfully downloaded 1 track!')
	else:
		print(f'Successfully downloaded ({total_tracks - len(tracks_lost)}/{total_tracks}) tracks\n'
			  f'Failed to download the following:\n')
		for track in tracks_lost:
			print(f'- {track}')

	for _object in data["images"]:
		getImageFromURL(_object['url'], outputPath)



elif data["type"] == "album":
	total_tracks = int(data['total_tracks'])
	tracks_downloaded = 1

	print(f'{data['name']}\n')

	for _object in data["tracks"]["items"]:
		artists = ''
		for artist in _object["artists"]:
			artists += f'{artist['name']}, '
		print(f'{artists[:-2]} - {_object['name']} ({tracks_downloaded}/{total_tracks})')
		print("Downloading...")
		subprocess.run(f'yt-dlp '
					   f'-P "C:\\Users\\tobia\\Downloads" '
					   f'--cookies-from-browser firefox '
					   f'--default-search "ytsearch" '
					   f'--restrict-filenames '
					   f'-q '
					   f'--no-mtime '
					   f'-o "%(title)s.%(ext)s" '
					   f'-f ba "{artists[:-2]} - {_object['name']} video song"',
					   shell=True, capture_output=False)
		print("Done!\n")
		tracks_downloaded += 1

	for _object in data["images"]:
		getImageFromURL(_object['url'], outputPath)
