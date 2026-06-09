# YouTube Downloader Pro (v1.1.0)

A high-performance, feature-rich desktop downloader built with a web-based **HTML/CSS/JS frontend**, **Python (Eel) backend**, and the robust **yt-dlp** engine. Designed to download YouTube videos, audio, and playlists at maximum quality (up to 1080p, 4K, and 8K) with clean visual dashboard controls.

---

## 🌟 Key Features

*   **High-Quality Merging**: Merges best separate video and best audio tracks automatically using FFmpeg (supporting 60 FPS, 1080p, 4K, and 8K).
*   **Bypass YouTube Bot Check**: Emulates official client signatures (e.g. Android VR) to solve signature challenges. Support for automatic browser cookie extraction and manual cookie file pathing.
*   **Playlist Selective Scraper [NEW v1.1.0]**: Analyzes playlists and displays a checkbox checklist of all videos (with thumbnails and durations), allowing you to download only selected videos.
*   **Custom Format Selector [NEW v1.1.0]**: Lists all available video/audio streams on YouTube, allowing power users to manually pair exact resolutions/bitrates and codecs (AV1, VP9, H.264, OPUS, AAC).
*   **Active Download Queue [NEW v1.1.0]**: Queue multiple downloads in the background. The app downloads them sequentially while keeping the input screen free to paste new URLs.
*   **Direct Subtitle & Metadata Embedding [NEW v1.1.0]**: Embeds subtitles and video tags (description, upload date, channel, uploader thumbnail cover art) directly inside the output file container.
*   **Automated Engine Updater [NEW v1.1.0]**: Update the internal `yt-dlp` package directly from settings in one click. Utilizes a dynamic override path so updates run natively inside packaged executables.
*   **Windowless Executable Launcher**: Features a custom C++ launcher (`ytd_webview_app.exe`) that spawns the Python backend completely hidden to prevent command prompt flashing on startup.

---

## 🛠️ Prerequisites

To run from source or compile the release, make sure you have:

1.  **Python 3.10+** (Required)
2.  **Node.js** (Required for signature decryption runtimes)
3.  **FFmpeg** (Required for merging streams and embedding metadata). Place `ffmpeg.exe` and `ffprobe.exe` in the application root folder or add them to your system PATH.
4.  **C++ Compiler** (Optional, MinGW `g++` & `windres` on PATH to compile the launcher).

---

## 🚀 Quick Start (Development)

### 1. Install Dependencies
Clone the repository and install the Python packages:
```bash
pip install -r requirements.txt
```
*(Dependencies: `eel`, `gevent`, `yt-dlp`)*

### 2. Launch the Application
Start the main Webview dashboard:
```bash
python ytd_webview_app.py
```
Or start the alternative native Tkinter client:
```bash
python myytd_app.py
```

---

## 📦 Automated Build & Packaging (Release v1.1.0)

We provide a streamlined build automation pipeline to package the application for Windows.

### 1. Compile the Application
Run the automated build script in PowerShell:
```powershell
powershell -ExecutionPolicy Bypass .\build.ps1
```
This script:
1. Verifies/installs Python packages.
2. Compiles `ytd_launcher.cpp` and icon resources into `dist/ytd_webview_app.exe`.
3. Packages the Python backend and HTML/CSS/JS files into `dist/ytd_webview_backend.exe` via PyInstaller.

### 2. Create the Distribution Zip
Run the release packaging script:
```powershell
powershell -ExecutionPolicy Bypass .\package_release.ps1
```
This script runs the compiler, automatically downloads static builds of **FFmpeg and FFprobe** from Gyan.dev, and bundles them with the compiled executables into a single distribution archive: **`YouTube_Downloader_Pro_x64.zip`**.

---

## 📝 Disclaimer

This project is for personal, educational use only. Please respect YouTube's Terms of Service.
