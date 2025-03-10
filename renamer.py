import subprocess as sp
import tkinter.filedialog

fileList = tkinter.filedialog.askopenfilenames()
addon = input(": ")
print(addon)
for i in fileList:
	i = i.replace('/', '\\')
	if i.find(addon) != -1:
		continue
	print(f'ren "{i}" "{i[:i.rfind("\\")+1] + addon + i[i.rfind("\\")+1:]}"')
	sp.run(f'rename "{i}" "{addon + i[i.rfind("\\")+1:]}"', shell=True)
