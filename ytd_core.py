import os
import sys
import json
import urllib.request
import tarfile
import io
import shutil
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
    "theme": "Dark",
    "embed_subtitles": False,
    "embed_metadata": False,
    "embed_thumbnail": False
}

def get_app_dir():
    """Safely resolve the directory containing the current executable or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def update_yt_dlp_engine():
    """Query PyPI, download latest sdist tarball, extract to updates/yt_dlp."""
    pypi_url = "https://pypi.org/pypi/yt-dlp/json"
    req = urllib.request.Request(pypi_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode('utf-8'))

    latest_version = data['info']['version']
    src_release = next((r for r in data['urls'] if r['packagetype'] == 'sdist'), None)
    if not src_release:
        raise Exception("Source release not found on PyPI")

    download_url = src_release['url']
    
    # Download source distribution tarball
    with urllib.request.urlopen(download_url, timeout=45) as response:
        tar_data = response.read()

    app_dir = get_app_dir()
    updates_dir = os.path.join(app_dir, "updates")
    temp_extract = os.path.join(app_dir, "updates_temp")
    
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract, ignore_errors=True)
    os.makedirs(temp_extract, exist_ok=True)

    # Extract tar.gz
    with tarfile.open(fileobj=io.BytesIO(tar_data), mode='r:gz') as tar:
        tar.extractall(path=temp_extract)

    extracted_dirs = os.listdir(temp_extract)
    if not extracted_dirs:
        raise Exception("Extraction directory empty")
        
    root_folder = os.path.join(temp_extract, extracted_dirs[0])
    src_ytdlp_folder = os.path.join(root_folder, "yt_dlp")
    
    if not os.path.exists(src_ytdlp_folder):
        raise Exception("yt_dlp package folder missing in sdist")

    target_ytdlp_folder = os.path.join(updates_dir, "yt_dlp")
    if os.path.exists(target_ytdlp_folder):
        shutil.rmtree(target_ytdlp_folder, ignore_errors=True)
    os.makedirs(updates_dir, exist_ok=True)

    shutil.move(src_ytdlp_folder, target_ytdlp_folder)
    shutil.rmtree(temp_extract, ignore_errors=True)

    return latest_version

def load_config(config_file=CONFIG_FILE):
    """Load configuration from config.json with fallback to default config."""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, OSError, ValueError):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config, config_file=CONFIG_FILE):
    """Save configuration to config.json."""
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def setup_environment(config):
    """Prepare environment paths including custom node path and application path."""
    current_dir = os.getcwd()
    app_dir = get_app_dir()

    paths_to_add = []
    if app_dir not in os.environ.get("PATH", "").split(os.pathsep):
        paths_to_add.append(app_dir)
    if current_dir not in os.environ.get("PATH", "").split(os.pathsep):
        paths_to_add.append(current_dir)
    
    node_path = config.get("node_path", "")
    if node_path and os.path.exists(node_path) and node_path not in os.environ.get("PATH", "").split(os.pathsep):
        paths_to_add.append(node_path)
        
    if paths_to_add:
        os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ.get("PATH", "")

def build_format_string(quality_preset, codec_pref):
    """Build standardized yt-dlp format selection queries."""
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

def get_ytdl_opts(config, is_download=True, progress_hooks=None, logger=None):
    """Assemble option parameters for the YoutubeDL object."""
    app_dir = get_app_dir()

    if not is_download:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'js_runtimes': {'node': {}},
        }
    else:
        out_dir = config.get("output_dir", os.path.join(os.path.expanduser("~"), "Downloads"))
        out_tmpl = os.path.join(out_dir, config.get("filename_template", "%(title)s.%(ext)s"))
        
        ydl_opts = {
            'outtmpl': out_tmpl,
            'yes_playlist': True,
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': True,
            'js_runtimes': {'node': {}},
            'retries': 20,
            'fragment_retries': 20,
            'retry_sleep_functions': {'http': lambda n: 10 * (n + 1)},
            'sleep_interval': 3,
            'max_sleep_interval': 10,
        }
        
        if progress_hooks:
            ydl_opts['progress_hooks'] = progress_hooks
        if logger:
            ydl_opts['logger'] = logger

    # Check local ffmpeg
    ffmpeg_path = os.path.join(app_dir, "ffmpeg.exe")
    if os.path.exists(ffmpeg_path):
        ydl_opts['ffmpeg_location'] = app_dir
    else:
        fallback_path = os.path.join(os.getcwd(), "ffmpeg.exe")
        if os.path.exists(fallback_path):
            ydl_opts['ffmpeg_location'] = os.getcwd()

    # Apply Authentication / Cookies
    auth_method = config.get("auth_method", "Bypass (Client Emulation)")
    if auth_method == "Browser Cookies (Auto)":
        browser = config.get("browser_name", "chrome")
        ydl_opts['cookiesfrombrowser'] = (browser,)
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_skip': ['webpage', 'configs'],
            }
        }
    elif auth_method == "Cookie File (Manual)":
        cookies = config.get("cookies_path", "")
        if os.path.exists(cookies):
            ydl_opts['cookiefile'] = cookies
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_skip': ['webpage', 'configs'],
            }
        }
    else:  # Bypass (Client Emulation)
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android_vr'],
            }
        }

    # Apply Proxy
    if config.get("proxy_enabled"):
        ydl_opts['proxy'] = config.get("proxy_url")

    # Playlist Items Limit
    playlist_items = config.get("playlist_items")
    if playlist_items and is_download:
        ydl_opts['playlist_items'] = str(playlist_items)

    # Apply Format & Subtitles & Metadata if downloading
    if is_download:
        video_format_id = config.get("video_format_id")
        audio_format_id = config.get("audio_format_id")
        
        if video_format_id and audio_format_id:
            # Custom formats selected
            if video_format_id == "audio_only":
                ydl_opts['format'] = audio_format_id
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['format'] = f"{video_format_id}+{audio_format_id}/best"
                ydl_opts['merge_output_format'] = 'mp4'
        else:
            # Standard preset formats
            quality_preset = config.get("quality_preset", "1080p (Best Quality)")
            codec_pref = config.get("video_codec", "Best Available")
            
            audio_quality = config.get("audio_quality", "192")
            if isinstance(audio_quality, str):
                audio_quality = audio_quality.split()[0]

            if "Audio Only" in quality_preset:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': str(audio_quality),
                }]
            else:
                ydl_opts['format'] = build_format_string(quality_preset, codec_pref)
                ydl_opts['merge_output_format'] = 'mp4'

        # Subtitles (Embed or download)
        if config.get("download_subtitles") or config.get("embed_subtitles"):
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            sub_langs = config.get("subtitle_languages", "").strip()
            if sub_langs:
                ydl_opts['subtitleslangs'] = [lang.strip() for lang in sub_langs.split(',')]

        if config.get("embed_subtitles"):
            ydl_opts['embedsubtitles'] = True

        # Metadata & Thumbnail
        if config.get("embed_metadata"):
            ydl_opts['embedmetadata'] = True
            
        if config.get("embed_thumbnail"):
            ydl_opts['writethumbnail'] = True
            ydl_opts['embedthumbnail'] = True

    return ydl_opts

def extract_detailed_info(url, config):
    """Fetch structured video details, formats list, and playlist items."""
    setup_environment(config)
    ydl_opts = get_ytdl_opts(config, is_download=False)
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
    if 'entries' in info:
        # Playlist
        entries = []
        for i, entry in enumerate(info['entries']):
            if not entry:
                continue
            entries.append({
                "index": i + 1,
                "title": entry.get('title', f"Video #{i+1}"),
                "duration": entry.get('duration', 0),
                "thumbnail": entry.get('thumbnail', ''),
                "id": entry.get('id', '')
            })
            
        return {
            "is_playlist": True,
            "playlist_title": info.get('title', 'Unknown Playlist'),
            "playlist_count": len(entries),
            "entries": entries,
            "thumbnail": entries[0]["thumbnail"] if entries else ""
        }
    else:
        # Single Video
        video_formats = []
        audio_formats = []
        
        formats = info.get('formats', [])
        for f in formats:
            vcodec = f.get('vcodec')
            acodec = f.get('acodec')
            fid = f.get('format_id')
            ext = f.get('ext')
            
            if not fid or not ext:
                continue
                
            # Filter Video-only streams
            if vcodec and vcodec != 'none' and (not acodec or acodec == 'none'):
                height = f.get('height')
                if height:
                    size = f.get('filesize') or f.get('filesize_approx') or 0
                    codec = vcodec.split('.')[0]
                    fps = f.get('fps', '')
                    fps_str = f" {fps}fps" if fps and fps != 30 else ""
                    video_formats.append({
                        "id": fid,
                        "resolution": f"{height}p{fps_str}",
                        "codec": codec,
                        "size": size,
                        "ext": ext
                    })
                    
            # Filter Audio-only streams
            elif acodec and acodec != 'none' and (not vcodec or vcodec == 'none'):
                abr = f.get('abr')
                if abr:
                    size = f.get('filesize') or f.get('filesize_approx') or 0
                    codec = acodec.split('.')[0]
                    audio_formats.append({
                        "id": fid,
                        "bitrate": f"{int(abr)} kbps",
                        "codec": codec,
                        "size": size,
                        "ext": ext
                    })

        view_count = info.get('view_count')
        try:
            views_str = f"{int(view_count):,}" if view_count is not None else "Unknown"
        except (ValueError, TypeError):
            views_str = str(view_count) if view_count is not None else "Unknown"

        return {
            "is_playlist": False,
            "title": info.get('title', 'Unknown Title'),
            "thumbnail": info.get('thumbnail', ''),
            "uploader": info.get('uploader', 'Unknown Channel'),
            "views": views_str,
            "duration": info.get('duration', 0),
            "video_formats": video_formats,
            "audio_formats": audio_formats
        }
