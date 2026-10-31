#include "chat_transport.h"
#include <windows.h>
#include <winhttp.h>
#include <algorithm>
#include <string>
#include <vector>

namespace {
std::string ToUtf8(const std::wstring& s) {
    if (s.empty()) return {};
    const int len = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS,
        s.c_str(), static_cast<int>(s.size()), nullptr, 0, nullptr, nullptr);
    if (!len) return {};
    std::string out(static_cast<size_t>(len), '\0');
    if (!WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS,
        s.c_str(), static_cast<int>(s.size()), &out[0], len, nullptr, nullptr)) return {};
    return out;
}

std::wstring FromUtf8(const std::string& s) {
    if (s.empty()) return {};
    const int len = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS,
        s.data(), static_cast<int>(s.size()), nullptr, 0);
    if (!len) return L"Respuesta UTF-8 inválida.";
    std::wstring out(static_cast<size_t>(len), L'\0');
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, s.data(),
        static_cast<int>(s.size()), &out[0], len);
    return out;
}

std::string EscapeJson(const std::string& source) {
    std::string out;
    for (unsigned char c : source) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (c < 32) {
                    const char* digits = "0123456789abcdef";
                    out += "\\u00";
                    out.push_back(digits[(c >> 4) & 15]);
                    out.push_back(digits[c & 15]);
                } else {
                    out.push_back(static_cast<char>(c));
                }
        }
    }
    return out;
}
}

std::wstring MatickReadEnv(const wchar_t* key) {
    const DWORD length = GetEnvironmentVariableW(key, nullptr, 0);
    if (!length || length > 8192) return {};
    std::vector<wchar_t> buffer(length, 0);
    if (!GetEnvironmentVariableW(key, buffer.data(), length)) return {};
    return std::wstring(buffer.data());
}

ChatReply MatickSendChat(const std::wstring& baseUrl, const std::wstring& token,
                         const std::wstring& prompt) {
    if (token.empty()) return {false, L"Configura MATICK_TOKEN para autenticar la conversación."};
    if (prompt.empty() || prompt.size() > 3000) {
        return {false, L"Escribe un mensaje de 1 a 3000 caracteres."};
    }
    if (token.find(L'\r') != std::wstring::npos || token.find(L'\n') != std::wstring::npos)
        return {false, L"MATICK_TOKEN contiene caracteres inválidos."};

    URL_COMPONENTS parts{};
    parts.dwStructSize = sizeof(parts);
    parts.dwHostNameLength = static_cast<DWORD>(-1);
    parts.dwUrlPathLength = static_cast<DWORD>(-1);
    parts.dwExtraInfoLength = static_cast<DWORD>(-1);
    if (!WinHttpCrackUrl(baseUrl.c_str(), 0, 0, &parts))
        return {false, L"MATICK_CLOUD_URL inválida."};
    const std::wstring host(parts.lpszHostName, parts.dwHostNameLength);
    if (parts.dwExtraInfoLength > 0)
        return {false, L"MATICK_CLOUD_URL no debe contener parámetros."};
    if (parts.nScheme != INTERNET_SCHEME_HTTP && parts.nScheme != INTERNET_SCHEME_HTTPS)
        return {false, L"El servidor debe usar HTTP local o HTTPS remoto."};
    if (parts.nScheme == INTERNET_SCHEME_HTTP &&
        host != L"localhost" && host != L"127.0.0.1" && host != L"[::1]" && host != L"::1")
        return {false, L"Para una nube remota se requiere HTTPS y un certificado válido."};

    std::wstring path = parts.dwUrlPathLength
        ? std::wstring(parts.lpszUrlPath, parts.dwUrlPathLength) : L"/";
    if (!path.empty() && path.back() == L'/') path.pop_back();
    path += L"/v1/chat";

    const std::string message = ToUtf8(prompt);
    if (message.empty()) return {false, L"Mensaje Unicode no válido."};
    const std::string payload =
        "{\"messages\":[{\"role\":\"user\",\"content\":\"" +
        EscapeJson(message) + "\"}]}";

    HINTERNET session = WinHttpOpen(L"MatickStudioLM/0.2",
        WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!session) return {false, L"Windows no pudo iniciar la conexión."};
    WinHttpSetTimeouts(session, 3000, 3000, 5000, 20000);
    HINTERNET connection = WinHttpConnect(session, host.c_str(), parts.nPort, 0);
    HINTERNET request = connection ? WinHttpOpenRequest(connection, L"POST",
        path.c_str(), nullptr, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES,
        parts.nScheme == INTERNET_SCHEME_HTTPS ? WINHTTP_FLAG_SECURE : 0) : nullptr;
    ChatReply reply{false, L"No se pudo contactar Matick Cloud. Revisa la URL y el servicio."};
    if (request) {
        const std::wstring headers = L"Content-Type: application/json\r\nAccept: text/plain\r\nAuthorization: Bearer " + token + L"\r\n";
        const bool sent = WinHttpSendRequest(request, headers.c_str(),
            static_cast<DWORD>(headers.length()),
            const_cast<char*>(payload.data()),
            static_cast<DWORD>(payload.size()),
            static_cast<DWORD>(payload.size()), 0);
        if (sent && WinHttpReceiveResponse(request, nullptr)) {
            DWORD status = 0;
            DWORD len = sizeof(status);
            if (WinHttpQueryHeaders(request,
                WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                WINHTTP_HEADER_NAME_BY_INDEX, &status, &len, WINHTTP_NO_HEADER_INDEX)) {
                std::string bytes;
                DWORD chunkSize = 0;
                while (bytes.size() < 14000 &&
                       WinHttpQueryDataAvailable(request, &chunkSize) && chunkSize > 0) {
                    const DWORD desired = static_cast<DWORD>(std::min<size_t>(
                        chunkSize, 14000 - bytes.size()));
                    std::string chunk(desired, '\0');
                    DWORD received = 0;
                    if (!WinHttpReadData(request, &chunk[0], desired, &received) || !received) break;
                    bytes.append(chunk.data(), received);
                }
                if (status == 200) {
                    reply = {true, FromUtf8(bytes)};
                } else if (status == 401) {
                    reply = {false, L"Acceso denegado. Revisa MATICK_TOKEN del cliente Windows."};
                } else if (status == 503) {
                    reply = {false, L"El servidor responde, pero no hay un modelo listo. Configura MATICK_MODEL_BASE_URL y MATICK_MODEL_ID."};
                } else {
                    reply = {false, L"Matick Cloud devolvió un error HTTP " + std::to_wstring(status)};
                }
            }
        }
    }
    if (request) WinHttpCloseHandle(request);
    if (connection) WinHttpCloseHandle(connection);
    WinHttpCloseHandle(session);
    return reply;
}
