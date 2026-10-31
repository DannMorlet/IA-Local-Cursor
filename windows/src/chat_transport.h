#pragma once
#include <string>

struct ChatReply {
    bool ok = false;
    std::wstring text;
};

// Sin Node, CUDA ni LM Studio embebidos. Solo HTTP(S) seguro de Windows.
std::wstring MatickReadEnv(const wchar_t* key);
ChatReply MatickSendChat(const std::wstring& baseUrl, const std::wstring& token,
                         const std::wstring& prompt);
