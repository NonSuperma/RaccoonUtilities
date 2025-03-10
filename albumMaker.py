import subprocess as sp
import tkinter.filedialog

imageInputPath = tkinter.filedialog.askopenfilename()
soundInputPaths = tkinter.filedialog.askopenfilenames()

finalFileName = input("Final file name: ")

path = soundInputPaths[0].replace('/', '\\')
path = path[:path.rfind("\\")] + "\\"

print(path)

inputPath = ''
for i in soundInputPaths:
	inputPath += f'-i "{i.replace('/', '\\')}" '

preConcat = ''
for i in range(0, len(soundInputPaths)):
	preConcat += f'[{i}:a]'

extension = soundInputPaths[0][soundInputPaths[0].rfind('.'):]

if len(f'ffmpeg {inputPath}-filter_complex "{preConcat}concat=n={len(soundInputPaths)}:v=0:a=1" {path}output{extension}') <= 8191:
	sp.run(
		f'ffmpeg {inputPath}-filter_complex "{preConcat}concat=n={len(soundInputPaths)}:v=0:a=1" {path}output{extension}',
		shell=True)
	sp.run(f'ren "{path}output{extension}" "{finalFileName + extension}"', shell=True)

	name = path + finalFileName

	sp.run(
		f'ffmpeg -r 1 -loop 1 -i "{imageInputPath}" -i "{name + extension}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{name}.mp4"',
		shell=True)
	if f'"{name}.mp4"' != f'{finalFileName + extension}':
		sp.run(f'del {finalFileName + extension}', shell=True)
	exit()

else:
	splitInputPath = inputPath.split("-i")
	for number in range(len(splitInputPath)):
		splitInputPath[number] = '-i' + splitInputPath[number]
	splitInputPath.pop(0)

	firstSongPath = splitInputPath[0]
	splitInputPath.pop(0)

	sp.run(
		f'ffmpeg {firstSongPath + splitInputPath[0]}-filter_complex "[0:a][1:a]concat=n=2:v=0:a=1" {path}output0{extension}'.replace(
			"  ", " "),
		shell=True)
	for index in range(1, len(splitInputPath)):
		sp.run(
			f'ffmpeg -i {path}output{index - 1}{extension} {splitInputPath[index]}-filter_complex "[0:a][1:a]concat=n=2:v=0:a=1" {path}output{index}{extension}'.replace(
				"  ", " "),
			shell=True)
		sp.run(f'del {path}output{index - 1}{extension}', shell=True)
	sp.run(f'ren "{path}output{len(soundInputPaths) - 2}{extension}" "{finalFileName + extension}"', shell=True)

	name = path + finalFileName

	sp.run(
		f'ffmpeg -r 1 -loop 1 -i "{imageInputPath}" -i "{name + extension}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{name}.mp4"',
		shell=True)

	if f'"{name}.mp4"' != f'{finalFileName + extension}':
		sp.run(f'del {finalFileName + extension}', shell=True)
