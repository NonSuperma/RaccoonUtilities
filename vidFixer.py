import subprocess as sp
import tkinter.filedialog


def shell(command, captureOutput=bool()):
	sp.run(command, shell=True, capture_output=captureOutput)


files = list(tkinter.filedialog.askopenfilenames())
for index in range(len(files)):
	files[index] = files[index].replace('/', '\\')

paths = []
for file in files:
	paths.append(file[:file.rfind("\\")])

names = []
for file in files:
	names.append(file[file.rfind("\\")+1:file.rfind('.')])

if len(files) == 0:
	exit()

for index in range(len(files)):
	shell(f'ffmpeg -i {files[index]} -c:v libx264 -crf 20 -c:a copy -b:a 160k -vf format=yuv420p -movflags +faststart {paths[index]}\\{names[index]}.fixed.mp4')
	shell(f'del {paths[index]}\\{names[index]}.mp4')
	shell(f'ren {paths[index]}\\{names[index]}.fixed.mp4 {names[index]}.mp4')
