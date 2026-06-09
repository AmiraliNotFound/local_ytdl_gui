import sys
import os

# Support dynamic updates of yt-dlp by prioritizing 'updates' directory in path
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
updates_dir = os.path.join(app_dir, "updates")
if os.path.exists(updates_dir) and updates_dir not in sys.path:
    sys.path.insert(0, updates_dir)

from yt_dlp import YoutubeDL
import ytd_core

def download_video(url, auth_method="bypass", browser_name="chrome", cookies_path="youtube_cookies.txt"):
    # Translate arguments to standard config format
    config = {
        "auth_method": "Bypass (Client Emulation)" if auth_method == "bypass"
                       else "Browser Cookies (Auto)" if auth_method == "browser"
                       else "Cookie File (Manual)",
        "browser_name": browser_name,
        "cookies_path": cookies_path,
        "quality_preset": "480p",  # default limit
        "video_codec": "Best Available",
        "audio_quality": "192",
        "download_subtitles": False,
        "proxy_enabled": False,
        "filename_template": "%(title)s.%(ext)s"
    }

    # Setup environment PATH
    ytd_core.setup_environment(config)

    # Get base options and override for CLI verbose output
    ydl_opts = ytd_core.get_ytdl_opts(config, is_download=True)
    ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best'  # Keep small resolution for testing
    ydl_opts['ignoreerrors'] = False  # Raise actual errors during debug/CLI execution
    ydl_opts['quiet'] = False
    ydl_opts['verbose'] = True

    print(f"[INFO] Starting download for: {url}")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("[SUCCESS] Video downloaded successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Command-line video downloader using yt-dlp")
    parser.add_argument("url", nargs="?", default="https://youtu.be/j0wJBEZdwLs?si=XB2E7g6kT1qz_ddc", help="The URL of the video to download")
    parser.add_argument("--auth", choices=["bypass", "browser", "manual"], default="bypass", help="Authentication method: bypass bot check, extract from browser, or manual cookie file")
    parser.add_argument("--browser", default="chrome", help="Browser to extract cookies from (used with --auth browser)")
    parser.add_argument("--cookies", default="youtube_cookies.txt", help="Path to cookie file (used with --auth manual)")
    
    args = parser.parse_args()
    download_video(args.url, auth_method=args.auth, browser_name=args.browser, cookies_path=args.cookies)
