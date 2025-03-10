import subprocess as sp
import tkinter.filedialog

def shell(command, captureOutput=bool()):
	sp.run(command, shell=True, capture_output=captureOutput)

TestFile = tkinter.filedialog.askopenfilename().replace('/', '\\')

#duration = sp.run(f'ffprobe -v error -sexagesimal -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file}"', capture_output=True, shell=True).stdout.decode().replace("\r\n", "")
#duration = duration[:duration.rfind(".")]

#dimentions = sp.run(f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "{imageInputPath}"', shell=True, capture_output=True).stdout.decode().replace("\r\n", "")

