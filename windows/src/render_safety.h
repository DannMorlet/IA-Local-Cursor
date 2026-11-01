#pragma once
#include <windows.h>

// Diagnóstico local y render alternativo: solo Win32/GDI, sin dependencias externas.
void MatickLog(const wchar_t* event, HRESULT hr = S_OK);
void MatickDrawSafeBackground(HWND window, HDC dc);
bool MatickPreferGDI();
