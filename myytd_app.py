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

import json
import threading
import urllib.request
from io import BytesIO
import customtkinter as ctk
from tkinter import filedialog
from yt_dlp import YoutubeDL
import ytd_core


# Try to import PIL for thumbnail support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# --- INITIALIZATION & CONFIG ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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

# --- CUSTOM LOGGER FOR GUI TEXTBOX ---
class GUILogger:
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


# --- MAIN APP CLASS ---
class YTDlpSlickApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro - Enhanced Quality")
        self.geometry("950x980")
        self.config = self.load_config()
        
        # Set loaded appearance mode (Dark/Light/System)
        ctk.set_appearance_mode(self.config.get("theme", "Dark"))
        
        self.is_downloading = False
        self.video_info = None

        self.setup_environment()
        self.build_ui()
        self.apply_config_to_ui()

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

    # --- UI LAYOUT ---
    def build_ui(self):
        # Top Bar (Title & Theme Toggle)
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=15, pady=(15, 0))
        
        self.logo_label = ctk.CTkLabel(
            self.top_bar, 
            text="YouTube Downloader Pro", 
            font=("Arial", 22, "bold")
        )
        self.logo_label.pack(side="left", padx=10, pady=5)

        # Version badge
        self.version_badge = ctk.CTkLabel(
            self.top_bar,
            text="v1.1.0",
            font=("Arial", 11),
            text_color="gray"
        )
        self.version_badge.pack(side="left", padx=(0, 10), pady=(8, 0))

        # GitHub Button
        self.github_btn = ctk.CTkButton(
            self.top_bar,
            text="GitHub 🌐",
            width=80,
            command=self.open_github_link,
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray30"),
            text_color=("black", "white"),
            hover_color=("gray80", "gray20")
        )
        self.github_btn.pack(side="left", padx=5, pady=5)
        
        # Theme Selector
        self.theme_var = ctk.StringVar(value=self.config.get("theme", "Dark"))
        self.theme_dropdown = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.theme_var,
            values=["Dark", "Light", "System"],
            command=self.change_appearance_mode,
            width=100
        )
        self.theme_dropdown.pack(side="right", padx=10, pady=5)
        
        self.theme_label = ctk.CTkLabel(self.top_bar, text="Theme:", font=("Arial", 12))
        self.theme_label.pack(side="right", padx=(10, 5), pady=5)

        # Create a main scrollable frame (no duplicate text label, cleaner look)
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # 1. URL Input Area
        self.url_frame = ctk.CTkFrame(self.scroll_frame)
        self.url_frame.pack(pady=15, padx=20, fill="x")
        
        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text="Paste YouTube URL here...", font=("Arial", 14))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        self.action_btn = ctk.CTkButton(self.url_frame, text="Analyze URL", font=("Arial", 14, "bold"), command=self.handle_action)
        self.action_btn.pack(side="right", padx=(0, 10), pady=10)

        # 2. Video Info Preview Panel (Enlarged)
        self.info_frame = ctk.CTkFrame(self.scroll_frame)
        # Initially hidden; shown after video info is fetched
        
        self.thumb_label = ctk.CTkLabel(self.info_frame, text="")
        self.thumb_label.pack(side="top", padx=10, pady=10)
        
        self.info_text_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.info_text_frame.pack(side="top", fill="x", padx=20, pady=(0, 10))
        
        self.info_title = ctk.CTkLabel(self.info_text_frame, text="", font=("Arial", 16, "bold"), wraplength=800)
        self.info_title.pack(pady=(0, 5))
        
        self.info_details = ctk.CTkLabel(self.info_text_frame, text="", font=("Arial", 12), justify="center")
        self.info_details.pack()

        # 3. Settings Tabs
        self.tabs = ctk.CTkTabview(self.scroll_frame)
        self.tabs.pack(pady=10, padx=20, fill="x")
        
        tab_quality = self.tabs.add("Quality & Format")
        tab_basic = self.tabs.add("Output Settings")
        tab_network = self.tabs.add("Network & Engine")
        
        # --- TAB: QUALITY & FORMAT ---
        # Quality Preset
        ctk.CTkLabel(tab_quality, text="Quality Preset:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.quality_var = ctk.StringVar()
        self.quality_dropdown = ctk.CTkOptionMenu(
            tab_quality, 
            variable=self.quality_var, 
            values=["Best Available (No Limit)", "4K (2160p)", "1080p (Best Quality)", "720p", "480p", "Audio Only (Best)"],
            width=250
        )
        self.quality_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Video Codec
        ctk.CTkLabel(tab_quality, text="Video Codec:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.codec_var = ctk.StringVar()
        self.codec_dropdown = ctk.CTkOptionMenu(
            tab_quality,
            variable=self.codec_var,
            values=["Best Available", "VP9 (Recommended)", "AV1 (Efficient)", "H.264 (Compatible)", "H.265/HEVC"],
            width=250
        )
        self.codec_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        # Audio Quality
        ctk.CTkLabel(tab_quality, text="Audio Quality:", font=("Arial", 12, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.audio_var = ctk.StringVar()
        self.audio_dropdown = ctk.CTkOptionMenu(
            tab_quality,
            variable=self.audio_var,
            values=["320 kbps (Best)", "256 kbps", "192 kbps", "128 kbps"],
            width=250
        )
        self.audio_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        # Subtitle Options
        ctk.CTkLabel(tab_quality, text="Subtitles:", font=("Arial", 12, "bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.subtitle_switch_var = ctk.BooleanVar()
        self.subtitle_switch = ctk.CTkSwitch(tab_quality, text="Download Subtitles", variable=self.subtitle_switch_var)
        self.subtitle_switch.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(tab_quality, text="Subtitle Languages:", font=("Arial", 11)).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.subtitle_entry = ctk.CTkEntry(tab_quality, placeholder_text="en,es,fr (comma-separated)", width=250)
        self.subtitle_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        
        # Info label
        info_text = "💡 Tip: 'Best Available' automatically selects the highest quality format.\nVP9 offers better quality at smaller file sizes than H.264."
        ctk.CTkLabel(tab_quality, text=info_text, font=("Arial", 10), text_color="gray", justify="left").grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # --- TAB: BASIC ---
        # Output Dir
        self.dir_btn = ctk.CTkButton(tab_basic, text="Output Folder", command=self.browse_dir, width=120)
        self.dir_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.dir_entry = ctk.CTkEntry(tab_basic, width=400)
        self.dir_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")

        # Auth Method
        ctk.CTkLabel(tab_basic, text="Auth Method:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.auth_var = ctk.StringVar()
        self.auth_dropdown = ctk.CTkOptionMenu(
            tab_basic,
            variable=self.auth_var,
            values=["Bypass (Client Emulation)", "Browser Cookies (Auto)", "Cookie File (Manual)"],
            command=self.update_auth_layout,
            width=250
        )
        self.auth_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Select Browser (Only shown for Browser Cookies)
        self.browser_label = ctk.CTkLabel(tab_basic, text="Select Browser:")
        self.browser_var = ctk.StringVar()
        self.browser_dropdown = ctk.CTkOptionMenu(
            tab_basic,
            variable=self.browser_var,
            values=["chrome", "firefox", "edge", "brave", "opera", "vivaldi", "safari"],
            width=250
        )

        # Cookies Path (Only shown for Cookie File)
        self.cookie_btn = ctk.CTkButton(tab_basic, text="Cookies File", command=self.browse_cookies, width=120)
        self.cookie_entry = ctk.CTkEntry(tab_basic, width=400)
        
        # Filename Template
        self.template_label = ctk.CTkLabel(tab_basic, text="File Template:")
        self.template_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.template_entry = ctk.CTkEntry(tab_basic, width=400)
        self.template_entry.grid(row=4, column=1, padx=10, pady=10, sticky="we")
        
        # --- TAB: NETWORK & ENGINE ---
        # Proxy
        self.proxy_switch_var = ctk.BooleanVar()
        self.proxy_switch = ctk.CTkSwitch(tab_network, text="Enable Proxy", variable=self.proxy_switch_var)
        self.proxy_switch.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(tab_network, text="Proxy URL:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.proxy_entry = ctk.CTkEntry(tab_network, width=400)
        self.proxy_entry.grid(row=1, column=1, padx=10, pady=10, sticky="we")

        # Node Path
        ctk.CTkLabel(tab_network, text="Node.js Path:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.node_entry = ctk.CTkEntry(tab_network, width=400)
        self.node_entry.grid(row=2, column=1, padx=10, pady=10, sticky="we")

        # Buttons
        btn_frame = ctk.CTkFrame(tab_network, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ctk.CTkButton(btn_frame, text="Save Defaults", command=self.save_config).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Reset to Defaults", fg_color="#8b0000", hover_color="#5c0000", command=self.reset_config).pack(side="left", padx=10)

        # 4. Progress Section
        self.prog_frame = ctk.CTkFrame(self.scroll_frame)
        self.prog_frame.pack(pady=20, padx=20, fill="x")

        # Current File Bar
        self.file_lbl = ctk.CTkLabel(self.prog_frame, text="Current File: Ready", font=("Arial", 13, "bold"))
        self.file_lbl.pack(anchor="w", padx=20, pady=(15, 5))
        self.file_bar = ctk.CTkProgressBar(self.prog_frame, height=12)
        self.file_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.file_bar.set(0)

        # Playlist Bar
        self.play_lbl = ctk.CTkLabel(self.prog_frame, text="Playlist Progress: N/A", font=("Arial", 12))
        self.play_lbl.pack(anchor="w", padx=20, pady=(5, 5))
        self.play_bar = ctk.CTkProgressBar(self.prog_frame, height=10)
        self.play_bar.pack(fill="x", padx=20, pady=(0, 20))
        self.play_bar.set(0)

        # 5. Log Output
        self.log_frame = ctk.CTkFrame(self.scroll_frame)
        self.log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(self.log_frame, text="Download Log", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.log_box = ctk.CTkTextbox(self.log_frame, height=200, font=("Consolas", 10))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def handle_action(self):
        url = self.url_entry.get().strip()
        if not url:
            self.write_log("[ERROR] Please paste a URL first.\n")
            return
        
        current_text = self.action_btn.cget("text")
        self.write_log(f"[DEBUG] Button clicked. Current state: {current_text}\n")
        
        if current_text == "Analyze URL":
            self.action_btn.configure(state="disabled", text="Analyzing...")
            self.write_log(f"\n[INFO] Fetching video info for: {url}\n")
            
            # Read UI elements before entering the thread
            config = {
                "auth_method": self.auth_var.get(),
                "browser_name": self.browser_var.get(),
                "cookies": self.cookie_entry.get(),
                "use_proxy": self.proxy_switch_var.get(),
                "proxy_url": self.proxy_entry.get()
            }
            threading.Thread(target=self.fetch_video_info, args=(url, config), daemon=True).start()
        elif current_text == "Start Download":
            self.start_download_thread()
        else:
            self.write_log(f"[WARNING] Unknown button state: {current_text}\n")

    def fetch_video_info(self, url, config):
        try:
            core_config = self.config.copy()
            core_config.update({
                "auth_method": config["auth_method"],
                "browser_name": config["browser_name"],
                "cookies_path": config["cookies"],
                "proxy_enabled": config["use_proxy"],
                "proxy_url": config["proxy_url"]
            })
            
            ytd_core.setup_environment(core_config)
            ydl_opts = ytd_core.get_ytdl_opts(core_config, is_download=False)
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Handle playlists
                if 'entries' in info:
                    first_video = next((e for e in info['entries'] if e), None)
                    if first_video:
                        playlist_title = info.get('title', 'Unknown Playlist')
                        playlist_count = len([e for e in info['entries'] if e])
                        self.video_info = first_video
                        self.video_info['is_playlist'] = True
                        self.video_info['playlist_title'] = playlist_title
                        self.video_info['playlist_count'] = playlist_count
                    else:
                        raise Exception("Playlist is empty")
                else:
                    self.video_info = info
                    self.video_info['is_playlist'] = False
                
                self.after(0, self.display_video_info)
                
        except Exception as e:
            self.after(0, lambda: self.write_log(f"[ERROR] Failed to fetch info: {str(e)}\n"))
            self.after(0, lambda: self.action_btn.configure(state="normal", text="Analyze URL"))
    
    def display_video_info(self):
        if not self.video_info:
            return
        
        # Show the info frame
        self.info_frame.pack(pady=10, padx=20, fill="x", after=self.url_frame)
        
        # Display title
        title = self.video_info.get('title', 'Unknown Title')
        if self.video_info.get('is_playlist'):
            title = f"📁 {self.video_info['playlist_title']} ({self.video_info['playlist_count']} videos)\nFirst video: {title}"
        self.info_title.configure(text=title)
        
        # Display details
        uploader = self.video_info.get('uploader', 'Unknown')
        duration = self.video_info.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
        view_count = self.video_info.get('view_count', 0)
        view_str = f"{view_count:,}" if view_count else "Unknown"
        
        details = f"👤 {uploader}  •  ⏱️ {duration_str}  •  👁️ {view_str}"
        self.info_details.configure(text=details)
        
        # Load thumbnail (Larger)
        if PIL_AVAILABLE:
            thumbnail_url = self.video_info.get('thumbnail')
            if thumbnail_url:
                threading.Thread(target=self.load_thumbnail, args=(thumbnail_url,), daemon=True).start()
            else:
                self.thumb_label.configure(text="📹\nNo Thumbnail", font=("Arial", 20))
        else:
            self.thumb_label.configure(text="📹", font=("Arial", 60))
        
        # Change button to Download
        self.action_btn.configure(state="normal", text="Start Download", fg_color="#2b719e", hover_color="#1a4d6b")
        self.write_log("[INFO] Video info loaded successfully! Click 'Start Download' to begin.\n")
    
    def load_thumbnail(self, url):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                img_data = response.read()
            
            image = Image.open(BytesIO(img_data))
            # Larger thumbnail: 480x270 (16:9)
            image.thumbnail((480, 270))
            photo = ImageTk.PhotoImage(image)
            
            def _set_thumbnail(p=photo):
                self.thumb_label.configure(image=p, text="")
                self.thumb_label.image = p  # Keep reference to prevent GC
            
            self.after(0, _set_thumbnail)
        except Exception as e:
            self.after(0, lambda: self.thumb_label.configure(text="📹\nThumbnail Load Failed", font=("Arial", 12)))

    # --- CONFIG MANAGEMENT ---
    def load_config(self):
        return ytd_core.load_config()
    
    def save_config(self):
        self.config = {
            "output_dir": self.dir_entry.get(),
            "quality_preset": self.quality_var.get(),
            "video_codec": self.codec_var.get(),
            "audio_quality": self.audio_var.get().split()[0],  # Extract number
            "download_subtitles": self.subtitle_switch_var.get(),
            "subtitle_languages": self.subtitle_entry.get(),
            "auth_method": self.auth_var.get(),
            "browser_name": self.browser_var.get(),
            "cookies_path": self.cookie_entry.get(),
            "proxy_enabled": self.proxy_switch_var.get(),
            "proxy_url": self.proxy_entry.get(),
            "node_path": self.node_entry.get(),
            "filename_template": self.template_entry.get(),
            "theme": self.theme_var.get()
        }
        ytd_core.save_config(self.config)
        self.write_log("[INFO] Configuration saved successfully!\n")
    
    def reset_config(self):
        self.config = ytd_core.DEFAULT_CONFIG.copy()
        self.apply_config_to_ui()
        self.write_log("[INFO] Configuration reset to defaults.\n")
    
    def apply_config_to_ui(self):
        self.dir_entry.delete(0, 'end'); self.dir_entry.insert(0, self.config["output_dir"])
        self.quality_var.set(self.config["quality_preset"])
        self.codec_var.set(self.config["video_codec"])
        audio_map = {"320": "320 kbps (Best)", "256": "256 kbps", "192": "192 kbps", "128": "128 kbps"}
        self.audio_var.set(audio_map.get(self.config['audio_quality'], "192 kbps"))
        self.subtitle_switch_var.set(self.config["download_subtitles"])
        self.subtitle_entry.delete(0, 'end'); self.subtitle_entry.insert(0, self.config["subtitle_languages"])
        self.auth_var.set(self.config.get("auth_method", "Bypass (Client Emulation)"))
        self.browser_var.set(self.config.get("browser_name", "chrome"))
        self.cookie_entry.delete(0, 'end'); self.cookie_entry.insert(0, self.config["cookies_path"])
        self.proxy_switch_var.set(self.config["proxy_enabled"])
        self.proxy_entry.delete(0, 'end'); self.proxy_entry.insert(0, self.config["proxy_url"])
        self.node_entry.delete(0, 'end'); self.node_entry.insert(0, self.config["node_path"])
        self.template_entry.delete(0, 'end'); self.template_entry.insert(0, self.config["filename_template"])
        self.theme_var.set(self.config.get("theme", "Dark"))
        self.update_auth_layout()

    def update_auth_layout(self, val=None):
        method = self.auth_var.get()
        if method == "Bypass (Client Emulation)":
            self.browser_label.grid_remove()
            self.browser_dropdown.grid_remove()
            self.cookie_btn.grid_remove()
            self.cookie_entry.grid_remove()
        elif method == "Browser Cookies (Auto)":
            self.browser_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
            self.browser_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky="w")
            self.cookie_btn.grid_remove()
            self.cookie_entry.grid_remove()
        elif method == "Cookie File (Manual)":
            self.browser_label.grid_remove()
            self.browser_dropdown.grid_remove()
            self.cookie_btn.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            self.cookie_entry.grid(row=3, column=1, padx=10, pady=10, sticky="we")

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def open_github_link(self):
        import webbrowser
        webbrowser.open("https://github.com/AmiraliNotFound/local_ytdl_gui")

    # --- FILE DIALOGS ---
    def browse_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dir_entry.delete(0, 'end')
            self.dir_entry.insert(0, folder)
    
    def browse_cookies(self):
        file = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file:
            self.cookie_entry.delete(0, 'end')
            self.cookie_entry.insert(0, file)

    # --- LOGGING ---
    def write_log(self, message):
        self.after(0, self._safe_write_log, message)

    def _safe_write_log(self, message):
        self.log_box.insert("end", message)
        self.log_box.see("end")

    # --- DOWNLOAD LOGIC ---
    def start_download_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            self.write_log("[ERROR] Please paste a valid YouTube URL first.\n")
            return
        
        if self.is_downloading: return
        self.is_downloading = True
        self.action_btn.configure(state="disabled", text="Downloading...")
        
        download_config = {
            "quality_preset": self.quality_var.get(),
            "codec_pref": self.codec_var.get(),
            "audio_quality": self.audio_var.get().split()[0],
            "out_dir": self.dir_entry.get(),
            "template": self.template_entry.get(),
            "auth_method": self.auth_var.get(),
            "browser_name": self.browser_var.get(),
            "cookies": self.cookie_entry.get(),
            "use_proxy": self.proxy_switch_var.get(),
            "proxy_url": self.proxy_entry.get(),
            "dl_subs": self.subtitle_switch_var.get(),
            "sub_langs": self.subtitle_entry.get().strip()
        }
        
        threading.Thread(target=self.execute_download, args=(url, download_config), daemon=True).start()

    def execute_download(self, url, config):
        self.write_log(f"\n--- Starting Job: {url} ---\n")
        
        out_dir = config["out_dir"]
        if not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
                self.write_log(f"[INFO] Created output directory: {out_dir}\n")
            except OSError as e:
                self.write_log(f"[ERROR] Cannot create output directory: {e}\n")
                self.is_downloading = False
                self.after(0, lambda: self.action_btn.configure(state="normal", text="Start Download"))
                return
        
        core_config = self.config.copy()
        core_config.update({
            "output_dir": config["out_dir"],
            "quality_preset": config["quality_preset"],
            "video_codec": config["codec_pref"],
            "audio_quality": config["audio_quality"],
            "download_subtitles": config["dl_subs"],
            "subtitle_languages": config["sub_langs"],
            "auth_method": config["auth_method"],
            "browser_name": config["browser_name"],
            "cookies_path": config["cookies"],
            "proxy_enabled": config["use_proxy"],
            "proxy_url": config["proxy_url"],
            "filename_template": config["template"]
        })
        
        ytd_core.setup_environment(core_config)
        
        ydl_opts = ytd_core.get_ytdl_opts(
            core_config,
            is_download=True,
            progress_hooks=[self.hook_routing],
            logger=GUILogger(self.write_log)
        )
        
        if core_config["auth_method"] != "Bypass (Client Emulation)":
            ydl_opts['http_headers'] = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
            self.write_log("[INFO] Using browser agent for browser extraction / manual cookies.\n")
        else:
            self.write_log("[INFO] Running with no cookies. Emulating Android VR client to bypass bot detection.\n")

        if core_config["proxy_enabled"]:
            self.write_log(f"Routing through Proxy: {ydl_opts.get('proxy')}\n")
            
        if "Audio Only" in config["quality_preset"]:
            self.write_log(f"[INFO] Audio-only mode: {config['audio_quality']} kbps MP3\n")
        else:
            self.write_log(f"[INFO] Video mode: {config['quality_preset']} with {config['codec_pref']}\n")

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.write_log("\n[SUCCESS] Download completed successfully!\n")
        except Exception as e:
            self.write_log(f"\n[CRITICAL ERROR] {str(e)}\n")
        finally:
            self.is_downloading = False
            self.after(0, lambda: self.action_btn.configure(state="normal", text="Analyze URL", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#367E96", "#144870"]))
            self.after(0, lambda: self.file_lbl.configure(text="Current File: Idle"))
            self.after(0, lambda: self.file_bar.set(0))

    # --- LIVE HOOK UPDATES ---
    def hook_routing(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            down = d.get('downloaded_bytes', 0)
            
            if total > 0:
                percent = down / total
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                lbl_text = f"Downloading: {percent * 100:.1f}%  |  Speed: {speed}  |  ETA: {eta}"
                self.after(0, self.update_bars, percent, lbl_text)
                
        elif d['status'] == 'finished':
            self.after(0, self.update_bars, 1.0, "File Downloaded, Processing/Merging...")
            
        info = d.get('info_dict', {})
        playlist_index = info.get('playlist_index')
        n_entries = info.get('n_entries') or info.get('playlist_count')
        if playlist_index is not None and n_entries is not None and n_entries > 0:
            self.after(0, self.update_playlist, playlist_index, n_entries)

    def update_bars(self, file_percent, file_text):
        self.file_bar.set(file_percent)
        self.file_lbl.configure(text=file_text)

    def update_playlist(self, current, total):
        self.play_bar.set(current / total)
        self.play_lbl.configure(text=f"Playlist Progress: Video {current} of {total}")


if __name__ == "__main__":
    app = YTDlpSlickApp()
    app.mainloop()

