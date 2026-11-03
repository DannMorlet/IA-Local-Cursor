#pragma once
#include <windows.h>
#include <string>

// Arranca ÚNICAMENTE el backend Matick empaquetado, si existe.
// No instala servicios de Windows, no usa aplicaciones externas.
class MatickBackend {
public:
    void StartIfBundled();
    void Stop();
    bool IsAlive() const;
    const std::wstring& Error() const { return error_; }
    ~MatickBackend() { Stop(); }
private:
    std::wstring error_;
    HANDLE job_ = nullptr;
    HANDLE process_ = nullptr;
};
