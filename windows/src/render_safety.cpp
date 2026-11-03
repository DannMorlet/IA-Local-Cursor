#include "render_safety.h"
#include <string>
#include <cwchar>
#include <algorithm>
#include <initializer_list>
#include <cmath>

namespace {
std::wstring LocalLogFile() {
    wchar_t local[MAX_PATH] = {};
    DWORD n = GetEnvironmentVariableW(L"LOCALAPPDATA", local, MAX_PATH);
    if (n == 0 || n >= MAX_PATH) return {};
    std::wstring dir = std::wstring(local) + L"\\MatickStudioLM";
    CreateDirectoryW(dir.c_str(), nullptr);
    dir += L"\\logs";
    CreateDirectoryW(dir.c_str(), nullptr);
    return dir + L"\\render.log";
}

void RectFill(HDC dc, HBRUSH brush, LONG l, LONG t, LONG r, LONG b) {
    if (r <= l || b <= t) return;
    const RECT area{l,t,r,b};
    FillRect(dc, &area, brush);
}

double gScale = 1.0;
}

void MatickInitScale(DWORD windowStyle) {
    UINT dpi = GetDpiForSystem();
    if (dpi == 0) dpi = 96;
    double scale = static_cast<double>(dpi) / 96.0;
    RECT work{};
    if (SystemParametersInfoW(SPI_GETWORKAREA, 0, &work, 0)) {
        // Margen no cliente (barra de título y bordes) a este DPI.
        RECT frame{0, 0, 0, 0};
        AdjustWindowRectExForDpi(&frame, windowStyle, FALSE, 0, dpi);
        const double availW = (work.right - work.left) - (frame.right - frame.left);
        const double availH = (work.bottom - work.top) - (frame.bottom - frame.top);
        if (availW > 0 && availH > 0) {
            scale = std::min(scale, availW / kDesignWidth);
            scale = std::min(scale, availH / kDesignHeight);
        }
    }
    gScale = std::max(0.5, scale);
}

int MatickScale(int designUnits) {
    return static_cast<int>(std::lround(designUnits * gScale));
}

void MatickLog(const wchar_t* event, HRESULT hr) {
    if (!event) return;
    wchar_t line[768] = {};
    SYSTEMTIME now{};
    GetLocalTime(&now);
    swprintf_s(line, L"%04u-%02u-%02u %02u:%02u:%02u | %ls | HRESULT 0x%08lX\r\n",
        now.wYear, now.wMonth, now.wDay,
        now.wHour, now.wMinute, now.wSecond, event,
        static_cast<unsigned long>(hr));
    OutputDebugStringW(line);
    const auto path = LocalLogFile();
    if (path.empty()) return;
    HANDLE file = CreateFileW(path.c_str(), FILE_APPEND_DATA,
        FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return;
    int size = WideCharToMultiByte(CP_UTF8, 0, line, -1, nullptr, 0, nullptr, nullptr);
    if (size > 1 && size < 2048) {
        std::string utf8(static_cast<size_t>(size), '\0');
        WideCharToMultiByte(CP_UTF8, 0, line, -1, &utf8[0], size, nullptr, nullptr);
        DWORD written = 0;
        WriteFile(file, utf8.data(), static_cast<DWORD>(utf8.size() - 1), &written, nullptr);
    }
    CloseHandle(file);
}

bool MatickPreferGDI() {
    wchar_t value[24] = {};
    DWORD length = GetEnvironmentVariableW(L"MATICK_RENDERER", value, 24);
    return length && length < 24 && _wcsicmp(value, L"gdi") == 0;
}

void MatickDrawSafeBackground(HWND window, HDC dc) {
    RECT client{};
    GetClientRect(window, &client);
    if (client.right <= 0 || client.bottom <= 0) return;
    const LONG width = client.right, height = client.bottom;
    const auto S = [](LONG v) { return static_cast<LONG>(MatickScale(static_cast<int>(v))); };
    HBRUSH white = CreateSolidBrush(RGB(255,255,255));
    HBRUSH side = CreateSolidBrush(RGB(10,20,36));
    HBRUSH header = CreateSolidBrush(RGB(11,19,34));
    HBRUSH card = CreateSolidBrush(RGB(252,253,255));
    HBRUSH edge = CreateSolidBrush(RGB(225,233,244));
    HBRUSH right = CreateSolidBrush(RGB(11,19,33));
    RectFill(dc, white, 0, 0, width, height);
    RectFill(dc, side, 0, S(66), std::min<LONG>(S(290),width), height);
    RectFill(dc, header, 0, 0, width, std::min<LONG>(S(66),height));
    if (width > S(1180)) RectFill(dc, right, S(1180), S(66), width, height);
    for (const RECT area : {
        RECT{S(308),S(91),S(1164),S(417)}, RECT{S(308),S(457),S(862),S(675)},
        RECT{S(880),S(457),S(1164),S(803)}, RECT{S(308),S(689),S(862),S(803)}}) {
        const LONG right = std::min<LONG>(area.right,width-12);
        const LONG bottom = std::min<LONG>(area.bottom,height-10);
        if (right <= area.left || bottom <= area.top) continue;
        RectFill(dc, card, area.left, area.top, right, bottom);
        const RECT border{area.left,area.top,right,bottom};
        FrameRect(dc, &border, edge);
    }
    DeleteObject(white); DeleteObject(side); DeleteObject(header);
    DeleteObject(card); DeleteObject(edge); DeleteObject(right);
}
