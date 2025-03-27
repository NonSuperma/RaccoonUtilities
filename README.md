Couple of small python scripts that I work on to learn python and use them for video downloading/editing\
Use as you wish, it's bad anyway\
\
Explanation for each file:

-Racoon.py\
Base of functions, classes and Errors that are used throughts the other files.

-All the V files are versions of a simple assist script that automates what you have to do to normally use yt-dlp.\
**Requirements:**\
Newest version of yt-dlp.exe and ffmpeg to be put in the same directory as V#.py\
-config\
config for the V files.\
\
\
-##-\
**All the following scripts need ffmpeg in the same directory to work**\
-##-\
\
-vidCutter.py\
Asks you to pick a video file, then asks you to pick the starting and ending time of that video. It then cuts out the specified chunk of the video out, without removing the oryginal.

-vidMaker.py\
Asks you to pick an image first, then any given amount of audio files (in that order). It then combines each audio file with the image, making a 1fps video with the still image and audio in the background.\
*It copies the audio codec from the file, uses the highest bitrate possible, and usues the H.264 codec for the final .mp4 video.*

-albumMaker.py\
Asks you to pick and image first, then any given amount of audio files(in that order). It then concats all the audio files to eachother, making one file that it then uses in the same way vidMaker does, merging the picture with the audio file and outputing both an mp4 file and the concated audio file.

-vidFixer.py\
Asks you to pick video files. It then re-encodes the videos to libx264, yuv420p and copies the audio encoding. It's intended to fix videos that have weird encoding that's not compatable with some video players.

-renamer.py\
Asks you to pick files, then asks you to input a string it will append at the beginning of each filename.

-file_converter.py (don't ask me why the naming convention is changed I have no clue what I'm doing.)\
Asks you to pick files, then to input an extension. It will then convert each of the chosen files to the chosen extension.

-FullAlbumCreator.py\
Asks you for album image, any amount of audio files, and a final file name. It then:\
Creates videos with vidMaker.py and puts them in one folder\
Created concaded audio and video files with albumMaker.py\
Moves the oryginally selected audio file to one of the new folder.

