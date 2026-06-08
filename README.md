# YouTube Downloader Pro

A modern, high-performance desktop application built with a web-based **HTML/CSS/JS frontend**, **Python (Eel) backend**, and the **yt-dlp** engine. It is designed for downloading YouTube videos, audio, and playlists in maximum quality (up to 1080p, 4K, and 8K).

It features a beautiful, glassmorphic UI dashboard with built-in theme support (Dark/Light) and advanced authentication bypass methods to prevent YouTube's "Sign in to confirm you're not a bot" checks.

---

## 🌟 Key Features

* **High-Quality Video & Audio**: Supports downloading separate best video and best audio formats, merging them automatically with FFmpeg (up to 1080p, 4K, 8K, and 60 FPS).
* **Bypass YouTube Bot Check (Cookie-Free)**:
  * **Bypass (Client Emulation)**: Emulates official **Android VR** player endpoints. Solves decryption challenges natively using Node.js without requiring login or cookie files.
  * **Browser Cookies (Auto)**: Automatically extracts active session cookies from Chrome, Edge, Firefox, Brave, Safari, Opera, or Vivaldi.
  * **Cookie File (Manual)**: Allows loading traditional browser-exported `.txt` cookie files.
* **Format & Codec Selection**: Fine-tune downloads by choosing your resolution presets and video codecs (VP9, AV1, H.264, or H.265/HEVC).
* **Stunning Web-Based Desktop GUI**: Built using clean HTML, modern responsive Vanilla CSS (glassmorphic UI, smooth transitions, micro-animations), and native-like desktop window wrapping via `Eel`.
* **CLI Utility**: Includes `download_inline.py` for headless or command-line operation.
* **Standalone Windowless Executable**: Packages into a clean C++ launcher (`ytd_webview_app.exe`) that spawns a hidden python backend (`ytd_webview_backend.exe`), completely preventing flashing console windows on startup.

---

## 🛠️ Prerequisites

To run this application from source, make sure you have the following installed on your system:

1. **Python 3.10+**
2. **Node.js** (Used by `yt-dlp` as a JavaScript runtime to solve signature challenges).
3. **FFmpeg** (Required to merge high-quality separate audio and video streams). Place `ffmpeg.exe` and `ffprobe.exe` in the application directory or add them to your system PATH.

---

## 🚀 Getting Started

### 1. Installation
Clone the repository and install the required Python dependencies:

```bash
pip install -r requirements.txt
```
*(Dependencies: `eel`, `gevent`, `yt-dlp`)*

### 2. Running the GUI Application
Launch the main dashboard interface:

```bash
python ytd_webview_app.py
```

### 3. Packaging into Standalone Executables
To build the windowless executable launcher and hidden backend:

#### Prerequisites for Compiling Launcher:
Make sure you have a C++ compiler (like `g++` / MinGW) and `windres` installed on your system PATH.

#### Compilation Steps:
1. **Compile the resource file (for the custom icon):**
   ```bash
   windres resource.rc -O coff -o resource.res
   ```
2. **Compile the windowless C++ launcher:**
   ```bash
   g++ -O3 ytd_launcher.cpp resource.res -o dist/ytd_webview_app.exe -mwindows
   ```
3. **Compile the Python backend using PyInstaller:**
   ```bash
   pyinstaller ytd_webview_backend.spec --clean -y
   ```

The compiled binaries will be available inside the `dist/` directory. Simply run `ytd_webview_app.exe` to launch the application completely windowless.

### 4. Running the CLI Tool
Use the helper script to download directly from the terminal:

```bash
# Bypassing bot detection using Android VR client emulation (no cookies needed)
python download_inline.py <youtube-url> --auth bypass

# Extracting cookies automatically from Google Chrome
python download_inline.py <youtube-url> --auth browser --browser chrome

# Using a manually exported cookie file
python download_inline.py <youtube-url> --auth manual --cookies path/to/cookies.txt
```

---

## ⚙️ Configuration & Settings

Inside the settings panels of the GUI, you can customize:
* **Output Folder**: Destination for downloaded files.
* **Authentication Method**: Configure client emulation, auto browser extraction, or manual cookie paths.
* **Theme Options**: Dynamically switch the theme between Dark and Light appearance modes.
* **Subtitles**: Enable/disable subtitles and specify preferred language codes (e.g., `en,es,fr`).
* **Proxy settings**: Route download traffic through a custom HTTP/SOCKS proxy server.

---

## 📝 Disclaimer

This project is for personal, educational use only. Please respect YouTube's Terms of Service and download videos only when you have permission from the copyright owner.
