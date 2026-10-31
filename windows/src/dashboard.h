#pragma once

#include <windows.h>

// Panel visual Matick: estado real del cloud, navegación MVP y mascota vectorial.
// El renderizado principal y las superficies de tarjetas se dibujan con Direct3D 12.
void DashboardInstall(HWND window, HINSTANCE instance);
LRESULT DashboardControlColor(HDC dc, HWND control);
void DashboardCommand(HWND window, UINT commandId);
void DashboardTick();
void DashboardSetCloudStatus(bool healthy);
void DashboardShutdown();

// Se usa para la solicitud de chat asíncrona; sin dependencias externas.
std::wstring DashboardReadChatInput();
void DashboardSetChatResponse(const std::wstring& result, bool ok);
