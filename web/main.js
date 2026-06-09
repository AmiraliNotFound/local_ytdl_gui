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
            showConnectionError("The Eel library could not be loaded. Please make sure the backend is running.");
            return;
        }
        
        if (!eel._websocket) {
            showConnectionError("Websocket connection is not initialized. Please restart the application.");
            return;
        }

        const ws = eel._websocket;
        
        if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
            showConnectionError("Websocket connection is closed. The python backend may have crashed.");
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

// Playlist Card Elements
const playlistCard = document.getElementById("playlist-card");
const playlistList = document.getElementById("playlist-list");
const playlistSelectAll = document.getElementById("playlist-select-all");
const playlistDeselectAll = document.getElementById("playlist-deselect-all");

// Settings Elements
const qualityPreset = document.getElementById("quality-preset");
const videoCodec = document.getElementById("video-codec");
const audioQuality = document.getElementById("audio-quality");
const downloadSubtitles = document.getElementById("download-subtitles");
const embedSubtitles = document.getElementById("embed-subtitles");
const embedMetadata = document.getElementById("embed-metadata");
const subtitleLanguages = document.getElementById("subtitle-languages");
const subtitleLangsGroup = document.getElementById("subtitle-langs-group");
const customStreamsGroup = document.getElementById("custom-streams-group");
const customVideoFormat = document.getElementById("custom-video-format");
const customAudioFormat = document.getElementById("custom-audio-format");

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

// Engine Maintenance
const updateEngineBtn = document.getElementById("update-engine-btn");
const engineStatus = document.getElementById("engine-status");

// Queue Elements
const queueCard = document.getElementById("queue-card");
const queueList = document.getElementById("queue-list");
const queueCount = document.getElementById("queue-count");
const clearQueueBtn = document.getElementById("clear-queue-btn");

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

// Application State
let appConfig = {};
let currentActionState = "analyze"; // "analyze" or "download"
let currentPreviewInfo = null; // Store analyzed info
let downloadQueue = [];
let queueIsProcessing = false;

function formatBytes(bytes, decimals = 2) {
    if (!bytes) return 'N/A';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

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
    qualityPreset.addEventListener("change", updateCustomFormatsVisibility);

    // 3. Theme Toggle Listener
    themeToggle.addEventListener("click", toggleTheme);

    // 4. Directory & File Selection Dialogs
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

    // 8. Playlist Select/Deselect All
    playlistSelectAll.addEventListener("click", () => togglePlaylistCheckboxes(true));
    playlistDeselectAll.addEventListener("click", () => togglePlaylistCheckboxes(false));

    // 9. Engine Auto-Update Trigger
    updateEngineBtn.addEventListener("click", triggerEngineUpdate);

    // 10. Queue Clear Trigger
    clearQueueBtn.addEventListener("click", clearQueue);

    // 11. GitHub Link Interceptor
    const githubBtn = document.querySelector(".github-btn");
    if (githubBtn) {
        githubBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const url = githubBtn.getAttribute("href");
            if (typeof eel !== 'undefined' && typeof eel.open_link === 'function') {
                eel.open_link(url);
            } else {
                window.open(url, "_blank");
            }
        });
    }

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

function updateCustomFormatsVisibility() {
    if (qualityPreset.value === "Custom Streams (Advanced)") {
        customStreamsGroup.classList.remove("hidden");
    } else {
        customStreamsGroup.classList.add("hidden");
    }
}

// Playlist Checkbox Helper
function togglePlaylistCheckboxes(checked) {
    const checkboxes = playlistList.querySelectorAll("input[type='checkbox']");
    checkboxes.forEach(cb => cb.checked = checked);
}

// Theme Management
function toggleTheme() {
    const isLight = document.body.classList.toggle("light-mode");
    const modeIcon = themeToggle.querySelector(".mode-icon");
    modeIcon.textContent = isLight ? "☀️" : "🌙";
    
    if (typeof eel !== 'undefined') {
        eel.save_theme(isLight ? "Light" : "Dark");
    }
}

// Trigger Core Engine Update
function triggerEngineUpdate() {
    updateEngineBtn.disabled = true;
    updateEngineBtn.textContent = "Updating Core...";
    engineStatus.textContent = "Updating...";
    engineStatus.className = "badge updating";
    
    if (typeof eel !== 'undefined') {
        eel.update_engine();
    }
}

// Action Button Handler
function handleActionButtonClick() {
    const url = urlInput.value.trim();
    if (!url) {
        append_log("[ERROR] Please paste a URL first.\n");
        return;
    }

    const currentConfig = buildConfigFromUI();

    if (currentActionState === "analyze") {
        actionBtn.disabled = true;
        actionBtn.textContent = "Analyzing...";
        append_log(`\n[INFO] Fetching video details for: ${url}\n`);

        if (typeof eel !== 'undefined') {
            eel.analyze_url(url, currentConfig);
        }
    } else if (currentActionState === "download") {
        // Build Playlist items string if playlist is active
        if (currentPreviewInfo && currentPreviewInfo.is_playlist) {
            const checkedBoxes = playlistList.querySelectorAll("input[type='checkbox']:checked");
            if (checkedBoxes.length === 0) {
                append_log("[ERROR] No playlist items selected. Select at least one item to download.\n");
                return;
            }
            const indices = Array.from(checkedBoxes).map(cb => cb.dataset.index);
            currentConfig["playlist_items"] = indices.join(",");
        }

        // Custom Formats selection mapping
        if (qualityPreset.value === "Custom Streams (Advanced)") {
            currentConfig["video_format_id"] = customVideoFormat.value;
            currentConfig["audio_format_id"] = customAudioFormat.value;
        }

        // Add to active download queue
        const title = currentPreviewInfo ? currentPreviewInfo.title || url : url;
        const queueItem = {
            id: Date.now() + Math.random(),
            url: url,
            title: title,
            status: "pending",
            config: currentConfig
        };
        
        downloadQueue.push(queueItem);
        updateQueueUI();
        
        append_log(`[INFO] Added to Queue: ${title}\n`);
        
        // Return UI immediately to analysis state so user can add more videos
        reset_analyze_btn("Analyze URL");
        urlInput.value = "";

        // Trigger queue process if not active
        if (!queueIsProcessing) {
            processNextQueueItem();
        }
    }
}

// Process Next Queue Item
function processNextQueueItem() {
    const nextItem = downloadQueue.find(item => item.status === "pending");
    if (!nextItem) {
        queueIsProcessing = false;
        return;
    }

    queueIsProcessing = true;
    nextItem.status = "downloading";
    updateQueueUI();

    update_progress(0, `Downloading: ${nextItem.title}`);
    playlistProgressContainer.style.display = "none";

    append_log(`\n[INFO] Spawning download task for: ${nextItem.title}\n`);
    if (typeof eel !== 'undefined') {
        eel.start_download(nextItem.url, nextItem.config);
    }
}

// Update Queue Interface
function updateQueueUI() {
    if (downloadQueue.length > 0) {
        queueCard.classList.remove("hidden");
    } else {
        queueCard.classList.add("hidden");
    }

    queueCount.textContent = downloadQueue.length;
    queueList.innerHTML = "";

    downloadQueue.forEach(item => {
        const itemDiv = document.createElement("div");
        itemDiv.className = `queue-item ${item.status === 'downloading' ? 'active' : ''}`;
        itemDiv.innerHTML = `
            <div class="queue-item-info">
                <span class="queue-item-title">${item.title}</span>
                <span class="queue-item-url">${item.url}</span>
            </div>
            <div class="queue-item-actions">
                <span class="queue-status-badge ${item.status}">${item.status}</span>
                <button class="btn-remove-queue" title="Remove from queue" onclick="removeFromQueue(${item.id})">❌</button>
            </div>
        `;
        queueList.appendChild(itemDiv);
    });
}

// Remove Item from Queue
window.removeFromQueue = function(id) {
    const idx = downloadQueue.findIndex(item => item.id === id);
    if (idx !== -1) {
        const item = downloadQueue[idx];
        if (item.status === "downloading") {
            append_log("[WARNING] Cannot remove currently downloading item.\n");
            return;
        }
        downloadQueue.splice(idx, 1);
        updateQueueUI();
    }
};

// Clear Queue
function clearQueue() {
    // Keep only downloading item
    downloadQueue = downloadQueue.filter(item => item.status === "downloading");
    updateQueueUI();
}

// Build Config object from current Form values
function buildConfigFromUI() {
    return {
        "output_dir": outputDir.value,
        "quality_preset": qualityPreset.value,
        "video_codec": videoCodec.value,
        "audio_quality": audioQuality.value,
        "download_subtitles": downloadSubtitles.checked,
        "embed_subtitles": embedSubtitles.checked,
        "embed_metadata": embedMetadata.checked,
        "embed_thumbnail": embedMetadata.checked, // Sync thumbnail with metadata tag embedding
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
    embedSubtitles.checked = !!config.embed_subtitles;
    embedMetadata.checked = !!config.embed_metadata;
    subtitleLanguages.value = config.subtitle_languages || "en";
    
    authMethod.value = config.auth_method || "Bypass (Client Emulation)";
    browserName.value = config.browser_name || "chrome";
    cookiesPath.value = config.cookies_path || "youtube_cookies.txt";
    
    proxyEnabled.checked = !!config.proxy_enabled;
    proxyUrl.value = config.proxy_url || "http://127.0.0.1:8080";
    nodePath.value = config.node_path || "";
    filenameTemplate.value = config.filename_template || "%(title)s.%(ext)s";

    const modeIcon = themeToggle.querySelector(".mode-icon");
    if (config.theme === "Light") {
        document.body.classList.add("light-mode");
        modeIcon.textContent = "☀️";
    } else {
        document.body.classList.remove("light-mode");
        modeIcon.textContent = "🌙";
    }

    updateAuthFieldVisibility();
    updateSubtitleFieldVisibility();
    updateProxyFieldVisibility();
    updateCustomFormatsVisibility();
}

eel.expose(update_preview);
function update_preview(info) {
    currentPreviewInfo = info;
    previewCard.classList.remove("hidden");
    
    videoThumbnail.src = info.thumbnail || "";
    videoTitle.textContent = info.title || "Unknown Title";
    
    if (info.is_playlist) {
        videoUploader.textContent = `📁 Playlist (${info.playlist_count} videos)`;
        videoViews.textContent = "";
        videoDuration.classList.add("hidden");
        playlistBadge.classList.remove("hidden");
        playlistBadge.textContent = `📁 Playlist`;
        
        // Populate Playlist Checklist
        playlistCard.classList.remove("hidden");
        playlistList.innerHTML = "";
        info.entries.forEach(entry => {
            const min = Math.floor(entry.duration / 60);
            const sec = String(entry.duration % 60).padStart(2, '0');
            const durStr = entry.duration ? `${min}:${sec}` : "N/A";
            
            const itemDiv = document.createElement("div");
            itemDiv.className = "playlist-item";
            itemDiv.innerHTML = `
                <input type="checkbox" data-index="${entry.index}" checked>
                <span class="playlist-item-title">${entry.index}. ${entry.title}</span>
                <span class="playlist-item-duration">${durStr}</span>
            `;
            playlistList.appendChild(itemDiv);
        });

        // Clear formats selection since it is a playlist
        qualityPreset.value = "Best Available (No Limit)";
        updateCustomFormatsVisibility();
    } else {
        videoUploader.textContent = `👤 ${info.uploader || "Unknown Channel"}`;
        videoViews.textContent = `👁️ ${info.views || "0"} views`;
        playlistBadge.classList.add("hidden");
        playlistCard.classList.add("hidden");

        if (info.duration) {
            const min = Math.floor(info.duration / 60);
            const sec = String(info.duration % 60).padStart(2, '0');
            videoDuration.textContent = `${min}:${sec}`;
            videoDuration.classList.remove("hidden");
        } else {
            videoDuration.classList.add("hidden");
        }

        // Populate Custom Streams
        customVideoFormat.innerHTML = '<option value="">Best Video Stream</option>';
        info.video_formats.forEach(f => {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = `${f.resolution} (${f.codec}) - ${formatBytes(f.size)} [.${f.ext}]`;
            customVideoFormat.appendChild(opt);
        });

        customAudioFormat.innerHTML = '<option value="">Best Audio Stream</option>';
        // Insert a dummy video bypass format if downloading audio only in custom streams
        const optAudioOnly = document.createElement("option");
        optAudioOnly.value = "audio_only";
        optAudioOnly.textContent = "Audio Only (Extract MP3)";
        customVideoFormat.insertBefore(optAudioOnly, customVideoFormat.firstChild);

        info.audio_formats.forEach(f => {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = `${f.bitrate} (${f.codec}) - ${formatBytes(f.size)} [.${f.ext}]`;
            customAudioFormat.appendChild(opt);
        });
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
    playlistCard.classList.add("hidden");
    currentPreviewInfo = null;

    // Resolve queue task status
    const downloadingItem = downloadQueue.find(item => item.status === "downloading");
    if (downloadingItem) {
        downloadingItem.status = "completed";
        updateQueueUI();
        processNextQueueItem(); // Automatically trigger next queue download!
    }
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

    // Check for errors to mark queue task failed
    if (message.includes("[CRITICAL ERROR]") || message.includes("[ERROR] Download failed")) {
        const downloadingItem = downloadQueue.find(item => item.status === "downloading");
        if (downloadingItem) {
            downloadingItem.status = "failed";
            updateQueueUI();
            
            // Clean up and proceed
            currentActionState = "analyze";
            actionBtn.disabled = false;
            actionBtn.textContent = "Analyze URL";
            actionBtn.className = "btn btn-primary";
            previewCard.classList.add("hidden");
            playlistCard.classList.add("hidden");
            currentPreviewInfo = null;
            
            processNextQueueItem();
        }
    }
}

// Engine update callback
eel.expose(engine_update_status);
function engine_update_status(success, versionOrError) {
    updateEngineBtn.disabled = false;
    updateEngineBtn.textContent = "Update yt-dlp Core";
    
    if (success) {
        engineStatus.textContent = `v${versionOrError}`;
        engineStatus.className = "badge updated";
    } else {
        engineStatus.textContent = "Failed";
        engineStatus.className = "badge failed";
    }
}
