#pragma once
#include <windows.h>

// Arranca ÚNICAMENTE el backend Matick empaquetado, si existe.
// No instala servicios de Windows, no usa aplicaciones externas.
class MatickBackend {
public:
    void StartIfBundled();
    void Stop();
    ~MatickBackend() { Stop(); }
private:
    HANDLE job_ = nullptr;
    HANDLE process_ = nullptr;
};
