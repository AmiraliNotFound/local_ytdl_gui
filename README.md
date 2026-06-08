# YouTube Downloader Pro

A modern, high-performance desktop application built with **Python**, **CustomTkinter**, and **yt-dlp** designed for downloading YouTube videos, audio, and playlists in maximum quality (up to 1080p, 4K, and 8K). 

It features an elegant UI with built-in theme support (Dark/Light/System) and advanced authentication bypass methods to prevent "Sign in to confirm you're not a bot" checks.

---

## 🌟 Key Features

* **High-Quality Video & Audio**: Supports downloading separate best video and best audio formats, merging them automatically with FFmpeg (up to 1080p, 4K, 8K, and 60 FPS).
* **Bypass YouTube Bot Check (Cookie-Free)**:
  * **Bypass (Client Emulation)**: Emulates official **Android VR** player endpoints. Solves decryption challenges natively using Node.js without requiring login or cookie files.
  * **Browser Cookies (Auto)**: Automatically extracts active session cookies from Chrome, Edge, Firefox, Brave, Safari, Opera, or Vivaldi.
  * **Cookie File (Manual)**: Allows loading traditional browser-exported `.txt` cookie files.
* **Format & Codec Selection**: Fine-tune downloads by choosing your resolution presets and video codecs (VP9, AV1, H.264, or H.265/HEVC).
* **Modern Desktop GUI**: Sleek dashboard layout with dynamic widgets, live logs, real-time download speed, playlist progress tracking, and theme switching.
* **CLI Utility**: Includes `download_inline.py` for headless or command-line operation.

---

## 🛠️ Prerequisites

To run this application, make sure you have the following installed on your system:

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
*(Dependencies: `customtkinter`, `yt-dlp`, `pillow` (optional for thumbnails))*

### 2. Running the GUI Application
Launch the main dashboard interface:

```bash
python myytd_app.py
```

### 3. Running the CLI Tool
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

Inside the **Output Settings** and **Network & Engine** tabs of the GUI, you can customize:
* **Output Folder**: Destination for downloaded files.
* **Authentication Method**: Configure client emulation, auto browser extraction, or manual cookie paths.
* **Theme Options**: Dynamically switch the theme between Dark, Light, or System appearance modes.
* **Subtitles**: Enable/disable subtitles and specify preferred language codes (e.g., `en,es,fr`).
* **Proxy settings**: Route download traffic through a custom HTTP/SOCKS proxy server.

---

## 📝 Disclaimer

This project is for personal, educational use only. Please respect YouTube's Terms of Service and only download videos when you have permission from the copyright owner.
