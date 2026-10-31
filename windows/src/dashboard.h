#pragma once

#include <windows.h>

// Panel visual Matick: estado real del cloud, navegación MVP y mascota vectorial.
// El renderizado principal y las superficies de tarjetas se dibujan con Direct3D 12.
void DashboardInstall(HWND window, HINSTANCE instance);
LRESULT DashboardControlColor(HDC dc, HWND control);
void DashboardCommand(HWND window, UINT commandId);
void DashboardTick();
// Estado del servicio cloud y de su sesión autenticada (no de los demás conectores).
enum class CloudConnectionState {
    NoConfigurado = 0,
    Desconectado = 1,
    SinSesion = 2,
    Conectado = 3,
};
void DashboardSetCloudStatus(CloudConnectionState state);
void DashboardShutdown();
