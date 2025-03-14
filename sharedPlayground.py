import configparser
import subprocess as sp
import tkinter.filedialog


config = configparser.ConfigParser(allow_no_value=True, delimiters='=')
config.optionxform = str
config.read("config.ini")

configOptionList = ''
for section in config.sections():
    if section == "DownloadPath":
        continue
    for key in config[section]:
        configOptionList += key + ' '

for key in config['DownloadPath']:
    downloadPath = f'{sp.run(f'echo {key}', shell=True, capture_output=True, universal_newlines=True).stdout.replace('%', '')} '.replace('\n', '')[3:]
    configOptionList += f'{sp.run(f'echo {key}', shell=True, capture_output=True, universal_newlines=True).stdout.replace('%', '')} '.replace('\n', '')
print(downloadPath)
print(configOptionList)



primaryUrl = 'https://www.youtube.com/watch?v=YKsQJVzr3a8&list=PLhu_BwnCi_WausW4fZA-O8mB7fRGTShWZ'
path = None
#idCheck = sp.run(f'yt-dlp --flat-playlist --print id "{primaryUrl}" -i', shell=True, capture_output=True).stdout.decode()





#if primaryUrl.find("list") != -1:
#    isAPlaylist = True
#    idCheck = sp.run(f'yt-dlp --flat-playlist --print id "{primaryUrl}" -i', shell=True, capture_output=True).stdout.decode().split()
#    urlList = []
#    for id in idCheck:
#        urlList.append(f"https://www.youtube.com/watch?v={id}")
#else:
#    isAPlaylist = False











optionsDescription = (
    '\nEnter options with a whitespace as a separator.'
    "\n---------------------------------------------------------------------------------------\n"
    "\n--download-sections  |  -d  |  Downloads only selected time-frame  |  *{Start}-{End}"
    "\n--write-thumbnail  |  -wt  |  Saves the thumbnail in the same path as the file"
    "\n-res  |  Custom resolution."
    "\n-p  |  Custom path\n"
    "\n---------------------------------------------------------------------------------------\n"
)
print(optionsDescription)

# Get tempOptions form OptionsDescription, replacing non-input related shortcut options with their full counterparts
tempOptions = input(f'\n: ').replace('-d', '--download-sections').replace('-wt', "--write-thumbnail")
if tempOptions[-1] != ' ':
    tempOptions += ' '
print(tempOptions + '\n')

# Check for custom options, get input and apply to tempOptions
if tempOptions.find("-res") != -1:
    sp.run(f'yt-dlp -F {primaryUrl}')
    tempOptions = tempOptions.replace('-res', '-f ' + input("WARNING!\nInclude both audio and video id! Example: 234+ba\nid: "))
if tempOptions.find("-p") != -1:
    path = tkinter.filedialog.askdirectory().replace('/', '\\')
    tempOptions = tempOptions.replace('-p', f'-P "{path}"')
print(path)

print(tempOptions)



primaryUrl = "https://youtu.be/YKsQJVzr3a8?si=U4W8tXNK7djtjd2b"

optionsDescription = (
    '\nEnter options with a whitespace as a separator.\n'
    "---------------------------------------------------------------------------------------"
    "\n--download-sections  |  -d  |  Downloads only selected time-frame  |  *{Start}-{End}"
    "\n--write-thumbnail  |  -wt  |  Saves the thumbnail in the same path as the file"
    "\n-res  |  Check and use custom resolutions"
    "\n-p  |  Custom path | Opens a directory selection window if alone, or uses the path given after it. Example: -p C:\\Users\\user\\Documents\n"
    "---------------------------------------------------------------------------------------"
)
print(optionsDescription)

# Get tempOptions form OptionsDescription, replacing non-input related shortcut options with their full counterparts
tempOptions = input(f': ').replace('-d', '--download-sections').replace('-wt', "--write-thumbnail")
if tempOptions[-1] != ' ':
    tempOptions += ' '

# Check for custom options, get input if needed and add to tempOptions
if tempOptions.find("-res") != -1:
    sp.run(f'yt-dlp -F {primaryUrl}')
    tempOptions = tempOptions.replace('-res', '-f ' + input("WARNING!\nInput both audio and video ids if you want both! Include one id for just one stream.\nExample: 234+ba\nid: "))
if tempOptions.find("-p") != -1:
    try:
        path_start = tempOptions.find("-p") + 3
        path_end = tempOptions.find(" -", path_start)
        if path_end == -1:
            path_end = len(tempOptions)
        path = tempOptions[path_start:path_end].strip()
        tempOptions = tempOptions.replace(f'-p {path}', f'-P "{path}"')
    except IndexError:
        path = tkinter.filedialog.askdirectory().replace('/', '\\')
        tempOptions = tempOptions.replace('-p', f'-P "{path}"')
