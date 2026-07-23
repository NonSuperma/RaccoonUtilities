import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import pyperclip
import time
from datetime import datetime
from deep_translator import GoogleTranslator
import threading
import tkinter as tk
import ctypes
from ctypes import wintypes
import os
import sys
import subprocess
import atexit


def clean_wikidata_strings(text):
    pattern = r'\b(?:title|label|date|medium|artist|author|creator)?\s*QS:(?:[^\s"]|"[^"]*")+'
    text = re.sub(pattern, '', text)
    text = re.sub(r'</?(?!https?:)[a-zA-Z]+[^>]*>', '', text)
    return re.sub(r'\s+', ' ', text).strip()


class WikimediaArtworkParser:
    def __init__(self, url, session):
       self.url = url
       self.session = session
       self.title_param = urllib.parse.unquote(url.split("/")[-1].split('?')[0])
       self.extmeta = {}
       self.soup = None
       self.raw_artist_names = []

    def fetch_data(self):
       api_url = "https://commons.wikimedia.org/w/api.php"
       params_meta = {
          "action": "query",
          "format": "json",
          "titles": self.title_param,
          "prop": "imageinfo",
          "iiprop": "extmetadata"
       }
       params_html = {
          "action": "parse",
          "format": "json",
          "page": self.title_param,
          "prop": "text"
       }
       res_meta = self.session.get(api_url, params=params_meta).json()
       res_html = self.session.get(api_url, params=params_html).json()

       pages = res_meta.get("query", {}).get("pages", {})
       page = next(iter(pages.values()), {})
       self.extmeta = page.get("imageinfo", [{}])[0].get("extmetadata", {})

       html_text = res_html.get("parse", {}).get("text", {}).get("*", "")
       self.soup = BeautifulSoup(html_text, 'html.parser')

    def extract_artist(self):
       artist_val = self.extmeta.get("Artist", {}).get("value", "")
       if not artist_val:
          return "-"

       art_soup = BeautifulSoup(artist_val, 'html.parser')
       for a in art_soup.find_all('a'):
          if a.find('img'):
             a.decompose()
             continue

          name = clean_wikidata_strings(a.get_text(strip=True))
          if not name:
             a.decompose()
             continue

          href = a.get('href', '')
          if 'wikidata.org' in href or 'Creator:' in href:
             a.replace_with(name)
          else:
             link = href
             if link.startswith('//'):
                link = 'https:' + link
             elif link.startswith('/'):
                link = 'https://commons.wikimedia.org' + link
             a.replace_with(f"[{name}](<{link}>)")

          self.raw_artist_names.append(name)

       text_out = clean_wikidata_strings(art_soup.get_text(separator=' ', strip=True))
       if text_out:
          if not self.raw_artist_names:
             for part in text_out.split('/'):
                if part.strip():
                   self.raw_artist_names.append(part.strip())
          return text_out
       return "-"

    def _get_qs_titles(self, text):
       qs_titles = {}
       p1 = r'(?:label|title)\s*QS:L([a-z]{2,3})\s*,\s*"([^"]+)"'
       p2 = r'(?:label|title)\s*QS:[A-Z0-9]+,([a-z]{2,3}):"([^"]+)"'
       for match in re.finditer(p1, text, re.IGNORECASE):
          lang, t_text = match.groups()
          qs_titles[lang.lower()] = t_text.strip()
       for match in re.finditer(p2, text, re.IGNORECASE):
          lang, t_text = match.groups()
          qs_titles[lang.lower()] = t_text.strip()
       return qs_titles

    def _extract_blue_bar_title(self):
       artwork_th = self.soup.find('th', style=lambda v: v and '#ccf' in v.lower())
       if not artwork_th:
          return None

       th_text = clean_wikidata_strings(artwork_th.get_text(separator=' ', strip=True))
       if ':' not in th_text:
          return None

       prefix, suffix = th_text.split(':', 1)
       for r_name in self.raw_artist_names:
          if r_name.lower() in prefix.lower() or prefix.lower() in r_name.lower():
             pot_title = suffix.strip()
             if len(pot_title) > 3 and not re.fullmatch(r'Q\d+', pot_title):
                return pot_title
       return None

    def _fallback_filename_title(self):
       raw_filename = urllib.parse.unquote(self.title_param.split("/")[-1])
       raw_filename = re.sub(r'\.(jpg|jpeg|png|tif|tiff|gif)$', '', raw_filename, flags=re.IGNORECASE)
       raw_filename = raw_filename.replace("File:", "").replace("_", " ")
       raw_filename = re.sub(r'\s*\([^)]*\)', '', raw_filename)

       r_drop = r'\b(attributed to|workshop of|circle of|follower of|manner of|school of|after)\b'
       raw_filename = re.sub(r_drop, '', raw_filename, flags=re.IGNORECASE)

       r_musedrop = r'\b(museum|samling|gallery|collection|musee|px|billede|img|dsc|dji|img_|sammlung|national|rcin)\b'
       raw_filename = re.sub(r_musedrop, '', raw_filename, flags=re.IGNORECASE)

       parts = re.split(r'\s*(?:[,–]|\s-\s)\s*', raw_filename)
       artist_comps = [re.sub(r'[^a-z0-9]', '', n.lower()) for n in self.raw_artist_names if n and n != "-"]

       for i, part in enumerate(parts):
          part = part.strip()
          part = re.sub(r'^[-–\s]+|[-–\s]+$', '', part)
          if not part:
             continue

          part_comp = re.sub(r'[^a-z0-9]', '', part.lower())
          is_artist = any(ac and (part_comp in ac or ac in part_comp) for ac in artist_comps)

          if i == 0 and is_artist:
             continue
          if len(part) > 4 and not part.isnumeric():
             return clean_wikidata_strings(part)
       return None

    def _fallback_description_title(self):
       desc_html = self.extmeta.get("ImageDescription", {}).get("value", "")
       if desc_html:
          desc_text = BeautifulSoup(desc_html, 'html.parser').get_text(separator=' ', strip=True)
          quotes = re.findall(r'["«“”„]([^"«“”„]{5,})["» Weimar ”]', desc_text)
          if quotes:
             return clean_wikidata_strings(quotes[0])
       return None

    def extract_title(self):
       og_title = None
       en_title = None

       title_raw_html = self.extmeta.get("ObjectName", {}).get("value", "")
       title_th = self.soup.find(id='fileinfotpl_art_title')
       if title_th and title_th.find_next_sibling('td'):
          title_raw_html += str(title_th.find_next_sibling('td'))

       title_raw_text = re.sub(r'<[^>]+>', '', title_raw_html)
       qs_titles = self._get_qs_titles(title_raw_text)

       if 'en' in qs_titles:
          en_title = clean_wikidata_strings(qs_titles['en'])
       for lang, text in qs_titles.items():
          if lang != 'en':
             og_title = clean_wikidata_strings(text)
             break

       blue_bar_en = self._extract_blue_bar_title()

       if not en_title:
          obj_name = self.extmeta.get("ObjectName", {}).get("value", "")
          if obj_name:
             en_title = clean_wikidata_strings(
                BeautifulSoup(obj_name, 'html.parser').get_text(separator=" ", strip=True))

       if title_th and title_th.find_next_sibling('td'):
          title_td = title_th.find_next_sibling('td')
          for tag in title_td.find_all(True, lang=True):
             lang = tag.get('lang', '').lower()
             clean_text = clean_wikidata_strings(tag.get_text(separator=" ", strip=True))
             if lang == 'en':
                en_title = clean_text
             elif lang and len(lang) <= 3 and not og_title:
                og_title = clean_text

          if not og_title:
             fn_div = title_td.find(class_='fn')
             if fn_div:
                og_title = clean_wikidata_strings(fn_div.get_text(separator=" ", strip=True))
             else:
                raw_title_text = clean_wikidata_strings(title_td.get_text(separator=" ", strip=True))
                if raw_title_text and raw_title_text != en_title:
                   og_title = raw_title_text

       if not og_title:
          og_title = self._fallback_filename_title()

       if not og_title:
          og_title = self._fallback_description_title()

       if blue_bar_en:
          en_title = blue_bar_en
       elif en_title:
          en_title = re.sub(r'^[A-Za-z]+:', '', en_title).strip()

       if og_title:
          og_title = re.sub(r'^[A-Za-z]+:', '', og_title).strip()

       if og_title and en_title:
          if og_title.lower() in en_title.lower() or en_title.lower() in og_title.lower():
             en_title = None

       if not og_title and not en_title:
          return '"**-**"'

       if og_title:
          final_en = en_title
          if not final_en:
             try:
                translator = GoogleTranslator(source='auto', target='en')
                translated = translator.translate(og_title)
                if translated and translated.lower() != og_title.lower():
                   final_en = translated
             except Exception as e:
                pass

          if final_en and final_en.lower() != og_title.lower():
             return f'"**{og_title}** - {final_en}"'
          return f'"**{og_title}**"'

       return f'"**{en_title}**"'

    def _get_cleaned_table_cell(self, element_id):
       th = self.soup.find(id=element_id)
       if not th or not th.find_next_sibling('td'):
          return None
       td = th.find_next_sibling('td')
       for hidden in td.find_all(style=re.compile(r'display:\s*none', re.I)):
          hidden.decompose()
       text = td.get_text(separator=' ', strip=True)
       return clean_wikidata_strings(text)

    def extract_date(self):
       date_str = self.extmeta.get("DateTimeOriginal", {}).get("value", "")
       if date_str:
          date_soup = BeautifulSoup(date_str, 'html.parser')
          for hidden in date_soup.find_all(style=re.compile(r'display:\s*none', re.I)):
             hidden.decompose()
          clean_date = clean_wikidata_strings(date_soup.get_text(separator=' ', strip=True))
          if clean_date:
             return clean_date
       return "-"

    def extract_medium(self):
       clean_med = self._get_cleaned_table_cell('fileinfotpl_art_medium')
       return clean_med if clean_med else "-"

    def extract_dimensions(self):
       clean_dims = self._get_cleaned_table_cell('fileinfotpl_art_dimensions')
       if not clean_dims:
          return "-"

       clean_dims = re.sub(r'\b(drager|beeldmaat|paneel|blad|lijst|dagmaat)\b', '', clean_dims, flags=re.IGNORECASE)
       clean_dims = re.sub(r'(?i)\bheight:', 'height:', clean_dims)
       clean_dims = re.sub(r'(?i)\bwidth:', 'width:', clean_dims)
       if 'width:' in clean_dims and '; width:' not in clean_dims:
          clean_dims = clean_dims.replace('width:', '; width:')

       clean_dims = re.sub(r'\s+', ' ', clean_dims).strip()
       return clean_dims if clean_dims else "-"

    def get_formatted_metadata(self):
       self.fetch_data()
       artist = self.extract_artist()
       title = self.extract_title()
       date = self.extract_date()
       medium = self.extract_medium()
       dimensions = self.extract_dimensions()
       return f"{title}\nPainter: {artist}\nDate: {date}\nMedium: {medium}\nDimensions: {dimensions}"


class ExtractorUI:
    def __init__(self):
       self.root = tk.Tk()
       self.root.title("Wiki Extractor")
       try:
          self.root.iconbitmap("SourceFiles/11-1.ico")
       except Exception:
          pass
       self.root.overrideredirect(True)
       self.root.withdraw()

       window_width = 800
       window_height = 400
       start_x = 0
       start_y = 5

       try:
          monitors = []
          def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
             r = lprcMonitor.contents
             monitors.append((r.left, r.top, r.right, r.bottom))
             return True

          MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(wintypes.RECT), ctypes.c_void_p)
          ctypes.windll.user32.EnumDisplayMonitors(None, None, MonitorEnumProc(callback), None)

          if len(monitors) > 1:
             m_left, m_top, m_right, m_bottom = monitors[1]
             start_x = m_right - window_width - 5
             start_y = m_top + 5
          else:
             screen_width = self.root.winfo_screenwidth()
             start_x = screen_width - window_width - 5
       except Exception:
          screen_width = self.root.winfo_screenwidth()
          start_x = screen_width - window_width - 5

       self.root.geometry(f"{window_width}x{window_height}+{start_x}+{start_y}")
       self.root.configure(bg="#050505")
       self.root.attributes("-alpha", 0.95)
       self.root.attributes("-topmost", True)
       self.root.deiconify()

       try:
          self.root.update_idletasks()
          hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
          style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
          style = style & ~0x00000080
          style = style | 0x00040000
          ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
          ctypes.windll.user32.ShowWindow(hwnd, 5)
       except Exception:
          pass

       self._drag_data = {"x": 0, "y": 0, "win_x": 0, "win_y": 0}

       self.console = tk.Text(
          self.root,
          bg="#050505",
          fg="#d8d7d9",
          font=("Lexend", 11),
          bd=0,
          highlightthickness=0,
          padx=10,
          pady=10,
          wrap=tk.WORD,
          state=tk.DISABLED
       )
       self.console.pack(fill=tk.BOTH, expand=True)

       self.console.bind("<ButtonPress-1>", self.start_drag)
       self.console.bind("<B1-Motion>", self.do_drag)
       self.root.bind("<ButtonPress-1>", self.start_drag)
       self.root.bind("<B1-Motion>", self.do_drag)
       self.root.bind("<Escape>", lambda e: self.quit_app())
       self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

       self.session = requests.Session()
       self.session.headers.update({"User-Agent": "RaccoonUtilitiesMediaFetcher/2.7"})

       self.ahk_process = None
       self.start_ahk()

       self.log_msg("Wikimedia Extractor UI initialized. Press ESC to close.")
       self.log_msg("Listening for Wikimedia Commons URLs...")

       threading.Thread(target=self.monitor_clipboard, daemon=True).start()

    def start_drag(self, event):
       self._drag_data["x"] = event.x_root
       self._drag_data["y"] = event.y_root
       self._drag_data["win_x"] = self.root.winfo_x()
       self._drag_data["win_y"] = self.root.winfo_y()

    def do_drag(self, event):
       dx = event.x_root - self._drag_data["x"]
       dy = event.y_root - self._drag_data["y"]
       new_x = self._drag_data["win_x"] + dx
       new_y = self._drag_data["win_y"] + dy
       self.root.geometry(f"+{new_x}+{new_y}")

    def log_msg(self, msg):
       now = datetime.now().strftime("%H:%M:%S")
       formatted = f"[{now}] {msg}\n"

       self.console.config(state=tk.NORMAL)
       self.console.insert(tk.END, formatted)
       self.console.see(tk.END)
       self.console.config(state=tk.DISABLED)

    def start_ahk(self):
       try:
          if getattr(sys, 'frozen', False):
             base_path = os.path.dirname(sys.executable)
          else:
             base_path = os.path.dirname(os.path.abspath(__file__))

          ahk_path = os.path.normpath(os.path.join(base_path, "clipboard_format.ahk"))
          if os.path.exists(ahk_path):
             # Try to find AutoHotkey executable to avoid shell=True
             ahk_exe = None
             for path in [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")]:
                if path:
                   potential_exe = os.path.join(path, "AutoHotkey", "AutoHotkey.exe")
                   if os.path.exists(potential_exe):
                      ahk_exe = potential_exe
                      break
                   potential_v2 = os.path.join(path, "AutoHotkey", "v2", "AutoHotkey64.exe")
                   if os.path.exists(potential_v2):
                      ahk_exe = potential_v2
                      break

             if ahk_exe:
                self.ahk_process = subprocess.Popen([ahk_exe, ahk_path])
             else:
                # Fallback to shell=True if AutoHotkey.exe not found in standard paths
                self.ahk_process = subprocess.Popen([ahk_path], shell=True)
             
             atexit.register(self.stop_ahk)
          else:
             self.log_msg(f"AHK script not found at: {ahk_path}")
       except Exception as e:
          self.log_msg(f"Failed to start AHK: {e}")

    def stop_ahk(self):
       if self.ahk_process:
          try:
             # Try taskkill with /T to kill child processes (important if shell=True was used)
             subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.ahk_process.pid)], 
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
          except Exception:
             try:
                self.ahk_process.terminate()
             except Exception:
                pass
          
          # Forceful cleanup of any remaining instance of this specific script
          try:
             if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
             else:
                base_path = os.path.dirname(os.path.abspath(__file__))
             ahk_path = os.path.normpath(os.path.join(base_path, "clipboard_format.ahk"))
             
             # Kill by window title which typically includes the script path
             # AHK windows usually have titles like "path\to\script.ahk - AutoHotkey v..."
             subprocess.run(['taskkill', '/F', '/FI', f'WINDOWTITLE eq {ahk_path}*'], 
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
          except Exception:
             pass

          self.ahk_process = None

    def quit_app(self):
       self.stop_ahk()
       self.root.destroy()
       sys.exit(0)

    def monitor_clipboard(self):
       recent_clipboard = ""
       while True:
          try:
             current_clipboard = pyperclip.paste().strip()
             if current_clipboard != recent_clipboard:
                recent_clipboard = current_clipboard

                if re.match(r"^https?://commons\.wikimedia\.org/wiki/File:[^\s]+$", current_clipboard):
                   self.log_msg(f"\nURL detected: {current_clipboard}")
                   try:
                      self.log_msg("Extracting metadata...")
                      parser = WikimediaArtworkParser(current_clipboard, self.session)
                      metadata = parser.get_formatted_metadata()
                      pyperclip.copy(metadata)
                      recent_clipboard = metadata
                      self.log_msg("Success! Copied to clipboard.")
                      self.log_msg(f"\n{metadata}\n{'-' * 40}")
                   except Exception as e:
                      self.log_msg(f"Failed to process URL: {e}")
          except Exception as e:
             self.log_msg(f"Clipboard read error: {e}")

          time.sleep(1.0)

    def run(self):
       self.root.mainloop()


if __name__ == "__main__":
    app = ExtractorUI()
    app.run()