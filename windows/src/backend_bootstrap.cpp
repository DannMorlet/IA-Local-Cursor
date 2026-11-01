#include "backend_bootstrap.h"
#include "render_safety.h"
#include <bcrypt.h>
#include <string>
#include <vector>
#pragma comment(lib, "bcrypt.lib")

namespace {
bool IsRegularFile(const std::wstring& path) {
    DWORD attrs = GetFileAttributesW(path.c_str());
    return attrs != INVALID_FILE_ATTRIBUTES && !(attrs & FILE_ATTRIBUTE_DIRECTORY);
}

std::wstring InstalledRoot() {
    std::vector<wchar_t> buffer(32768, L'\0');
    DWORD len = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!len || len >= buffer.size()) return {};
    std::wstring exe(buffer.data(), len);
    const auto slash = exe.find_last_of(L"\\/");
    return slash == std::wstring::npos ? std::wstring() : exe.substr(0, slash);
}

std::wstring UserDataPath() {
    wchar_t local[32768] = {};
    DWORD len = GetEnvironmentVariableW(L"LOCALAPPDATA", local, 32768);
    if (!len || len >= 32768) return {};
    std::wstring root(local);
    root += L"\\MatickStudioLM";
    CreateDirectoryW(root.c_str(), nullptr);
    return root;
}

std::wstring RandomToken() {
    unsigned char bytes[32] = {};
    if (BCryptGenRandom(nullptr, bytes, sizeof(bytes), BCRYPT_USE_SYSTEM_PREFERRED_RNG) < 0)
        return {};
    constexpr wchar_t digits[] = L"0123456789abcdef";
    std::wstring token;
    token.reserve(64);
    for (unsigned char byte : bytes) {
        token.push_back(digits[byte >> 4]);
        token.push_back(digits[byte & 15]);
    }
    SecureZeroMemory(bytes, sizeof(bytes));
    return token;
}
}

void MatickBackend::StartIfBundled() {
    // Un usuario puede elegir expresamente su propia nube. Respetar el entorno.
    if (GetEnvironmentVariableW(L"MATICK_CLOUD_URL", nullptr, 0) != 0 ||
        GetEnvironmentVariableW(L"MATICK_TOKEN", nullptr, 0) != 0 ||
        GetEnvironmentVariableW(L"MATICK_TOKENS_JSON", nullptr, 0) != 0) {
        MatickLog(L"BACKEND_EXTERNAL_CONFIG_PRESERVED");
        return;
    }
    const auto root = InstalledRoot();
    if (root.empty()) return;
    const auto python = root + L"\\runtime\\python.exe";
    const auto server = root + L"\\cloud\\matick_cloud\\__main__.py";
    if (!IsRegularFile(python) || !IsRegularFile(server)) {
        MatickLog(L"BACKEND_EMBEDDED_RUNTIME_NOT_INSTALLED");
        return;
    }
    const auto userdata = UserDataPath();
    if (userdata.empty()) {
        MatickLog(L"BACKEND_USER_DATA_PATH_UNAVAILABLE");
        return;
    }
    const auto data = userdata + L"\\data";
    const auto logs = userdata + L"\\logs";
    CreateDirectoryW(data.c_str(), nullptr);
    CreateDirectoryW(logs.c_str(), nullptr);
    const auto token = RandomToken();
    if (token.empty()) {
        MatickLog(L"BACKEND_TOKEN_GENERATION_FAILED");
        return;
    }
    std::wstring tokenJson = L"{\"windows-dx12\":\"" + token + L"\"}";
    SetEnvironmentVariableW(L"MATICK_TOKEN", token.c_str());
    SetEnvironmentVariableW(L"MATICK_TOKENS_JSON", tokenJson.c_str());
    SetEnvironmentVariableW(L"MATICK_HOST", L"127.0.0.1");
    SetEnvironmentVariableW(L"MATICK_PORT", L"8787");
    const auto dbPath = data + L"\\events.sqlite";
    SetEnvironmentVariableW(L"MATICK_DB_PATH", dbPath.c_str());
    SecureZeroMemory(tokenJson.data(), tokenJson.size() * sizeof(wchar_t));

    SECURITY_ATTRIBUTES sa{};
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;
    HANDLE log = CreateFileW((logs + L"\\backend.log").c_str(), FILE_APPEND_DATA,
        FILE_SHARE_READ, &sa, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    HANDLE input = CreateFileW(L"NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
        &sa, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    STARTUPINFOW start{};
    start.cb = sizeof(start);
    start.dwFlags = STARTF_USESTDHANDLES;
    start.hStdInput = input != INVALID_HANDLE_VALUE ? input : nullptr;
    start.hStdOutput = log != INVALID_HANDLE_VALUE ? log : nullptr;
    start.hStdError = start.hStdOutput;

    PROCESS_INFORMATION proc{};
    std::wstring command = L"\"" + python + L"\" -m matick_cloud";
    job_ = CreateJobObjectW(nullptr, nullptr);
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limit{};
    limit.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if (!job_ || !SetInformationJobObject(job_, JobObjectExtendedLimitInformation,
        &limit, sizeof(limit))) {
        MatickLog(L"BACKEND_JOB_CREATE_FAILED", HRESULT_FROM_WIN32(GetLastError()));
        Stop();
    } else if (!CreateProcessW(python.c_str(), command.data(), nullptr, nullptr, TRUE,
        CREATE_NO_WINDOW | CREATE_SUSPENDED, nullptr, root.c_str(), &start, &proc)) {
        MatickLog(L"BACKEND_PROCESS_CREATE_FAILED", HRESULT_FROM_WIN32(GetLastError()));
        Stop();
    } else {
        if (!AssignProcessToJobObject(job_, proc.hProcess)) {
            MatickLog(L"BACKEND_JOB_ATTACH_FAILED", HRESULT_FROM_WIN32(GetLastError()));
            TerminateProcess(proc.hProcess, 1); // Solo el proceso que acabamos de crear.
            CloseHandle(proc.hProcess);
            Stop();
        } else {
            process_ = proc.hProcess;
            if (ResumeThread(proc.hThread) == DWORD(-1)) {
                MatickLog(L"BACKEND_RESUME_FAILED", HRESULT_FROM_WIN32(GetLastError()));
                Stop();
            } else {
                MatickLog(L"BACKEND_STARTED_ISOLATED");
            }
        }
        CloseHandle(proc.hThread);
    }
    if (input != INVALID_HANDLE_VALUE) CloseHandle(input);
    if (log != INVALID_HANDLE_VALUE) CloseHandle(log);
}

void MatickBackend::Stop() {
    // Cerrar el Job termina solo el backend hijo, nunca servidores ajenos.
    if (job_) { CloseHandle(job_); job_ = nullptr; }
    if (process_) { CloseHandle(process_); process_ = nullptr; }
}
