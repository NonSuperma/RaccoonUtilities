import subprocess
import sys
import msvcrt
import os
from datetime import datetime
from pathlib import Path
import colorama
from colorama import Fore
import json
import validators
import pyperclip
import time
import configparser


def get_mpv_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'mpv.exe'
    return Path('mpv.exe')


def get_ytdlp_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'yt-dlp.exe'
    return Path('yt-dlp.exe')


def get_stream_info(yt_dlp_exe, url):
    try:
        cmd = [
            str(yt_dlp_exe),
            '--dump-json',
            '--no-playlist',
            url
        ]

        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        data = json.loads(result)
        return data
    except subprocess.CalledProcessError:
        return None
    except json.JSONDecodeError:
        return None


def config_parser():
    config = configparser.ConfigParser()
    config.read('stream_downloader.ini')

    config_dict = {}

    for section in config.sections():
        for item in config.items(section):
            key = item[0]
            keyword = item[1]
            config_dict[key] = keyword
    return config_dict


def ask_exit(message: str = '', timeout: int = 5) -> None:
    print(message)
    print(f'Press any key to exit (or wait {timeout} more seconds)')
    start = time.monotonic()
    last_shown = None

    while True:
        if msvcrt.kbhit():
            msvcrt.getch()
            break

        elapsed = time.monotonic() - start
        remaining = max(0, int(timeout - elapsed))

        if remaining != last_shown:
            print(f"\033[F\033[K"  # Move curson up, to beginning of line and clear line
                  f"Press any key to exit "
                  f"(or wait {remaining} more seconds)…")
            last_shown = remaining

        if elapsed >= timeout:
            break

        time.sleep(0.05)

    sys.exit()


def update_ytdlp():
    print(f'{Fore.CYAN}Checking if yt-dlp.exe is up to date...{Fore.RESET}')
    try:
        process = subprocess.Popen(
            ['yt-dlp', '-U'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            text=True,
        )
        line_count = 0
        updated = False
        version = None
        for line in iter(process.stdout.readline, ''):
            print(f'{Fore.LIGHTYELLOW_EX}{line.strip()}{Fore.RESET}')
            if 'ERROR' in line:
                raise ConnectionError
            if 'Updating' in line:
                updated = True
            if 'Current version' in line:
                version = line[len('Current version: '):]
            if 'Latest version' in line:
                version = line[len('Latest version: '):]
            line_count += 1
        process.wait()
        for i in range(line_count):
            sys.stdout.write("\033[F\033[K")
        if updated:
            print(f'{Fore.GREEN}'
                  f'Updated to: {version}\n'
                  f'{Fore.RESET}')
        else:
            print(f'{Fore.GREEN}'
                  f'Yt-dlp is up to date [{str(version).strip()}]\n'
                  f'{Fore.RESET}')
    except ConnectionError:
        print(f'{Fore.LIGHTRED_EX}Error updating yt-dlp to newest version!!!{Fore.RESET}')
        decision_temp = input(f'Continue with the current version? '
                              f'(It is highly recommended to abort and manually update yt-dlp to latest stable version)\n'
                              f'y/n\n: ')
        if decision_temp.lower() == 'n':
            ask_exit('')


def main():
    CLEARLINE = '\033[K'  # from the cursor to the right

    os.system("mode con: cols=80 lines=20")
    os.system("title Stream Recorder")

    colorama.init(autoreset=True)

    mpv_exe = get_mpv_path()
    yt_dlp_exe = get_ytdlp_path()

    print(f'{Fore.CYAN}Checking tools...{Fore.RESET}')
    if not yt_dlp_exe.exists():
        print(
            f"{Fore.RED}CRITICAL: yt-dlp.exe not found! It has to be in the same folder as stream_downloader.exe{Fore.RESET}\n"
            f"Press Enter to exit...")
        return
    print(f'{Fore.GREEN}All tools there ^^{Fore.RESET}\n')

    update_ytdlp()

    try:
        clipBoardData = pyperclip.paste()
    except (Exception,):
        clipBoardData = None

    # If clipboards is a URL use it, if not, get URL
    if validators.url(clipBoardData):
        url = clipBoardData

        print(f'{Fore.GREEN}Found a valid url link in the clipboard!{Fore.RESET}\n'
              f'{Fore.LIGHTCYAN_EX}{url}{Fore.RESET} - using that one.\n')
    else:
        urlInput_count = 0
        while True:
            print('Url: ', end='')
            temp_url = input()
            if validators.url(temp_url):
                url = temp_url
                sys.stdout.write("\033[F\033[K")
                print(f'{Fore.GREEN}'
                      f'Url:{Fore.RESET} {url}')
                break
            else:
                sys.stdout.write("\033[F\033[K")
            urlInput_count += 1

    if 'lemoncams.com' in url and 'chaturbate' in url:
        url = url.replace('lemoncams.com/chaturbate', 'chaturbate.com')
    if 'www.lemoncams.com/bongacams' in url:
        url = url.replace('www.lemoncams.com/bongacams', 'bongacams.com')

    print(f"{Fore.CYAN}Fetching stream metadata...{Fore.RESET}")
    meta = get_stream_info(yt_dlp_exe, url)

    if not meta:
        print(f"{Fore.RED}Error: Could not fetch info.{Fore.RESET}")
        streamer_name = None
        stream_title = None
        resolution = None
        vcodec = None
        acodec = None
    else:
        streamer_name = meta.get('id') or meta.get('display_id')
        stream_title = meta.get('title')
        resolution = f"{meta.get('width')}x{meta.get('height')}"
        vcodec = meta.get('vcodec')
        acodec = meta.get('acodec')

        if stream_title:
            os.system(f"title {stream_title}")

        print(f"\n{Fore.MAGENTA}--- STREAM INFO ---{Fore.RESET}")
        print(f"Streamer:   {Fore.WHITE}{streamer_name}{Fore.RESET}")
        print(f"Title:      {Fore.WHITE}{stream_title}{Fore.RESET}")
        print(f"Quality:    {Fore.WHITE}{resolution}({vcodec} - {acodec}){Fore.RESET}")
        print(f"-------------------")

    time_now = datetime.now()
    timestamp = time_now.strftime("%Y-%m-%d__%H-%M-%S")

    if streamer_name:
        filename = f'{streamer_name}_{timestamp}.mkv'
    else:
        filename = f'stream_capture_{timestamp}.mkv'

    window_title = stream_title if stream_title else 'Stream'

    config = configparser.ConfigParser()
    config.read('stream_downloader.ini')

    config_dict = {}

    for section in config.sections():
        if section == 'Default':
            continue
        for item in config.items(section):
            key = item[0]
            keyword = item[1]
            config_dict[key] = keyword

    output_dir = Path(config['Default']['path'])
    for key in config_dict.keys():
        if key in url:
            output_dir = Path(config_dict[key])

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    #os.system(f"mode con: cols={len(str(file_path))} lines=20")

    print(f"{Fore.MAGENTA}Saving to:\n"
          f"{file_path}{Fore.RESET}\n"
          f""
          f"{Fore.CYAN}Press 'q' to toggle recording.{Fore.RESET}\n"
          f"{Fore.CYAN}Press 'e' to toggle mpv.{Fore.RESET}\n"
          f"{Fore.CYAN}Press 't' to finish.{Fore.RESET}\n"
          f"{Fore.CYAN}Press 'g' to finish {Fore.LIGHTCYAN_EX}but remove VOD.{Fore.RESET}")

    dl_cmd = [
        str(yt_dlp_exe),
        '--ignore-errors',
        '--no-live-from-start',
        '--retries', 'infinite',
        '--fragment-retries', 'infinite',
        '--skip-unavailable-fragments',
        '--wait-for-video', '15',
        '--no-part',
        '-o', '-',
        url
    ]

    mpv_cmd = [
        str(mpv_exe),
        f'--title={window_title}',
        f'--force-media-title={window_title}',
        f'--script-opts=osc-title={window_title}',
        '--cache=yes',
        '--demuxer-max-bytes=100M',
        '--mute=yes',
        '--screen=1',
        '--no-border',
        '--ontop',
        '--geometry=40%',
        '--force-window=immediate',
        '--snap-window',
        '-'
    ]

    player = subprocess.Popen(
        mpv_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    start_time = time.time()
    last_update_time = 0

    recording = True
    mpv_active = True
    abandon = False
    user_stopped = False
    stream_ended = False

    total_bytes = 0
    header_cache = b""
    HEADER_MAX_SIZE = 5 * 1024 * 1024

    reconnecting_count = 0

    while not user_stopped:
        downloader = subprocess.Popen(
            dl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

        try:
            with open(file_path, 'ab') as f:
                while True:

                    chunk = downloader.stdout.read(65536)

                    if not chunk:
                        if downloader.poll() is not None:

                            if reconnecting_count == 15:
                                stream_ended = True
                                user_stopped = True

                            print(
                                f'\r{Fore.YELLOW}Stream disconnected [{reconnecting_count}]. Reconnecting in 2s...{Fore.RESET}{CLEARLINE}',
                                end='', flush=True)
                            time.sleep(2)
                            reconnecting_count += 1
                            break

                        continue

                    if len(header_cache) < HEADER_MAX_SIZE:
                        header_cache += chunk

                    if recording:
                        f.write(chunk)
                        total_bytes += len(chunk)

                    if mpv_active:
                        try:
                            player.stdin.write(chunk)
                            player.stdin.flush()
                        except (OSError, BrokenPipeError, ValueError):
                            mpv_active = False

                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key.lower() == b'q':
                            if recording:
                                recording = False
                                print(f"\n{Fore.YELLOW}Paused recording...{Fore.RESET}")

                            else:
                                recording = True
                                print(f"\n{Fore.GREEN}Starting recording again...{Fore.RESET}")

                        if key.lower() == b'e':
                            if mpv_active:
                                print(f"\n{Fore.RED}Closing MPV...{Fore.RESET}")
                                try:
                                    player.terminate()
                                except (OSError, AttributeError):
                                    pass
                                mpv_active = False
                            else:
                                print(f"\n{Fore.GREEN}Restarting MPV...{Fore.RESET}")
                                mpv_active = True
                                player = subprocess.Popen(
                                    mpv_cmd,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                )

                                try:
                                    if header_cache:
                                        player.stdin.write(header_cache)
                                    player.stdin.write(chunk)
                                    player.stdin.flush()
                                except (BrokenPipeError, OSError, ValueError):
                                    # manual widnow close
                                    mpv_active = False

                        if key.lower() == b't':
                            user_stopped = True
                            break

                        if key.lower() == b'g':
                            abandon = True
                            user_stopped = True
                            break

                    current_time = time.time()
                    if current_time - last_update_time > 0.5:
                        elapsed_seconds = int(current_time - start_time)
                        hours, rem = divmod(elapsed_seconds, 3600)
                        minutes, seconds = divmod(rem, 60)
                        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

                        rec_status = f"{Fore.GREEN}[REC]{Fore.RESET}" if recording else f"{Fore.YELLOW}[PAUSED]{Fore.RESET}"

                        if total_bytes / (1024 * 1024) > 1000:
                            size_str = f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"
                        else:
                            size_str = f"{total_bytes / (1024 * 1024):.1f} MB"

                        sys.stdout.write(f"\r{rec_status} Captured: {size_str} | Time: {time_str}   ")
                        sys.stdout.flush()
                        last_update_time = current_time

        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(2)

        try:
            downloader.terminate()
        except:
            pass

    if mpv_active:
        player.terminate()

    if abandon:
        try:
            file_path.unlink()
        except:
            pass
        print(f"\n{Fore.GREEN}Done. File rejected\n"
              f"Closing in 3s{Fore.RESET}\n")
        time.sleep(3)
    elif stream_ended:
        print(f"\n{Fore.GREEN}Stream most likely stopped (30s passed). Saved to {filename}\n")
        print(f"Press enter to end{Fore.RESET}")
        input('')
    else:
        print(f"\n{Fore.GREEN}Done. Saved to {filename}\n")
        print(f"Closing in 3s{Fore.RESET}")
        time.sleep(3)


if __name__ == '__main__':
    main()
