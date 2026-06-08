# package_release.ps1
# This script bundles the YouTube Downloader Pro executables and FFmpeg binaries into a single ZIP file ready for GitHub Release.

$ErrorActionPreference = "Stop"

$ReleaseDir = "release_temp"
$ZipName = "YouTube_Downloader_Pro_x64.zip"

Write-Host "=== Preparing Release Directory ===" -ForegroundColor Cyan
if (Test-Path $ReleaseDir) {
    Remove-Item -Recurse -Force $ReleaseDir
}
if (Test-Path $ZipName) {
    Remove-Item -Force $ZipName
}
New-Item -ItemType Directory -Path $ReleaseDir | Out-Null

Write-Host "=== Copying Application Executables ===" -ForegroundColor Cyan
if (-not (Test-Path "dist/ytd_webview_app.exe") -or -not (Test-Path "dist/ytd_webview_backend.exe")) {
    Write-Error "Could not find executables in dist/ folder. Please build the project first."
}
Copy-Item "dist/ytd_webview_app.exe" -Destination "$ReleaseDir/ytd_webview_app.exe"
Copy-Item "dist/ytd_webview_backend.exe" -Destination "$ReleaseDir/ytd_webview_backend.exe"

Write-Host "=== Checking for Local FFmpeg Binaries ===" -ForegroundColor Cyan
$HasLocalFfmpeg = $false
if ((Test-Path "ffmpeg.exe") -and (Test-Path "ffprobe.exe")) {
    Write-Host "Found local ffmpeg.exe and ffprobe.exe. Copying them..." -ForegroundColor Green
    Copy-Item "ffmpeg.exe" -Destination "$ReleaseDir/ffmpeg.exe"
    Copy-Item "ffprobe.exe" -Destination "$ReleaseDir/ffprobe.exe"
    $HasLocalFfmpeg = $true
}

if (-not $HasLocalFfmpeg) {
    Write-Host "Local FFmpeg not found in root. Downloading static builds..." -ForegroundColor Yellow
    
    # We use a reliable, lightweight static build of FFmpeg from Gyan.dev (release-essentials)
    $FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $FfmpegZip = "ffmpeg_temp.zip"
    
    Write-Host "Downloading FFmpeg from $FfmpegUrl..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $FfmpegUrl -OutFile $FfmpegZip -UseBasicParsing
    
    Write-Host "Extracting FFmpeg..." -ForegroundColor Cyan
    $ExtractDir = "ffmpeg_extracted"
    if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }
    Expand-Archive -Path $FfmpegZip -DestinationPath $ExtractDir
    
    Write-Host "Moving ffmpeg.exe and ffprobe.exe to release folder..." -ForegroundColor Green
    $FfmpegBinPath = Get-ChildItem -Path $ExtractDir -Filter "ffmpeg.exe" -Recurse | Select-Object -ExpandProperty DirectoryName
    Copy-Item "$FfmpegBinPath/ffmpeg.exe" -Destination "$ReleaseDir/ffmpeg.exe"
    Copy-Item "$FfmpegBinPath/ffprobe.exe" -Destination "$ReleaseDir/ffprobe.exe"
    
    # Cleanup temp files
    Remove-Item -Force $FfmpegZip
    Remove-Item -Recurse -Force $ExtractDir
}

Write-Host "=== Creating Release ZIP Archive ===" -ForegroundColor Cyan
Compress-Archive -Path "$ReleaseDir/*" -DestinationPath $ZipName

Write-Host "=== Cleaning Up Temp Folders ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $ReleaseDir

Write-Host "=== Success! ===" -ForegroundColor Green
Write-Host "Generated release archive: $ZipName" -ForegroundColor Green
Write-Host "You can now upload this ZIP file directly to your GitHub Releases page." -ForegroundColor Green
