from Racoon import RacoonMediaTools as RacoonMTools
from Racoon import RacoonErrors as RacoonE



if __name__ == "__main__":
	imageInputPath = RacoonMTools.winFilePath('Pick the album cover image')
	soundInputPaths = RacoonMTools.winFilesPath('Pick songs')

	workingFolderPath = soundInputPaths[0][:soundInputPaths[0].rfind("\\")]
	workingFolderName = workingFolderPath[workingFolderPath.rfind("\\") + 1:]
	userChoice = input(
		f'The selected songs are in a folder called "{workingFolderName}"\nPress enter to use that folder as the album name, or input the album name manually\n: ')
	if userChoice == '':
		albumName = workingFolderName
	else:
		albumName = userChoice

	outputPath = None
	try:
		vid = RacoonMTools(imageInputPath, soundInputPaths)
		vid.makeAlbum(outputPath, albumName)
	except RacoonE.MissingInputError:
		print("RacoonUtilitiesMissingInputError: No input")
		RacoonWTools.askExit()
	exit()
