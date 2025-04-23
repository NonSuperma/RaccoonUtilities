import os.path
from PIL import ImageGrab
import subprocess

image = ImageGrab.grabclipboard()
if isinstance(image, type(None)):
    print("No image in clipboard nigga!")
    input("Press enter to exit...")
    exit()

downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
image.save(f'{downloads_path}\\clipboard.png')
subprocess.run(f'explorer {downloads_path}')