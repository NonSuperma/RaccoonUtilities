from Raccoon.windowsUtilities import *
from Raccoon.audioUtilities import *
from Raccoon.errors import *
from Raccoon.imageUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.mediaUtilities import *
from colorama import Fore, Back, Style, init
from pathlib import Path
import subprocess
import sys
import os


def main():
	init(autoreset=True)

	try:
		imageFilePath = win_file_path('Pick the album cover image', filetypes='image')
	except MissingInputError:
		ask_exit(f"{Fore.RED}User closed the window!")


	try:
		filetypeSelection = [
			("All without images", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus *.webm *.mp4 *.mov *.avi *.wmv"),
			("MP3 files", "*.MP3"),
			("AAC files", "*.AAC"),
			("FLAC files", "*.FLAC"),
			("WAV files", "*.WAV"),
			("PCM files", "*.PCM"),
			("M4A files", "*.M4A"),
			("OPUS files", "*.opus"),
			("Video files", "*.webm *.mp4 *.mov *.avi *.wmv")
		]
		audioFilesPaths = win_files_path('Pick songs', filetypes=filetypeSelection)
	except MissingInputError:
		ask_exit(f"{Fore.RED}User closed the window!")

	workingFolderPath = audioFilesPaths[0].parent
	workingFolderName = workingFolderPath.name

	userChoice = input(
		f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} The selected songs are in a folder called {Fore.GREEN}{workingFolderName}{Fore.RESET}\n'
		f'       Press {Back.BLACK}ENTER{Back.RESET} to use that folder as the album name, or input the album name manually\n'
		f'       {Fore.LIGHTBLUE_EX}[]{Fore.RESET} gets converted into {Fore.GREEN}{workingFolderName}{Fore.RESET}\n'
		f'       {Fore.LIGHTBLUE_EX}--full{Fore.RESET} removes {Fore.LIGHTBLUE_EX}[Full Album]{Fore.RESET} from the final name\n'
		f'       : '
	)

	if userChoice == '':
		albumName = workingFolderName + ' [Full Album]'
	elif userChoice == '--full':
		albumName = workingFolderName
	else:
		albumName = userChoice

		if '[]' in albumName:
			albumName = albumName.replace('[]', workingFolderName)

		if '--full' in albumName:
			if ' --full' in albumName:
				albumName = albumName.replace(' --full', '')
			if ' --full ' in albumName:
				albumName = albumName.replace(' --full ', '')
			if '--full ' in albumName:
				albumName = albumName.replace('--full ', '')
			albumName = albumName.replace('--full', '')
		else:
			albumName += ' [Full Album]'

	print(f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} Filename chosen: {Fore.LIGHTBLUE_EX}"{albumName}"{Fore.RESET}\n')

	audioSourceFolderPath = Path.joinpath(workingFolderPath, 'Source Files')
	os.makedirs(audioSourceFolderPath, exist_ok=True)

	finalConcadFilePath = workingFolderPath.joinpath(albumName).with_suffix('.flac')
	finalMp4FilePath = workingFolderPath.joinpath(albumName).with_suffix('.mp4')

	# check for uneven image input dimentions and scale if yes
	print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
		  f'Checking {Fore.LIGHTYELLOW_EX}"{imageFilePath.name}"{Fore.RESET} '
		  f'for uneven image dimentions...')
	oryginal_dimentions = get_media_dimentions(imageFilePath)
	try:
		ScaleToEven_Output = scale_to_even(imageFilePath)
		if ScaleToEven_Output.returncode == 0:
			print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
				  f'{Fore.LIGHTGREEN_EX}Scaled {Fore.LIGHTYELLOW_EX}"{imageFilePath.name}"{Fore.RESET} '
				  f'{Fore.LIGHTGREEN_EX}from ({oryginal_dimentions[0]}:{oryginal_dimentions[1]}) '
				  f'to even '
				  f'({ScaleToEven_Output.dimensions[0]}:{ScaleToEven_Output.dimensions[1]}) '
				  f'dimentions!\n{Style.RESET_ALL}')
		else:
			print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
				  f'{Fore.LIGHTGREEN_EX}Dimentions are even!\n{Style.RESET_ALL}')
	except FfmpegGeneralError:
		ask_exit(f'{Fore.RED}Something went wrong while scaling the cover image!{Fore.RESET}\n'
				  f'Ffmpeg needs even dimentions to work\n'
				  f'Try manually changing the dimentions to be even and then try again')

	# Temp audio paths like workingFolderPath//"audio1.flac"
	tempAudioPaths = []
	for index in range(len(audioFilesPaths)):
		tempAudioPaths.append(Path(workingFolderPath, 'audio' + str(index)).with_suffix('.flac'))


	# Convert every audio input to the temp audio file
	for index in range(len(audioFilesPaths)):
		audioPath = audioFilesPaths[index]
		tempAudioPath = tempAudioPaths[index]

		print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
			  f'Converting {Fore.LIGHTYELLOW_EX}"{audioPath.name}"{Fore.RESET} '
			  f'to .flac...  '
			  f'{Fore.LIGHTGREEN_EX}({index + 1}/{len(audioFilesPaths)}){Fore.RESET}')
		try:
			ffmpegOutput_converter = sp.run(f'ffmpeg '
											f'-loglevel fatal '
											f'-y '
											f'-i "{audioPath}" '
											f'-c:a flac '
											f'"{tempAudioPath}"',
											shell=True, capture_output=False)
			if ffmpegOutput_converter.returncode != 0:
				raise FfmpegGeneralError('Something went to shit')
		except FfmpegGeneralError:
			ask_exit("Something went wrong while converting audio input into flac")
	try:
		with open(workingFolderPath / 'audio_input_list.txt', 'w+', encoding='utf-8') as audio_input_list:
			for tempAudioPath in tempAudioPaths:
				audio_input_list.write(f"file '{str(tempAudioPath)}'\n")
	except (Exception,):
		ask_exit(
			f'{Fore.RED}Something went wrong while creating and writing the audio list!{Fore.RED}\n')

	# Concad audio files
	print(f'\n{Fore.LIGHTCYAN_EX}[Concad]{Style.RESET_ALL} Concading audio files into one...  ')
	try:
		ffmpegOutput_concad = sp.run(f'ffmpeg '
									 f'-y '
									 f'-loglevel fatal '
									 f'-f concat '
									 f'-safe 0 '
									 f'-i "{str(workingFolderPath.joinpath('audio_input_list.txt'))}" '
									 #f'-c:a flac '
									 f'"{finalConcadFilePath}"',
									 capture_output=True)
		if ffmpegOutput_concad.returncode != 0:
			raise FfmpegConcadError('something went to shit')

	except FfmpegConcadError:
		print(ffmpegOutput_concad)
		ask_exit(f'{Fore.LIGHTCYAN_EX}[Concad]{Style.RESET_ALL} '
								  f'{Fore.RED}Something went wrong while concading!{Style.RESET_ALL}')
	else:
		print(f'{Fore.LIGHTCYAN_EX}[Concad]{Fore.RESET} '
			  f'{Fore.GREEN}Done!{Fore.RESET} ')

if __name__ == '__main__':
	main()