#include <windows.h>
#include <string>
#include <fstream>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Get the path of the current launcher executable
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);

    std::string path(exePath);
    size_t lastSlash = path.find_last_of("\\/");
    std::string dir = (lastSlash != std::string::npos) ? path.substr(0, lastSlash + 1) : "";

    std::string backendPath = dir + "ytd_webview_backend.exe";

    // Write log file
    std::ofstream log(dir + "launcher.log");
    log << "Launcher started." << std::endl;
    log << "dir: " << dir << std::endl;
    log << "backendPath: " << backendPath << std::endl;

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE; // Start child process hidden

    ZeroMemory(&pi, sizeof(pi));

    // Prepare command line
    std::string cmdLine = "\"" + backendPath + "\" " + lpCmdLine;
    log << "cmdLine: " << cmdLine << std::endl;
    
    char* cmdLinePtr = &cmdLine[0];

    // Launch the child process (set working directory to dir)
    bool success = CreateProcessA(
        NULL,
        cmdLinePtr,
        NULL,
        NULL,
        FALSE,
        0,
        NULL,
        dir.c_str(), // Set working directory to the dist folder
        &si,
        &pi
    );

    if (success) {
        log << "CreateProcessA succeeded. PID: " << pi.dwProcessId << std::endl;
        
        // Wait for the backend process to exit
        log << "Waiting for child process to exit..." << std::endl;
        WaitForSingleObject(pi.hProcess, INFINITE);
        
        DWORD exitCode = 0;
        GetExitCodeProcess(pi.hProcess, &exitCode);
        log << "Child process exited with code: " << exitCode << std::endl;
        
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);

        if (exitCode != 0 && exitCode != 259) {
            std::string msg = "Backend exited with code: " + std::to_string(exitCode);
            MessageBoxA(NULL, msg.c_str(), "Backend Error", MB_ICONERROR | MB_OK);
        }
    } else {
        DWORD err = GetLastError();
        log << "CreateProcessA failed. GetLastError: " << err << std::endl;
        MessageBoxA(NULL, ("Failed to launch backend. Error code: " + std::to_string(err)).c_str(), "Error", MB_ICONERROR | MB_OK);
    }
    
    log << "Launcher exiting." << std::endl;
    log.close();
    return 0;
}
