// Redirect console log/error/warn to python backend logger
const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;

function sendToPython(type, args) {
    if (typeof eel !== 'undefined' && typeof eel.js_log === 'function') {
        const msg = `[JS ${type}] ${args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ')}`;
        try {
            eel.js_log(msg);
        } catch (e) {}
    }
}

console.log = function(...args) {
    originalLog.apply(console, args);
    sendToPython('LOG', args);
};
console.error = function(...args) {
    originalError.apply(console, args);
    sendToPython('ERROR', args);
};
console.warn = function(...args) {
    originalWarn.apply(console, args);
    sendToPython('WARN', args);
};

// Global Javascript Error Logger to Python Backend
window.onerror = function(message, source, lineno, colno, error) {
    const errorMsg = `[JS ERROR] ${message} at ${source}:${lineno}:${colno}`;
    if (typeof eel !== 'undefined' && typeof eel.js_log === 'function') {
        try {
            eel.js_log(errorMsg);
        } catch (e) {}
    }
    return false;
};

// Connection Error Banner Helper
function showConnectionError(message) {
    if (document.querySelector(".connection-error-banner")) return;
    const container = document.querySelector(".app-container");
    const errDiv = document.createElement("div");
    errDiv.className = "connection-error-banner";
    errDiv.innerHTML = `
        <div class="error-banner-content">
            <span class="error-icon">⚠️</span>
            <div class="error-text">
                <h3>Backend Connection Failed</h3>
                <p>${message}</p>
            </div>
        </div>
    `;
    container.insertBefore(errDiv, container.firstChild);
}

// Monitor backend websocket status
function monitorConnection() {
    setTimeout(() => {
        if (typeof eel === 'undefined') {
            showConnectionError("The Eel library could not be loaded. Please make sure the backend is running and that no firewalls or network changes are blocking local websocket ports.");
            return;
        }
        
        if (!eel._websocket) {
            showConnectionError("Websocket connection is not initialized. Please restart the application.");
            return;
        }

        const ws = eel._websocket;
        
        if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
            showConnectionError("Websocket connection is closed. The python backend may have crashed or terminated.");
        }

        ws.addEventListener('close', () => {
            showConnectionError("Websocket connection was closed. The python backend process may have exited.");
        });
        
        ws.addEventListener('error', (err) => {
            showConnectionError("Websocket connection error occurred. Check browser console.");
        });
    }, 2000);
}

document.addEventListener("DOMContentLoaded", () => {
    initializeUI();
    monitorConnection();
});

// Cache DOM Elements
const urlInput = document.getElementById("url-input");
const actionBtn = document.getElementById("action-btn");
const themeToggle = document.getElementById("theme-toggle");

const previewCard = document.getElementById("preview-card");
const videoThumbnail = document.getElementById("video-thumbnail");
const videoDuration = document.getElementById("video-duration");
const videoTitle = document.getElementById("video-title");
const videoUploader = document.getElementById("video-uploader");
const videoViews = document.getElementById("video-views");
const playlistBadge = document.getElementById("playlist-badge");

const qualityPreset = document.getElementById("quality-preset");
const videoCodec = document.getElementById("video-codec");
const audioQuality = document.getElementById("audio-quality");
const downloadSubtitles = document.getElementById("download-subtitles");
const subtitleLanguages = document.getElementById("subtitle-languages");
const subtitleLangsGroup = document.getElementById("subtitle-langs-group");

const outputDir = document.getElementById("output-dir");
const browseDirBtn = document.getElementById("browse-dir-btn");
const authMethod = document.getElementById("auth-method");
const browserName = document.getElementById("browser-name");
const browserSelectGroup = document.getElementById("browser-select-group");
const cookiesPath = document.getElementById("cookies-path");
const browseCookiesBtn = document.getElementById("browse-cookies-btn");
const cookiesFileGroup = document.getElementById("cookies-file-group");

const filenameTemplate = document.getElementById("filename-template");
const nodePath = document.getElementById("node-path");
const proxyEnabled = document.getElementById("proxy-enabled");
const proxyUrl = document.getElementById("proxy-url");
const proxyUrlGroup = document.getElementById("proxy-url-group");

const fileStatus = document.getElementById("file-status");
const filePercent = document.getElementById("file-percent");
const fileProgressBar = document.getElementById("file-progress-bar");

const playlistProgressContainer = document.getElementById("playlist-progress-container");
const playlistStatus = document.getElementById("playlist-status");
const playlistPercent = document.getElementById("playlist-percent");
const playlistProgressBar = document.getElementById("playlist-progress-bar");

const logConsole = document.getElementById("log-console");
const clearLogBtn = document.getElementById("clear-log-btn");
const saveDefaultsBtn = document.getElementById("save-defaults-btn");
const resetDefaultsBtn = document.getElementById("reset-defaults-btn");

let appConfig = {};
let currentActionState = "analyze"; // "analyze" or "download"

function initializeUI() {
    // 1. Tab Switching Logic
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });

    // 2. Setting Visibility Updates on Input Change
    authMethod.addEventListener("change", updateAuthFieldVisibility);
    downloadSubtitles.addEventListener("change", updateSubtitleFieldVisibility);
    proxyEnabled.addEventListener("change", updateProxyFieldVisibility);

    // 3. Theme Toggle Listener
    themeToggle.addEventListener("click", toggleTheme);

    // 4. Directory & File Selection Dialogs (Python callbacks)
    browseDirBtn.addEventListener("click", () => {
        if (typeof eel !== 'undefined') {
            eel.choose_directory()(path => {
                if (path) outputDir.value = path;
            });
        }
    });

    browseCookiesBtn.addEventListener("click", () => {
        if (typeof eel !== 'undefined') {
            eel.choose_cookies_file()(path => {
                if (path) cookiesPath.value = path;
            });
        }
    });

    // 5. Save and Reset Configuration
    saveDefaultsBtn.addEventListener("click", saveConfiguration);
    resetDefaultsBtn.addEventListener("click", () => {
        if (typeof eel !== 'undefined') eel.reset_config();
    });

    // 6. Action Button (Analyze / Download)
    actionBtn.addEventListener("click", handleActionButtonClick);

    // 7. Clear Log Console
    clearLogBtn.addEventListener("click", () => {
        logConsole.textContent = "";
    });

    // Request initial config from Python
    if (typeof eel !== 'undefined') {
        eel.get_initial_config();
    }
}

// UI Visibility Updates
function updateAuthFieldVisibility() {
    const method = authMethod.value;
    if (method === "Bypass (Client Emulation)") {
        browserSelectGroup.classList.add("hidden");
        cookiesFileGroup.classList.add("hidden");
    } else if (method === "Browser Cookies (Auto)") {
        browserSelectGroup.classList.remove("hidden");
        cookiesFileGroup.classList.add("hidden");
    } else if (method === "Cookie File (Manual)") {
        browserSelectGroup.classList.add("hidden");
        cookiesFileGroup.classList.remove("hidden");
    }
}

function updateSubtitleFieldVisibility() {
    if (downloadSubtitles.checked) {
        subtitleLangsGroup.classList.remove("hidden");
    } else {
        subtitleLangsGroup.classList.add("hidden");
    }
}

function updateProxyFieldVisibility() {
    if (proxyEnabled.checked) {
        proxyUrlGroup.classList.remove("hidden");
    } else {
        proxyUrlGroup.classList.add("hidden");
    }
}

// Theme Management
function toggleTheme() {
    const isLight = document.body.classList.toggle("light-mode");
    const modeIcon = themeToggle.querySelector(".mode-icon");
    modeIcon.textContent = isLight ? "☀️" : "🌙";
    
    // Save theme to python config
    if (typeof eel !== 'undefined') {
        eel.save_theme(isLight ? "Light" : "Dark");
    }
}

// Action Button Handler
function handleActionButtonClick() {
    const url = urlInput.value.trim();
    if (!url) {
        appendLog("[ERROR] Please paste a URL first.\n");
        return;
    }

    const currentConfig = buildConfigFromUI();

    if (currentActionState === "analyze") {
        actionBtn.disabled = true;
        actionBtn.textContent = "Analyzing...";
        appendLog(`\n[INFO] Fetching video info for: ${url}\n`);

        if (typeof eel !== 'undefined') {
            eel.analyze_url(url, currentConfig);
        }
    } else if (currentActionState === "download") {
        actionBtn.disabled = true;
        actionBtn.textContent = "Downloading...";
        
        // Reset progress bars
        updateProgress(0, "Current File: Preparing...");
        playlistProgressContainer.style.display = "none";
        
        if (typeof eel !== 'undefined') {
            eel.start_download(url, currentConfig);
        }
    }
}

// Build Config object from current Form values
function buildConfigFromUI() {
    return {
        "output_dir": outputDir.value,
        "quality_preset": qualityPreset.value,
        "video_codec": videoCodec.value,
        "audio_quality": audioQuality.value,
        "download_subtitles": downloadSubtitles.checked,
        "subtitle_languages": subtitleLanguages.value,
        "auth_method": authMethod.value,
        "browser_name": browserName.value,
        "cookies_path": cookiesPath.value,
        "proxy_enabled": proxyEnabled.checked,
        "proxy_url": proxyUrl.value,
        "node_path": nodePath.value,
        "filename_template": filenameTemplate.value,
        "theme": document.body.classList.contains("light-mode") ? "Light" : "Dark"
    };
}

function saveConfiguration() {
    const config = buildConfigFromUI();
    if (typeof eel !== 'undefined') {
        eel.save_config(config);
    }
}

// API Callbacks invoked from Python
eel.expose(set_initial_config);
function set_initial_config(config) {
    appConfig = config;

    outputDir.value = config.output_dir || "";
    qualityPreset.value = config.quality_preset || "1080p (Best Quality)";
    videoCodec.value = config.video_codec || "Best Available";
    audioQuality.value = config.audio_quality || "192";
    downloadSubtitles.checked = !!config.download_subtitles;
    subtitleLanguages.value = config.subtitle_languages || "en";
    
    authMethod.value = config.auth_method || "Bypass (Client Emulation)";
    browserName.value = config.browser_name || "chrome";
    cookiesPath.value = config.cookies_path || "youtube_cookies.txt";
    
    proxyEnabled.checked = !!config.proxy_enabled;
    proxyUrl.value = config.proxy_url || "http://127.0.0.1:8080";
    nodePath.value = config.node_path || "";
    filenameTemplate.value = config.filename_template || "%(title)s.%(ext)s";

    // Set Theme
    const modeIcon = themeToggle.querySelector(".mode-icon");
    if (config.theme === "Light") {
        document.body.classList.add("light-mode");
        modeIcon.textContent = "☀️";
    } else {
        document.body.classList.remove("light-mode");
        modeIcon.textContent = "🌙";
    }

    // Trigger field visibility updates
    updateAuthFieldVisibility();
    updateSubtitleFieldVisibility();
    updateProxyFieldVisibility();
}

eel.expose(update_preview);
function update_preview(info) {
    previewCard.classList.remove("hidden");
    
    videoThumbnail.src = info.thumbnail || "";
    videoTitle.textContent = info.title || "Unknown Title";
    videoUploader.textContent = `👤 ${info.uploader || "Unknown Channel"}`;
    videoViews.textContent = `👁️ ${info.views || "0"} views`;
    
    if (info.duration) {
        const min = Math.floor(info.duration / 60);
        const sec = String(info.duration % 60).padStart(2, '0');
        videoDuration.textContent = `${min}:${sec}`;
        videoDuration.classList.remove("hidden");
    } else {
        videoDuration.classList.add("hidden");
    }

    if (info.is_playlist) {
        playlistBadge.classList.remove("hidden");
        playlistBadge.textContent = `📁 Playlist (${info.playlist_count} videos)`;
    } else {
        playlistBadge.classList.add("hidden");
    }

    // Shift state to download
    currentActionState = "download";
    actionBtn.disabled = false;
    actionBtn.textContent = "Start Download";
    actionBtn.className = "btn btn-primary btn-download-state";
}

eel.expose(reset_analyze_btn);
function reset_analyze_btn(stateText = "Analyze URL") {
    currentActionState = "analyze";
    actionBtn.disabled = false;
    actionBtn.textContent = stateText;
    actionBtn.className = "btn btn-primary";
    previewCard.classList.add("hidden");
}

eel.expose(update_progress);
function update_progress(percent, text) {
    filePercent.textContent = `${Math.round(percent * 100)}%`;
    fileStatus.textContent = text;
    fileProgressBar.style.width = `${percent * 100}%`;
}

eel.expose(update_playlist_progress);
function update_playlist_progress(current, total) {
    playlistProgressContainer.style.display = "block";
    playlistStatus.textContent = `Playlist Progress: Video ${current} of ${total}`;
    const percent = current / total;
    playlistPercent.textContent = `${Math.round(percent * 100)}%`;
    playlistProgressBar.style.width = `${percent * 100}%`;
}

eel.expose(append_log);
function append_log(message) {
    logConsole.textContent += message;
    logConsole.scrollTop = logConsole.scrollHeight;
}
