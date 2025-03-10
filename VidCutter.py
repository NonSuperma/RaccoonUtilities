import subprocess as sp
import tkinter.filedialog

def shell(command, captureOutput=bool()):
	sp.run(command, shell=True, capture_output=captureOutput)

file = tkinter.filedialog.askopenfilename().replace('/', '\\')
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


# dimentions = sp.run(f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "{imageInputPath}"', shell=True, capture_output=True).stdout.decode().replace("\r\n", "")


print(f'ffmpeg -ss {start} -to {end} -i {file} -c copy "{path}\\out.mp4"')
shell(f'ffmpeg -ss {start} -to {end} -i {file} -c copy "{path}\\out.mp4"')