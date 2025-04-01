import subprocess as sp
from Racoon import RacoonUtils as Ru
from Racoon import RacoonErrors as RuE


if __name__ == "__main__":
	imageInputPath = Ru.winFilePath("Album cover")
	soundInputPaths = Ru.winFilesPath("Audio files")
	outputPath = None
	try:
		vid = Ru(imageInputPath, soundInputPaths)
		vid.makeVideo(outputPath)
		for path in soundInputPaths:
			sp.run(f'del "{path}"', shell=True)
		sp.run(f'del "{imageInputPath}"', shell=True)

	except RuE.MissingInputError:
		print("No input!")
		Ru.askExit()
	exit()
