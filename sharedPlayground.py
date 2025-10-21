from itertools import count
from os.path import exists
from Raccoon.windowsUtilities import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.errors import *
import validators
import sys
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
import pyperclip

mp3 = 'mp3'
strip = 'strip'
data = 'data'
concad = 'concad'
flactomp3 = 'flactomp3'
mp3tomp4 = 'mp3tomp4'
xtoflac = 'xtoflac'
mode = xtoflac

if mode == xtoflac:
	audioPath = winFilePath('audio')
	outputPath = audioPath.with_suffix('.flac')
	outputName = outputPath.name

	subprocess.run(f'ffmpeg '
				   f'-i "{audioPath}" '
				   f'-map 0 '
				   f'-c:a flac '
				   f'-sample_fmt s16 '
				   f'-ar 44100 '
				   f'-map_metadata 0 -id3v2_version 3 '
				   f'-c:v copy '
				   f'"{outputPath}"')

if mode == 4:
	videoPath = winFilePath('video')
	audioPath = winFilePath('audio', filetypes='audio')
	outputPath = videoPath.parent.joinpath('output.mp4')
	ffmpegOutput = subprocess.run(
		f'ffmpeg '
		f'-loglevel fatal '
		f'-y '
		f'-i "{videoPath}" '
		f'-i "{audioPath}" '
		f'-map 0:v:0 -map 1:a:0 '
		f'-c:v copy -c:a copy '
		f'-movflags +faststart '
		f'-shortest '
		f'"{outputPath}"'
	)

if mode == 3:
	coverPath = winFilePath()
	audioPath = winFilePath('audio')
	subprocess.run(
		f'ffmpeg '
		f'-loglevel fatal '
		f'-y '
		f'-loop 1 '
		f'-framerate 1 '
		f'-i "{coverPath}" '
		f'-i "{audioPath}" '
		f'-map 0:v:0 -map 1:a:0 '
		f'-c:v libx264 -crf 30 -tune stillimage '
		f'-c:a copy '
		f'-shortest '
		f'-movflags +faststart '
		f'-map_metadata 1 '
		f'-id3v2_version 3 -write_id3v1 1 '
		f'-vf "format=yuv420p" '
		f'-r 1 '
		f'"{audioPath.with_suffix(f'.mp4')}"'
	)

if mode == 2:
	filePath = winFilePath(filetypes='audio')
	subprocess.run(f'ffmpeg '
				   f'-y '
				   f'-i "{filePath}" '
				   f'-af "rubberband=tempo=0.55, aecho=0.8:0.9:1000:0.3, lowpass=f=8000" '
				   f'"{filePath.parent.joinpath(str(filePath.stem) + ' (slowed)' + str(filePath.suffix))}')
if mode == 1:
	filePath = winFilePath(filetypes='audio')
	subprocess.run(f'ffmpeg '
				   f'-y '
				   f'-i "{filePath}" '
				   f'-af "rubberband=tempo=0.633" '
				   f'"{filePath.parent.joinpath(str(filePath.stem) + ' (slowed)' + str(filePath.suffix))}')

if mode == 40:
	mode = Path(
		'E:\\Other\\Music\\Tyler, The Creator\\CHROMAKOPIA [24-bit 44.1 kHz] [Full Album]\\Tyler, The Creator - CHROMAKOPIA - 01 - St. Chroma.flac')
	print(mode.parent)
if mode == mp3tomp4:
	coverPath = winFilePath('cover', 'image')
	mp3FilesPaths = winFilesPath('audio', 'audio')

	albumCoverConverted = False
	userChoice = input(f'Scale album cover to 1000x1000? Enter=No, y=Yes\n'
					   f': ')
	if userChoice == 'y':
		albumCoverConverted = True
		print(f'Converting cover...')
		coverPath = ScaleImage(coverPath, '1000:1000', remove_old=False)
		print(f'Done!')

	mp3FilesPaths_safe = []
	for index in range(len(mp3FilesPaths)):
		mp3FilesPaths_safe.append(Path(str(mp3FilesPaths[index]).replace("'", "")))
		mp3FilesPaths[index].rename(mp3FilesPaths_safe[index])
		print(f'Converting "{mp3FilesPaths[index]}" to .mp4...')
		subprocess.run(
			f'ffmpeg '
			f'-loglevel fatal '
			f'-y '
			f'-loop 1 '
			f'-framerate 1 '
			f'-i "{coverPath}" '
			f'-i "{mp3FilesPaths_safe[index]}" '
			f'-map 0:v:0 -map 1:a:0 '
			f'-c:v libx264 -crf 30 -tune stillimage '
			f'-c:a copy '
			f'-shortest '
			f'-movflags +faststart '
			f'-map_metadata 1 '
			f'-id3v2_version 3 -write_id3v1 1 '
			f'-vf "format=yuv420p" '
			f'-r 1 '
			f'"{Path.joinpath(mp3FilesPaths_safe[index].with_suffix(".mp4"))}"',
		)
		print('Done!')
		mp3FilesPaths_safe[index].rename(mp3FilesPaths[index])
if mode == flactomp3:
	flacFilePaths = winFilesPath()
	flacFilePaths_safe = []
	for index in range(len(flacFilePaths)):
		flacFilePaths_safe.append(Path(str(flacFilePaths[index]).replace("'", "")))
		flacFilePaths[index].rename(flacFilePaths_safe[index])

	folderPath = flacFilePaths[0].parent
	folderName = folderPath.name
	with open(f'{folderPath}\\temp_audio_list.txt', 'w+', encoding='utf-8') as f:
		for file in flacFilePaths_safe:
			f.write(f"file '{str(file).replace("'", "")}'\n")

	print(f'Concading "{folderName}.flac"...')
	ffmpegOutput_concad = subprocess.run(f'ffmpeg '
										 f'-y '
										 f'-loglevel fatal '
										 f'-f concat '
										 f'-safe 0 '
										 f'-i "{folderPath}\\temp_audio_list.txt" '
										 f'-c copy '
										 f'"{folderPath}\\{folderName}.flac"',
										 capture_output=False)
	print(f'Done!\n')
	Path(f'{folderPath}\\temp_audio_list.txt').unlink()
	os.makedirs(Path.joinpath(folderPath, 'mp3'), exist_ok=True)
	print(f'Encoding to mp3 320kbps...')
	subprocess.run(f'ffmpeg '
				   f'-y '
				   f'-loglevel fatal '
				   f'-i "{folderPath}\\{folderName}.flac" '
				   f'-map_metadata 0 '
				   f'-id3v2_version 3 -write_id3v1 1 '
				   f'-c:a libmp3lame -b:a 320k '
				   f'"{folderPath}\\mp3\\{str(folderName.replace('[16-bit 44.1kHz]', '').replace('[24-bit 44.1 kHz]', '')) + ' [320kbps]'}.mp3"'
				   )
	for index in range(len(flacFilePaths)):
		flacFilePaths_safe[index].rename(flacFilePaths[index])
if mode == concad:
	flacFilePaths = winFilesPath()
	folderPath = flacFilePaths[0].parent
	folderName = folderPath.name
	with open(f'{folderPath}\\temp_audio_list.txt', 'w') as f:
		for file in flacFilePaths:
			f.write(f"file '{file}'\n")
	print(folderPath)
	print(f'Concading "{folderName}.flac"...')
	ffmpegOutput_concad = subprocess.run(f'ffmpeg '
										 f'-y '
										 #f'-loglevel fatal '
										 f'-f concat '
										 f'-safe 0 '
										 f'-i "temp_audio_list.txt" '
										 f'"{folderPath}\\{folderName}.txt"',
										 capture_output=False)
	print(f'Done!\n')
	Path(f'{folderPath}\\temp_audio_list.txt').unlink()
if mode == mp3:
	for songPath in winFilesPath():
		print(f'Processing {songPath}...')
		folderPath = songPath.parent
		outputPath = Path.joinpath(folderPath, 'mp3', songPath.name)
		os.makedirs(Path.joinpath(folderPath, 'mp3'), exist_ok=True)
		subprocess.run(f'ffmpeg '
					   f'-y '
					   f'-loglevel fatal '
					   f'-i "{songPath}" '
					   f'-map_metadata 0 '
					   f'-id3v2_version 3 -write_id3v1 1 '
					   f'-c:a libmp3lame -b:a 320k '
					   f'"{outputPath.with_suffix('.mp3')}"'
					   )
		print(f'{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}')
if mode == data:
	file = winFilePath()

	with open('data.json', 'w') as f:
		f.write(json.dumps(get_audio_data(file), indent=4))
if mode == 25:
	file = Path('E:\\Other\\Music\\Acid_Bath\\Paegan Terrorism Tactics')
	print(file.joinpath('balls'))
if mode == 24:
	file = Path('E:\\Other\\Music\\Acid_Bath\\Paegan Terrorism Tactics\\Crazy_tick_removal_Or_fake.webm')
	print(file.suffix)
if mode == strip:
	files = winFilesPath()
	for file in files:
		print(f'Processing {file}...')
		fileData = get_audio_data(file)
		fileName = file.name
		fileName_safe = fileName.replace("'", '')
		filePath_safe = file.parent.joinpath(fileName_safe)
		filePath_suffixed = filePath_safe.with_suffix(f'.{fileData['streams']['codec_name']}')
		file.rename(fileName_safe)

		output = subprocess.run(f'ffmpeg '
					   f'-loglevel fatal '
					   f'-i "{filePath_safe}" '
					   f'-c:a copy '
					   f'-map_metadata 0 '
					   f'-id3v2_version 3 -write_id3v1 1 '
					   f'"{filePath_suffixed}"', capture_output=True)
		if output.returncode == 0:
			...
			#file.unlink(missing_ok=True)
		else:
			print(output.stderr)
		filePath_suffixed.rename(file)

if mode == 22:
	pathToFile = Path('E:\\Other\\Music\\!!Nicotine+ Downloads\\Femtanyl - WORLDWID3 (feat. zombAe).flac')
	ffprobeOutput = subprocess.run(
		f'ffprobe '
		f'-select_streams a:0 '
		f'-show_entries format=format_name,duration,size,bit_rate:stream=codec_name,sample_rate,channels,bit_rate:format_tags:stream_tags -print_format json "{pathToFile}"',
		shell=True, capture_output=True)
	ffprobeOutputJson = json.loads(ffprobeOutput.stdout)
	results = {}
	results.update({'streams': ffprobeOutputJson["streams"][0]})
	results.update({'format': ffprobeOutputJson['format']})
	results.update({'tags': ffprobeOutputJson['format']['tags']})
	results['format'].pop('tags')


	def convert_numeric_keys_values(d):
		new_dict = {}
		for key, value in d.items():
			if isinstance(key, str):
				try:
					if key.isdigit():
						key = int(key)
					else:
						key = float(key)
				except ValueError:
					pass

			if isinstance(value, dict):
				value = convert_numeric_keys(value)

			elif isinstance(value, str):
				try:
					if value.isdigit():
						value = int(value)
					else:
						value = float(value)
				except ValueError:
					pass

			new_dict[key] = value
		return new_dict


	results = convert_numeric_keys_values(results)
if mode == 21:
	def get_audio_data(pathToFile: Path):
		extensions = ['png', 'jpg', 'jpeg', 'webp', 'ico', 'gif', 'bmp', 'tiff', 'svg', 'heic', 'avif']
		if pathToFile.suffix in extensions:
			return None

		ffprobeOutput = subprocess.run(
			f'ffprobe '
			f'-select_streams a:0 '
			f'-show_entries format=format_name,duration,size,bit_rate:stream=codec_name,sample_rate,channels,bit_rate:format_tags:stream_tags -print_format json "{pathToFile}"',
			shell=True, capture_output=True)
		ffprobeOutputJson = json.loads(ffprobeOutput.stdout)

		results = {}
		results.update({'format': ffprobeOutputJson['format']})
		results.update({'streams': ffprobeOutputJson["streams"][0]})
		tags = {}
		if 'tags' in ffprobeOutputJson['format']:
			tags.update(ffprobeOutputJson['format']['tags'])
			results['format'].pop('tags')

		if 'tags' in ffprobeOutputJson["streams"][0]:
			tags.update(ffprobeOutputJson["streams"][0]['tags'])
			results['streams'].pop('tags')

		results.update({'tags': tags})

		def convert_numeric_keys_values(d):
			new_dict = {}
			for key, value in d.items():
				if isinstance(key, str):
					try:
						if key.isdigit():
							key = int(key)
						else:
							key = float(key)
					except ValueError:
						pass

				if isinstance(value, dict):
					value = convert_numeric_keys_values(value)

				elif isinstance(value, str):
					try:
						if value.isdigit():
							value = int(value)
						else:
							value = float(value)
					except ValueError:
						pass

				new_dict[key] = value
			return new_dict

		results = convert_numeric_keys_values(results)

		return results
if mode == 20:
	pathToFile = winFilePath()
	fileInfo = get_audio_data(pathToFile)
	codecName = fileInfo['streams']['codec_name']
	durationMinutes = fileInfo['format']['duration']
	print(codecName)
	print(durationMinutes)
	with open("data.json", "w") as f:
		f.write(json.dumps(fileInfo))

	if input('\n\nProceed?') == '':
		subprocess.run(f'ffmpeg '
					   f'-y '
					   f'-i "{pathToFile}" '
					   f'-map_metadata 0 '
					   f'-id3v2_version 3 -write_id3v1 1 '
					   f'-c:a libmp3lame -b:a 320k '
					   f'"{pathToFile.with_suffix('.mp3')}"'
					   )
