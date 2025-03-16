import subprocess as sp
import tkinter.filedialog

def shell(command, captureOutput=bool()):
	sp.run(command, shell=True, capture_output=captureOutput)

file = tkinter.filedialog.askopenfilename().replace('/', '\\')
if file.find(" ") != -1:
	shell(f'ren "{file}" "{file[file.rfind('\\')+1:].replace(' ', '_')}"')
	file = file.replace(' ', '_')

fileName = file[file.rfind('\\')+1:file.rfind('.')]
path = file[:file.rfind("\\")]
print(file)
print(path)

duration = sp.run(f'ffprobe -v error -sexagesimal -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file}"', capture_output=True, shell=True).stdout.decode().replace("\r\n", "")
duration = duration[:duration.rfind(".")]

start = input(f"{duration}\nXX XX XX\nStart: ").replace(" ", ":")
tempVar = input(f"{duration}\nXX XX XX\nEnd: ").replace(" ", ":")
if tempVar == "":
	end = duration
else:
	end = tempVar


print(f'ffmpeg -ss {start} -to {end} -i {file} -c copy "{path}\\{fileName}__CUT.mp4"')
shell(f'ffmpeg -ss {start} -to {end} -i {file} -c copy "{path}\\{fileName}__CUT.mp4"')