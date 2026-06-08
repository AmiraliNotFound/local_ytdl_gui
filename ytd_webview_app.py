from gevent import monkey
monkey.patch_all()

import os
import sys

# Hide console window programmatically if running on Windows
if sys.platform == 'win32':
    import ctypes
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass

import traceback

# If running as packaged executable, redirect stdout/stderr to a log file
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    log_path = os.path.join(exe_dir, "ytd_app.log")
    try:
        log_file = open(log_path, 'w', encoding='utf-8')
        sys.stdout = log_file
        sys.stderr = log_file
    except Exception:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    try:
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)
        
        # Also print to sys.stderr so it goes to our redirected log file
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        if sys.stderr:
            sys.stderr.flush()
            
        with open("crash_log.txt", "w") as f:
            f.write(tb_text)
            
        # Display native Windows MessageBox
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, tb_text, "Python Backend Crash", 0x10) # 0x10 = MB_ICONERROR
    except Exception:
        pass

sys.excepthook = handle_exception
import json
import threading
import urllib.request
import eel
import tkinter as tk
from tkinter import filedialog
from yt_dlp import YoutubeDL

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "output_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
    "quality_preset": "1080p (Best Quality)",
    "video_codec": "Best Available",
    "audio_quality": "192",
    "download_subtitles": False,
    "subtitle_languages": "en",
    "auth_method": "Bypass (Client Emulation)",
    "browser_name": "chrome",
    "cookies_path": "youtube_cookies.txt",
    "proxy_enabled": False,
    "proxy_url": "http://127.0.0.1:8080",
    "node_path": r"C:\Program Files\nodejs",
    "filename_template": "%(title)s.%(ext)s",
    "theme": "Dark"
}

# --- CUSTOM LOGGER FOR WEBVIEW ---
class WebViewLogger:
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def debug(self, msg): 
        pass 
    def info(self, msg): 
        self.log_callback(f"[INFO] {msg}\n")
    def warning(self, msg): 
        self.log_callback(f"[WARNING] {msg}\n")
    def error(self, msg): 
        self.log_callback(f"[ERROR] {msg}\n")


# --- WEBVIEW JAVASCRIPT API ---
class WebviewAPI:
    def __init__(self):
        self.config = self.load_config()
        self.is_downloading = False
        self.video_info = None
        self.setup_environment()

    def setup_environment(self):
        current_dir = os.getcwd()
        paths_to_add = []
        if current_dir not in os.environ.get("PATH", "").split(os.pathsep):
            paths_to_add.append(current_dir)
        
        node_path = self.config.get("node_path", "")
        if node_path and os.path.exists(node_path) and node_path not in os.environ.get("PATH", "").split(os.pathsep):
            paths_to_add.append(node_path)
            
        if paths_to_add:
            os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ.get("PATH", "")

    # Config Management
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except (json.JSONDecodeError, OSError, ValueError):
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def get_initial_config(self):
        eel.set_initial_config(self.config)

    def save_config(self, config):
        self.config = config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        self.setup_environment()
        self.write_log("[INFO] Configuration saved successfully!\n")
        self.get_initial_config()

    def save_theme(self, theme):
        self.config["theme"] = theme
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def reset_config(self):
        self.config = DEFAULT_CONFIG.copy()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        self.setup_environment()
        self.write_log("[INFO] Configuration reset to defaults.\n")
        self.get_initial_config()

    # File / Folder Dialogs
    def choose_directory(self):
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        path = filedialog.askdirectory(parent=root, title="Select Output Directory")
        root.destroy()
        return path

    def choose_cookies_file(self):
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        path = filedialog.askopenfilename(
            parent=root,
            title="Select Cookies File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        root.destroy()
        return path

    # Logger Helper
    def write_log(self, message):
        eel.append_log(message)

    # URL Analyzer
    def analyze_url(self, url, config_from_ui):
        self.config = config_from_ui
        threading.Thread(target=self._execute_analyze, args=(url,), daemon=True).start()

    def _execute_analyze(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'js_runtimes': {'node': {}},
            }
            
            # Apply cookies / auth
            auth_method = self.config.get("auth_method")
            if auth_method == "Browser Cookies (Auto)":
                ydl_opts['cookiesfrombrowser'] = (self.config.get("browser_name", "chrome"),)
            elif auth_method == "Cookie File (Manual)":
                cookies = self.config.get("cookies_path", "")
                if os.path.exists(cookies):
                    ydl_opts['cookiefile'] = cookies
            else:  # Bypass (Client Emulation)
                ydl_opts['extractor_args'] = {
                    'youtube': {
                        'player_client': ['android_vr'],
                    }
                }
            
            # Apply proxy
            if self.config.get("proxy_enabled"):
                ydl_opts['proxy'] = self.config.get("proxy_url")
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Handle playlists
                if 'entries' in info:
                    first_video = next((e for e in info['entries'] if e), None)
                    if first_video:
                        self.video_info = first_video.copy()
                        self.video_info['is_playlist'] = True
                        self.video_info['playlist_title'] = info.get('title', 'Unknown Playlist')
                        self.video_info['playlist_count'] = len([e for e in info['entries'] if e])
                    else:
                        raise Exception("Playlist is empty")
                else:
                    self.video_info = info.copy()
                    self.video_info['is_playlist'] = False
                
                # Prepare metadata for JS preview
                preview_data = {
                    "title": self.video_info.get('title', 'Unknown Title'),
                    "thumbnail": self.video_info.get('thumbnail', ''),
                    "uploader": self.video_info.get('uploader', 'Unknown Channel'),
                    "views": f"{self.video_info.get('view_count', 0):,}" if self.video_info.get('view_count') else "Unknown",
                    "duration": self.video_info.get('duration', 0),
                    "is_playlist": self.video_info['is_playlist'],
                    "playlist_count": self.video_info.get('playlist_count', 0)
                }
                
                # Push back to JS
                eel.update_preview(preview_data)
                self.write_log("[INFO] Video details parsed successfully!\n")
                
        except Exception as e:
            self.write_log(f"[ERROR] Failed to fetch info: {str(e)}\n")
            eel.reset_analyze_btn('Analyze URL')

    # Video Downloader
    def start_download(self, url, config_from_ui):
        if self.is_downloading:
            return
        self.config = config_from_ui
        self.is_downloading = True
        threading.Thread(target=self._execute_download, args=(url,), daemon=True).start()

    def _execute_download(self, url):
        self.write_log(f"\n--- Starting Job: {url} ---\n")
        
        out_dir = self.config["output_dir"]
        if not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
                self.write_log(f"[INFO] Created output directory: {out_dir}\n")
            except OSError as e:
                self.write_log(f"[ERROR] Cannot create output directory: {e}\n")
                self.is_downloading = False
                eel.reset_analyze_btn('Start Download')
                return

        current_dir = os.getcwd()
        quality_preset = self.config["quality_preset"]
        codec_pref = self.config["video_codec"]
        audio_quality = self.config["audio_quality"]
        out_tmpl = os.path.join(out_dir, self.config["filename_template"])
        
        ydl_opts = {
            'outtmpl': out_tmpl,
            'yes_playlist': True,
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': True,
            'js_runtimes': {'node': {}},
            'logger': WebViewLogger(self.write_log),
            'progress_hooks': [self.hook_routing],
            'retries': 20,
            'fragment_retries': 20,
            'retry_sleep_functions': {'http': lambda n: 10 * (n + 1)},
            'sleep_interval': 3,
            'max_sleep_interval': 10,
        }

        # Set ffmpeg location if found
        ffmpeg_path = os.path.join(current_dir, "ffmpeg.exe")
        if os.path.exists(ffmpeg_path):
            ydl_opts['ffmpeg_location'] = current_dir

        # Apply Auth / Cookies
        auth_method = self.config["auth_method"]
        if auth_method == "Browser Cookies (Auto)":
            browser = self.config["browser_name"]
            ydl_opts['cookiesfrombrowser'] = (browser,)
            self.write_log(f"[INFO] Extracting cookies from browser: {browser}\n")
        elif auth_method == "Cookie File (Manual)":
            cookies = self.config["cookies_path"]
            if os.path.exists(cookies):
                ydl_opts['cookiefile'] = cookies
                self.write_log(f"[INFO] Using cookies file: {cookies}\n")
            else:
                self.write_log("[WARNING] Cookie file not found. May fail Bot-Check.\n")
        else:  # Bypass (Client Emulation)
            if 'http_headers' in ydl_opts:
                ydl_opts['http_headers'].pop('User-Agent', None)
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['android_vr'],
                }
            }
            self.write_log("[INFO] Running with no cookies. Emulating Android VR client to bypass bot detection.\n")

        # Apply Proxy
        if self.config.get("proxy_enabled"):
            ydl_opts['proxy'] = self.config["proxy_url"]
            self.write_log(f"Routing through Proxy: {ydl_opts['proxy']}\n")
        
        # Build Format Option
        if "Audio Only" in quality_preset:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality,
            }]
            self.write_log(f"[INFO] Audio-only mode: {audio_quality} kbps MP3\n")
        else:
            format_str = self.build_format_string(quality_preset, codec_pref)
            ydl_opts['format'] = format_str
            ydl_opts['merge_output_format'] = 'mp4'
            self.write_log(f"[INFO] Video mode: {quality_preset} with {codec_pref}\n")
        
        # Subtitle options
        if self.config.get("download_subtitles"):
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            sub_langs = self.config.get("subtitle_languages", "").strip()
            if sub_langs:
                ydl_opts['subtitleslangs'] = [lang.strip() for lang in sub_langs.split(',')]
            self.write_log(f"[INFO] Subtitles enabled: {sub_langs or 'all available'}\n")

        # Download execution
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.write_log("\n[SUCCESS] Download completed successfully!\n")
        except Exception as e:
            self.write_log(f"\n[CRITICAL ERROR] {str(e)}\n")
        finally:
            self.is_downloading = False
            eel.reset_analyze_btn('Analyze URL')
            eel.update_progress(0, 'Current File: Idle')

    def build_format_string(self, quality_preset, codec_pref):
        if "Best Available" in quality_preset:
            height_limit = ""
        elif "4K" in quality_preset:
            height_limit = "[height<=2160]"
        elif "1080p" in quality_preset:
            height_limit = "[height<=1080]"
        elif "720p" in quality_preset:
            height_limit = "[height<=720]"
        elif "480p" in quality_preset:
            height_limit = "[height<=480]"
        else:
            height_limit = "[height<=1080]"
        
        codec_filter = ""
        if "VP9" in codec_pref:
            codec_filter = "[vcodec^=vp9]"
        elif "AV1" in codec_pref:
            codec_filter = "[vcodec^=av01]"
        elif "H.264" in codec_pref:
            codec_filter = "[vcodec^=avc1]"
        elif "H.265" in codec_pref or "HEVC" in codec_pref:
            codec_filter = "[vcodec^=hev1]"
        
        if codec_filter and height_limit:
            format_str = f"bestvideo{height_limit}{codec_filter}+bestaudio/bestvideo{height_limit}+bestaudio/best"
        elif codec_filter:
            format_str = f"bestvideo{codec_filter}+bestaudio/bestvideo+bestaudio/best"
        elif height_limit:
            format_str = f"bestvideo{height_limit}+bestaudio/best"
        else:
            format_str = "bestvideo+bestaudio/best"
        
        return format_str

    # --- PROGRESS HOOKS ---
    def hook_routing(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            down = d.get('downloaded_bytes', 0)
            
            if total > 0:
                percent = down / total
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                status_text = f"Downloading... Speed: {speed}  |  ETA: {eta}"
                eel.update_progress(percent, status_text)
                
        elif d['status'] == 'finished':
            eel.update_progress(1.0, 'File Downloaded, Processing/Merging...')
            
        info = d.get('info_dict', {})
        playlist_index = info.get('playlist_index')
        n_entries = info.get('n_entries') or info.get('playlist_count')
        if playlist_index is not None and n_entries is not None and n_entries > 0:
            eel.update_playlist_progress(playlist_index, n_entries)


# Initialize global API instance
api = WebviewAPI()

@eel.expose
def choose_directory():
    return api.choose_directory()

@eel.expose
def choose_cookies_file():
    return api.choose_cookies_file()

@eel.expose
def reset_config():
    return api.reset_config()

@eel.expose
def get_initial_config():
    return api.get_initial_config()

@eel.expose
def save_theme(theme):
    return api.save_theme(theme)

@eel.expose
def analyze_url(url, config_from_ui):
    return api.analyze_url(url, config_from_ui)

@eel.expose
def start_download(url, config_from_ui):
    return api.start_download(url, config_from_ui)

@eel.expose
def save_config(config):
    return api.save_config(config)


if __name__ == "__main__":
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        web_dir = os.path.join(sys._MEIPASS, 'web')
    else:
        web_dir = 'web'
        
    eel.init(web_dir)
    
    # Try starting Chrome, fallback to Edge or default
    try:
        eel.start('index.html', host='127.0.0.1', mode='chrome', size=(950, 920))
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception:
        try:
            eel.start('index.html', host='127.0.0.1', mode='edge', size=(950, 920))
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception:
            try:
                eel.start('index.html', host='127.0.0.1', mode='default', size=(950, 920))
            except (SystemExit, KeyboardInterrupt):
                raise
