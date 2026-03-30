from Raccoon.windowsUtilities import *
import os
import subprocess
# flac to mp4


def main():
	init(autoreset=True)
	 # image input
	try:
		imageFilePath = win_file_path('Pick the album cover image', filetypes='image')
	except MissingInputError:
		ask_exit(f"{Fore.RED}User closed the window!")

	# flac song inputs
	try:
		filetypeSelection = [
			("FLAC files", "*.FLAC"),
		]
		audioFilesPaths = win_files_path('Pick FLAC inputs', filetypes=filetypeSelection)
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


if __name__ == '__main__':
	main()