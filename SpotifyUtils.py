import json
import subprocess
with open('data.json', 'r') as file:
	data = json.load(file)




def getBitrate(sound_input_path):
    if len(sound_input_path) == 1:
        sound_input_path = sound_input_path[0]
        value = sp.run(
            f'ffprobe -v quiet -select_streams a:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
            shell=True, capture_output=True).stdout.decode().strip()
        type = 'bitrate'
        if value == 'N/A':
            value = sp.run(
            f'ffprobe -v quiet -select_streams a:0 -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
            shell=True, capture_output=True).stdout.decode().strip()
            type = 'samplerate'

        output = {
            type: int(value)
        }
        return output




data = data[0]
if data["type"] == "playlist":
	tracks = []
	for object in data["tracks"]["items"]:
		tracks.append(object["track"]["name"])
	names = []
	for object in data["tracks"]["items"]:
		for subObject in object["track"]["artists"]:
			names.append(subObject["name"])

	if len(tracks)==len(names):
		namesTracks = []
		for i in range(len(tracks)):
			namesTracks.append(f'{names[i]} - {tracks[i]}')
		for combo in namesTracks:
			print(combo)
			subprocess.run(
				f'yt-dlp -P "C:\\Users\\tobia\\Downloads" --cookies-from-browser firefox --default-search "ytsearch" --restrict-filenames --no-mtime -o "%(title)s.%(ext)s" -f ba "{combo} video song"',
				shell=True)

	else:
		for i in names:
			print(i)
		print('\n')
		for i in tracks:
			print(i)
elif data["type"] == "album":
	tracks = []
	for object in data["tracks"]["items"]:
		artists = ''
		for artist in object["artists"]:
			artists += f'{artist['name']}, '
		print(f'{artists[:-2]} - {object['name']}')
		print("Downloading...")
		subprocess.run(	f'yt-dlp -P "C:\\Users\\tobia\\Downloads" --cookies-from-browser firefox --default-search "ytsearch" --restrict-filenames -q --no-mtime -o "%(title)s.%(ext)s" -f ba "{artists[:-2]} - {object['name']} video song"', shell=True, capture_output=False)
		print("Done!\n")