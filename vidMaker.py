from Playground import folderPath
from Raccoon.windowsUtilities import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.errors import *
from playsound3 import playsound
from colorama import Fore
import sys
import pyperclip
import os

def main():
	flacFilePaths = winFilesPath('Audio', 'audio')
	folderPath = flacFilePaths[0].parent

	label = ''

	temp = str(folderPath).split('\\')
	for index in range(len(temp)):
		temp[index] = temp[index].replace("'", '').strip()
	folderPath_safe = Path('\\'.join(temp))
	trackCount = len(flacFilePaths)

	flacFilePaths_safe = []
	for path in flacFilePaths:
		flacFilePaths_safe.append(Path.joinpath(folderPath_safe, str(path.name).replace("'", '')))

	for index in range(trackCount):
		flacFilePaths[index].rename(Path.joinpath(folderPath, flacFilePaths_safe[index].name))

	folderPath.rename(Path.joinpath(folderPath.parent, folderPath_safe.name))
	# folderPath.parent.rename(Path.joinpath(folderPath.parent.parent, folderPath_safe.parent.name))

	coverPath = winFilePath('Cover', 'image', initialDir=folderPath_safe)
	coverDimentions = ScaleToEven(coverPath).dimensions
	if coverDimentions[0] > 1000 and coverDimentions[1] > 1000 and (coverDimentions != [1000, 1000]):
		userChoice = input(f'Scale album cover to 1000x1000? Enter=Yes, n=No\n'
						   f': ')
		if userChoice != 'n':
			print(f'Converting cover...')
			coverPath = ScaleImage(coverPath, '1000:1000', remove_old=False)
			print(f'{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}\n')

	if trackCount > 1:
		with open(f'{folderPath_safe}\\temp_audio_list.txt', 'w+', encoding='utf-8') as f:
			for file in flacFilePaths_safe:
				f.write(f"file '{str(file)}'\n")

		print(f'Concading "{folderPath_safe.name}.flac"...')
		concadedFlacPath = Path.joinpath(folderPath_safe, str(folderPath_safe.name) + '.flac')
		ffmpegOutput_concad = subprocess.run(
			f'ffmpeg '
			f'-y '
			f'-loglevel fatal '
			f'-f concat '
			f'-safe 0 '
			f'-i "{folderPath_safe}\\temp_audio_list.txt" '
			f'"{concadedFlacPath}"'
		)
		print(f'{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}\n')
		Path(f"{folderPath_safe}\\temp_audio_list.txt").unlink()
	else:
		concadedFlacPath = Path.joinpath(folderPath_safe, str(flacFilePaths_safe[0].name))

	print(f'Converting {concadedFlacPath.name} to mp3')
	mp3FilePath = Path.joinpath(folderPath_safe, f'{concadedFlacPath.stem}.mp3')
	subprocess.run(
		f'ffmpeg '
		f'-y '
		f'-loglevel fatal '
		f'-i "{concadedFlacPath}" '
		f'-map_metadata 0 '
		f'-id3v2_version 3 -write_id3v1 1 '
		f'-c:a libmp3lame -b:a 320k '
		f'"{mp3FilePath}"'
	)
	print(f'{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}\n')

	print(f'Converting "{mp3FilePath.name}" to mp4...')
	if len(flacFilePaths) > 1:
		label += ' [Full Album]'
	artist = str(mp3FilePath.parent.parent.name)
	if artist not in mp3FilePath.name:
		mp4FinalPath = Path.joinpath(folderPath_safe, artist + ' - ' + str(mp3FilePath.stem) + label + '.mp4')
	else:
		mp4FinalPath = Path.joinpath(folderPath_safe, str(mp3FilePath.stem) + label + '.mp4')
	subprocess.run(
		f'ffmpeg '
		f'-loglevel fatal '
		f'-y '
		f'-loop 1 '
		f'-framerate 1 '
		f'-i "{coverPath}" '
		f'-i "{mp3FilePath}" '
		f'-map 0:v:0 -map 1:a:0 '
		f'-c:v libx264 -crf 30 -tune stillimage '
		f'-c:a copy '
		f'-shortest '
		f'-movflags +faststart '
		f'-map_metadata 1 '
		f'-id3v2_version 3 -write_id3v1 1 '
		f'-vf "format=yuv420p" '
		f'-r 1 '
		f'"{mp4FinalPath}"'
	)
	print(f'{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}\n')

	if trackCount > 1:
		concadedFlacPath.unlink()
	mp3FilePath.unlink()

	for index in range(trackCount):
		flacFilePaths_safe[index].rename(Path.joinpath(folderPath_safe, flacFilePaths[index].name))

	folderPath_safe.rename(Path.joinpath(folderPath_safe.parent, folderPath.name))


if __name__ == "__main__":

	main()

	# input('Press Enter to exit...')
	playsound('SourceFiles\\au5-1.mp3')
	os.startfile(folderPath)
	pape
	sys.exit(0)
