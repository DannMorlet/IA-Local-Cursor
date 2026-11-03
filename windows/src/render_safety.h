#pragma once
#include <windows.h>

// Diagnóstico local y render alternativo: solo Win32/GDI, sin dependencias externas.
void MatickLog(const wchar_t* event, HRESULT hr = S_OK);
void MatickDrawSafeBackground(HWND window, HDC dc);
bool MatickPreferGDI();

// Escala de interfaz: el diseño está hecho en 1500x850 px a 96 DPI. Se adapta
// al DPI del sistema (Windows 11 con 125 %/150 %) y al área útil del monitor.
constexpr int kDesignWidth = 1500;
constexpr int kDesignHeight = 850;
void MatickInitScale(DWORD windowStyle);
int MatickScale(int designUnits);
