# build.ps1
# Automates compiling the C++ launcher and building the Python backend with PyInstaller.

$ErrorActionPreference = "Stop"

Write-Host "=== Verifying Python Dependencies ===" -ForegroundColor Cyan
$RequiredPackages = @(
    @{ Name = "eel"; Import = "eel" },
    @{ Name = "gevent"; Import = "gevent" },
    @{ Name = "yt-dlp"; Import = "yt_dlp" },
    @{ Name = "pyinstaller"; Import = "PyInstaller" }
)
foreach ($pkg in $RequiredPackages) {
    $name = $pkg.Name
    $import = $pkg.Import
    python -c "import $import" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing missing dependency: $name..." -ForegroundColor Yellow
        python -m pip install $name
    } else {
        Write-Host "  Dependency ok: $name" -ForegroundColor Green
    }
}

if (!(Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

Write-Host "=== Checking for C++ Compiler ===" -ForegroundColor Cyan
$HasWindres = $null -ne (Get-Command windres -ErrorAction SilentlyContinue)
$HasGpp = $null -ne (Get-Command g++ -ErrorAction SilentlyContinue)

if ($HasWindres -and $HasGpp) {
    Write-Host "Compiling resources and C++ launcher..." -ForegroundColor Cyan
    try {
        & windres resource.rc -O coff -o resource.res
        & g++ -O3 ytd_launcher.cpp resource.res -o dist/ytd_webview_app.exe -mwindows
        if (Test-Path "resource.res") { Remove-Item -Force resource.res }
        Write-Host "  Launcher compiled successfully -> dist/ytd_webview_app.exe" -ForegroundColor Green
    } catch {
        Write-Host "  Failed to compile C++ launcher: $_" -ForegroundColor Red
        if (Test-Path "resource.res") { Remove-Item -Force resource.res }
    }
} else {
    Write-Host "WARNING: 'g++' or 'windres' was not found on your system PATH." -ForegroundColor Yellow
    Write-Host "Skipping C++ launcher compilation. Pre-compiled dist/ytd_webview_app.exe will be used if present." -ForegroundColor Yellow
    Write-Host "To compile from source, install MinGW-w64 (GCC/binutils) and add it to your PATH." -ForegroundColor Gray
}

Write-Host "=== Compiling Python Backend ===" -ForegroundColor Cyan
if (!(Test-Path "ytd_webview_backend.spec")) {
    Write-Error "ytd_webview_backend.spec not found in the root directory."
}

try {
    & pyinstaller ytd_webview_backend.spec --clean -y
    Write-Host "  Backend compiled successfully -> dist/ytd_webview_backend.exe" -ForegroundColor Green
} catch {
    Write-Error "Failed to compile backend with PyInstaller: $_"
}

Write-Host "=== Build Completed! ===" -ForegroundColor Green
