import subprocess as sp
import tkinter.filedialog

imageInputPath = tkinter.filedialog.askopenfilename()
soundInputPaths = tkinter.filedialog.askopenfilenames()

if soundInputPaths == "" or imageInputPath == "":
	exit()

if len(soundInputPaths) == 1:
	soundInputPaths = soundInputPaths[0]
	name = soundInputPaths[:soundInputPaths.rfind(".")]
	extension = soundInputPaths[soundInputPaths.rfind("."):]

	sp.run(f'ffmpeg -r 1 -loop 1 -i "{imageInputPath}" -i "{soundInputPaths}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{name}.mp4"', shell=True)
	sp.run(f'del "{imageInputPath.replace('/', '\\')}"', shell=True)
	sp.run(f'del "{soundInputPaths.replace('/', '\\')}"', shell=True)
	exit()

else:
	names = []
	for number in range(0, len(soundInputPaths)):
		names.append(soundInputPaths[number][:soundInputPaths[number].rfind(".")])
	print(names)

	for index in range(len(names)):
		sp.run(f'ffmpeg -r 1 -loop 1 -i "{imageInputPath}" -i "{soundInputPaths[index]}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{names[index]}.mp4"', shell=True)
		sp.run(f'del "{soundInputPaths[index].replace('/', '\\')}"', shell=True)
	sp.run(f'del "{imageInputPath.replace('/', '\\')}"', shell=True)
	exit()
