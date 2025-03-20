import subprocess as sp
import tkinter.filedialog
from vidMaker import makeVideo
from albumMaker import makeAlbum

def cmd(shell_command=str, capture_output=bool):
    sp.run(shell_command, shell=True, capture_output=capture_output)


