from Racoon import RacoonMediaTools as Ru
from Racoon import RacoonErrors as RuE


if __name__ == "__main__":
	imageInputPath = Ru.winFilePath('Pick album cover image')
	soundInputPaths = Ru.winFilesPath('Pick songs')
	finalFilename = input("Final file name: ")
	outputPath = None
	try:
		vid = Ru(imageInputPath, soundInputPaths)
		vid.makeAlbum(outputPath, finalFilename)
	except RuE.RacoonUtilitiesMissingInputError:
		print("RacoonUtilitiesMissingInputError: No input")
		askExit()
	except RuE.RacoonUtilitiesInputLengthError:
		print("RacoonUtilitiesInputLengthError: Too many audio files selected")
		askExit()
	exit()
