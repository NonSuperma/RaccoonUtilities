from Racoon import RacoonMediaTools as Ru
from Racoon import RacoonErrors as RuE


if __name__ == "__main__":
	imageInputPath = Ru.winFilePath('Pick the album cover image')
	soundInputPaths = Ru.winFilesPath('Pick songs')
	finalFilename = input("Final file name: ")
	outputPath = None
	try:
		vid = Ru(imageInputPath, soundInputPaths)
		vid.makeAlbum(outputPath, finalFilename)
	except RuE.MissingInputError:
		print("RacoonUtilitiesMissingInputError: No input")
		Ru.askExit()
	exit()
