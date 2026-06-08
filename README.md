# YouTube Downloader Pro

A modern, high-performance desktop application built with a web-based **HTML/CSS/JS frontend**, **Python (pywebview) backend**, and the **yt-dlp** engine. It is designed for downloading YouTube videos, audio, and playlists in maximum quality (up to 1080p, 4K, and 8K).

It features a beautiful, glassmorphic UI dashboard with built-in theme support (Dark/Light) and advanced authentication bypass methods to prevent YouTube's "Sign in to confirm you're not a bot" checks.

---

## 🌟 Key Features

* **High-Quality Video & Audio**: Supports downloading separate best video and best audio formats, merging them automatically with FFmpeg (up to 1080p, 4K, 8K, and 60 FPS).
* **Bypass YouTube Bot Check (Cookie-Free)**:
  * **Bypass (Client Emulation)**: Emulates official **Android VR** player endpoints. Solves decryption challenges natively using Node.js without requiring login or cookie files.
  * **Browser Cookies (Auto)**: Automatically extracts active session cookies from Chrome, Edge, Firefox, Brave, Safari, Opera, or Vivaldi.
  * **Cookie File (Manual)**: Allows loading traditional browser-exported `.txt` cookie files.
* **Format & Codec Selection**: Fine-tune downloads by choosing your resolution presets and video codecs (VP9, AV1, H.264, or H.265/HEVC).
* **Stunning Web-Based Desktop GUI**: Built using clean HTML, modern responsive Vanilla CSS (glassmorphism, smooth animations), and native-like window wrapping via `pywebview`.
* **CLI Utility**: Includes `download_inline.py` for headless or command-line operation.
* **Standalone Executable**: Packages into a single self-contained `.exe` file for easy deployment.

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
*(Dependencies: `pywebview`, `yt-dlp`)*

### 2. Running the GUI Application
Launch the main dashboard interface:

```bash
python ytd_webview_app.py
```

### 3. Packaging into a Standalone Executable (.exe)
You can compile the application into a single executable that runs on other computers without requiring a Python environment or pip packages:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --clean --onefile --noconsole --add-data "web;web" ytd_webview_app.py
```
Once completed, the single self-contained executable will be generated inside the `dist/` folder:
* **`dist/ytd_webview_app.exe`**

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

This project is for personal, educational use only. Please respect YouTube's Terms of Service and only download videos when you have permission from the copyright owner.
