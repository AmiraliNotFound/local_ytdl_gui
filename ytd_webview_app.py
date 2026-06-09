from gevent import monkey
monkey.patch_all(dns=False)

import os
import sys

# Support dynamic updates of yt-dlp by prioritizing 'updates' directory in path
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
updates_dir = os.path.join(app_dir, "updates")
if os.path.exists(updates_dir) and updates_dir not in sys.path:
    sys.path.insert(0, updates_dir)

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

# Unbuffered logging system
log_file_handle = None
try:
    log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    log_path = os.path.join(log_dir, "ytd_app.log")
    log_file_handle = open(log_path, 'w', encoding='utf-8', buffering=1)
except Exception:
    pass

def log_debug(msg):
    formatted = f"{msg}\n"
    if log_file_handle:
        try:
            log_file_handle.write(formatted)
            log_file_handle.flush()
        except Exception:
            pass
    try:
        sys.__stdout__.write(formatted)
        sys.__stdout__.flush()
    except Exception:
        pass

# Redirect stdout/stderr to log_debug writes
class LogStream:
    def __init__(self, is_stderr=False):
        self.is_stderr = is_stderr
    def write(self, data):
        if data.strip():
            log_debug(f"[{'STDERR' if self.is_stderr else 'STDOUT'}] {data.strip()}")
    def flush(self):
        if log_file_handle:
            try:
                log_file_handle.flush()
            except Exception:
                pass

sys.stdout = LogStream(is_stderr=False)
sys.stderr = LogStream(is_stderr=True)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    try:
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)
        log_debug(f"[CRASH] Uncaught exception:\n{tb_text}")
        
        crash_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(), "crash_log.txt")
        with open(crash_path, "w") as f:
            f.write(tb_text)
            
        # Display native Windows MessageBox
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, tb_text, "Python Backend Crash", 0x10) # 0x10 = MB_ICONERROR
    except Exception:
        pass

sys.excepthook = handle_exception
import json
import urllib.request
import eel
import tkinter as tk
from tkinter import filedialog
from yt_dlp import YoutubeDL
import ytd_core

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
        ytd_core.setup_environment(self.config)

    # Config Management
    def load_config(self):
        return ytd_core.load_config()

    def get_initial_config(self):
        eel.set_initial_config(self.config)

    def save_config(self, config):
        self.config = config
        ytd_core.save_config(self.config)
        self.setup_environment()
        self.write_log("[INFO] Configuration saved successfully!\n")
        self.get_initial_config()

    def save_theme(self, theme):
        self.config["theme"] = theme
        ytd_core.save_config(self.config)

    def reset_config(self):
        self.config = ytd_core.DEFAULT_CONFIG.copy()
        ytd_core.save_config(self.config)
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
        log_debug(f"[APP_LOG] {message.strip()}")
        try:
            eel.append_log(message)
        except Exception as e:
            log_debug(f"[WARN] Failed to write log to Eel: {e}")

    # URL Analyzer
    def analyze_url(self, url, config_from_ui):
        log_debug(f"[API] analyze_url called for URL: {url}")
        self.config = config_from_ui
        import gevent
        gevent.spawn(self._execute_analyze, url)

    def _execute_analyze(self, url):
        log_debug(f"[API] _execute_analyze thread started for URL: {url}")
        try:
            info = ytd_core.extract_detailed_info(url, self.config)
            log_debug(f"[API] Pushing detailed preview details to JS: {info}")
            eel.update_preview(info)
            self.write_log("[INFO] Video details parsed successfully!\n")
        except Exception as e:
            log_debug(f"[API_ERROR] Exception in _execute_analyze: {traceback.format_exc()}")
            self.write_log(f"[ERROR] Failed to fetch info: {str(e)}\n")
            eel.reset_analyze_btn('Analyze URL')

    def update_engine(self):
        log_debug("[API] update_engine called")
        import gevent
        gevent.spawn(self._execute_update_engine)

    def _execute_update_engine(self):
        self.write_log("\n--- Checking for Engine Updates ---\n")
        try:
            latest_version = ytd_core.update_yt_dlp_engine()
            self.write_log(f"[SUCCESS] yt-dlp updated to version: {latest_version}!\n")
            eel.engine_update_status(True, latest_version)
        except Exception as e:
            log_debug(f"[API_ERROR] Exception in _execute_update_engine: {traceback.format_exc()}")
            self.write_log(f"[ERROR] Engine update failed: {str(e)}\n")
            eel.engine_update_status(False, str(e))

    # Video Downloader
    def start_download(self, url, config_from_ui):
        if self.is_downloading:
            return
        self.config = config_from_ui
        self.is_downloading = True
        import gevent
        gevent.spawn(self._execute_download, url)

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

        ytd_core.setup_environment(self.config)
        
        ydl_opts = ytd_core.get_ytdl_opts(
            self.config,
            is_download=True,
            progress_hooks=[self.hook_routing],
            logger=WebViewLogger(self.write_log)
        )

        if self.config["auth_method"] != "Bypass (Client Emulation)":
            ydl_opts['http_headers'] = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
            self.write_log("[INFO] Using browser agent for browser extraction / manual cookies.\n")
        else:
            self.write_log("[INFO] Running with no cookies. Emulating Android VR client to bypass bot detection.\n")

        if self.config.get("proxy_enabled"):
            self.write_log(f"Routing through Proxy: {ydl_opts.get('proxy')}\n")
        
        if "Audio Only" in self.config["quality_preset"]:
            self.write_log(f"[INFO] Audio-only mode: {self.config['audio_quality']} kbps MP3\n")
        else:
            self.write_log(f"[INFO] Video mode: {self.config['quality_preset']} with {self.config['video_codec']}\n")

        # Download execution
        try:
            log_debug("[API] Initiating download with YoutubeDL...")
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            log_debug("[API] Download completed successfully.")
            self.write_log("\n[SUCCESS] Download completed successfully!\n")
        except Exception as e:
            log_debug(f"[API_ERROR] Exception in _execute_download: {traceback.format_exc()}")
            self.write_log(f"\n[CRITICAL ERROR] {str(e)}\n")
        finally:
            self.is_downloading = False
            eel.reset_analyze_btn('Analyze URL')
            eel.update_progress(0, 'Current File: Idle')

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

@eel.expose
def js_log(message):
    log_debug(message)

@eel.expose
def update_engine():
    return api.update_engine()

@eel.expose
def open_link(url):
    import webbrowser
    log_debug(f"[API] Opening external link in system browser: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        log_debug(f"[API_ERROR] Failed to open external link: {e}")


if __name__ == "__main__":
    log_debug("Backend main startup initiated.")
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        web_dir = os.path.join(sys._MEIPASS, 'web')
        log_debug(f"Packaged executable context. sys._MEIPASS: {sys._MEIPASS}, web_dir: {web_dir}")
    else:
        web_dir = 'web'
        log_debug(f"Standard python context. web_dir: {web_dir}")
        
    log_debug(f"Initializing Eel with web_dir: {web_dir}")
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
