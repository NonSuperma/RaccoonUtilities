Couple of small python scripts that I work on to 1. learn python 2. use for video downloading and editing\
Use as you wish, it's bad anyway\
\
Explanation for each file:\
-All the V files are versions of the main yt-dlp helper. Its a simple assist script that automates what you have to do to normally use yt-dlp.\
Requirements:\
yt-dlp.exe and ffmpeg to be put in the same directory as V#.py\
\
-All the following scripts need ffmpeg in the same directory to work-\
\
-vidCutter asks you to pick a video file, then asks you to pick the starting and ending time of that video. It then cuts the video (without removing the original) to be just the length specified.\
-vidMaker asks you to pick an image first, then any given amount of audio files (in that order). It then combines each audio file with the image, making a 1fps video with the still image and audio in the background. It copies the audio codec from the file, and usues the H.264 codec for the final .mp4 video.\
