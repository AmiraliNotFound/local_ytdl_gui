import sys
import os
from yt_dlp import YoutubeDL

def download_video(url, auth_method="bypass", browser_name="chrome", cookies_path="youtube_cookies.txt"):
    ydl_opts = {
        'yes_playlist': True,
        'ignoreerrors': False,  # Changed to False so we raise actual errors during debug/loop
        'no_warnings': False,
        'quiet': False,
        'js_runtimes': {'node': {}},
        'verbose': True,
        'retries': 20,
        'fragment_retries': 20,
        'retry_sleep_functions': {'http': lambda n: 10 * (n + 1)},
        'sleep_interval': 3,
        'max_sleep_interval': 10,
        'format': 'bestvideo[height<=360]+bestaudio/best',  # Limit resolution for quick loop verification
    }

    if auth_method == "browser":
        ydl_opts['cookiesfrombrowser'] = (browser_name,)
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_skip': ['webpage', 'configs'],
            }
        }
        print(f"[INFO] Extracting cookies from browser: {browser_name}")
    elif auth_method == "manual":
        if os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path
            print(f"[INFO] Using cookies file: {cookies_path}")
        else:
            print(f"[WARNING] Cookies file '{cookies_path}' not found. Running without cookies.")
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_skip': ['webpage', 'configs'],
            }
        }
    else:  # bypass
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android_vr'],
            }
        }
        print("[INFO] Running with no cookies. Emulating Android VR client to bypass bot detection.")

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
