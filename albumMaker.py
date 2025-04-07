from Racoon import RacoonMediaTools as Ru
from Racoon import RacoonErrors as RuE


if __name__ == "__main__":
	imageInputPath = Ru.winFilePath('Pick the album cover image')
	soundInputPaths = Ru.winFilesPath('Pick songs')

	userChoice = input(
		f'The selected songs are in a folder called "{workingFolderName}"\nPress enter to use that folder as the album name, or input the album name manually\n: ')
	if userChoice == '':
		albumName = workingFolderName
	else:
		albumName = userChoice

	outputPath = None
	try:
		vid = Ru(imageInputPath, soundInputPaths)
		vid.makeAlbum(outputPath, albumName)
	except RuE.MissingInputError:
		print("RacoonUtilitiesMissingInputError: No input")
		Ru.askExit()
	exit()
