import subprocess as sp
import tkinter.filedialog

imageInputPath = tkinter.filedialog.askopenfilename().replace('/','\\')
soundInputPaths = tkinter.filedialog.askopenfilename()

for index in range(len(soundInputPaths)):
	soundInputPaths = soundInputPaths.replace('/', '\\')



#if soundInputPaths == "" or imageInputPath == "":
#exit()
#soundInputPaths = "D:\\\Other\\\Music\\Alice_In_Chains_-_Down_in_a_Hole_MTV_Unplugged_-_HD_Video.webm"
#imageInputPath = 'D:\\\Other\\\Music\\mzi.wegmszqt.jpg'

name = soundInputPaths[:soundInputPaths.rfind(".")]
extension = soundInputPaths[soundInputPaths.rfind("."):]

#print(name)
#print(extension)

#dim = sp.run(f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "{imageInputPath}"', shell=True, capture_output=True).stdout.decode().replace("\r\n", "")


sp.run(f'ffmpeg -r 1 -loop 1 -i "{imageInputPath}" -i "{soundInputPaths}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{name}.mp4"', shell=True)
#sp.run(f'ffmpeg -r 1 -loop 1 -i "{imageInputPath}" -i "{soundInputPaths}" -c:v libx264 -acodec copy -r 1 -shortest -vf scale=1000:1000 "{name}.mp4"', shell=True)
#sp.run(f'del "{imageInputPath.replace('/', '\\')}"', shell=True)
#sp.run(f'del "{soundInputPaths.replace('/', '\\')}"', shell=True)
exit()
