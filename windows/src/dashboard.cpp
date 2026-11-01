// Dashboard Matick Studio LM - versión inicial basada en el diseño aprobado.
// Es una interfaz de Windows integrada con el renderizador Direct3D 12:
// esta capa Win32 dibuja textos, controles accesibles y una mascota vectorial.
#include "dashboard.h"
#include "chat_transport.h"
#include <shellapi.h>
#include <string>
#include <vector>

namespace {
constexpr COLORREF kDark = RGB(10, 20, 36);
constexpr COLORREF kTop = RGB(11, 19, 34);
constexpr COLORREF kRight = RGB(11, 19, 33);
constexpr COLORREF kLight = RGB(241, 246, 251);
constexpr COLORREF kWhite = RGB(255, 255, 255);
constexpr COLORREF kText = RGB(25, 39, 62);
constexpr COLORREF kMuted = RGB(92, 108, 128);
constexpr COLORREF kCyan = RGB(30, 210, 239);

HBRUSH gDarkBrush = nullptr;
HBRUSH gTopBrush = nullptr;
HBRUSH gRightBrush = nullptr;
HBRUSH gLightBrush = nullptr;
HBRUSH gWhiteBrush = nullptr;
std::vector<HFONT> gFonts;
HWND gMascot = nullptr;
HWND gApiStatus = nullptr;
HWND gRendererStatus = nullptr;
HWND gPageTitle = nullptr;
HWND gPageSubtitle = nullptr;
HWND gChatInput = nullptr;
HWND gChatOutput = nullptr;
UINT gTick = 0;
bool gCloudHealthy = false;

HFONT NewFont(int pixelSize, int weight = FW_NORMAL) {
    HFONT font = CreateFontW(-pixelSize, 0, 0, 0, weight,
        FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS,
        CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
        DEFAULT_PITCH | FF_SWISS, L"Segoe UI");
    if (font) gFonts.push_back(font);
    return font;
}

HWND Label(HWND parent, HINSTANCE instance, UINT id, const wchar_t* text,
    int x, int y, int width, int height, int pixelSize = 17,
    int weight = FW_NORMAL) {
    HWND widget = CreateWindowExW(0, L"STATIC", text,
        WS_CHILD | WS_VISIBLE | SS_LEFT | SS_NOTIFY | SS_NOPREFIX,
        x, y, width, height, parent,
        reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)), instance, nullptr);
    SendMessageW(widget, WM_SETFONT,
        reinterpret_cast<WPARAM>(NewFont(pixelSize, weight)), TRUE);
    return widget;
}

void Shape(HDC dc, HBRUSH brush, HPEN pen,
    int left, int top, int right, int bottom, int radius = 0) {
    HGDIOBJ previousBrush = SelectObject(dc, brush);
    HGDIOBJ previousPen = SelectObject(dc, pen);
    if (radius) {
        RoundRect(dc, left, top, right, bottom, radius, radius);
    } else {
        Ellipse(dc, left, top, right, bottom);
    }
    SelectObject(dc, previousPen);
    SelectObject(dc, previousBrush);
}

LRESULT CALLBACK MascotProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
        case WM_ERASEBKGND:
            return 1;
        case WM_PAINT: {
            PAINTSTRUCT paint{};
            HDC dc = BeginPaint(window, &paint);
            RECT area{};
            GetClientRect(window, &area);
            FillRect(dc, &area, gRightBrush);

            HPEN quietPen = CreatePen(PS_SOLID, 2, RGB(16, 101, 160));
            HPEN glowPen = CreatePen(PS_SOLID, 5, kCyan);
            HBRUSH turquoise = CreateSolidBrush(RGB(38, 216, 238));
            HBRUSH navy = CreateSolidBrush(RGB(12, 21, 45));
            HBRUSH shell = CreateSolidBrush(RGB(220, 243, 249));
            HBRUSH shellShade = CreateSolidBrush(RGB(100, 160, 194));
            HBRUSH face = CreateSolidBrush(RGB(8, 23, 44));

            // Pedestal luminoso: no es una fotografía, es un avatar nativo GDI.
            Shape(dc, turquoise, quietPen, 26, 257, 258, 283);
            Shape(dc, navy, glowPen, 43, 255, 243, 275);

            // Orejitas y silueta del robot.
            POINT leftEar[3] = {{48, 73}, {56, 8}, {99, 61}};
            POINT rightEar[3] = {{189, 61}, {232, 8}, {240, 75}};
            HGDIOBJ prevBrush = SelectObject(dc, shell);
            HGDIOBJ prevPen = SelectObject(dc, glowPen);
            Polygon(dc, leftEar, 3);
            Polygon(dc, rightEar, 3);
            SelectObject(dc, turquoise);
            POINT innerLeft[3] = {{66, 54}, {67, 28}, {87, 59}};
            POINT innerRight[3] = {{198, 59}, {222, 28}, {219, 57}};
            Polygon(dc, innerLeft, 3);
            Polygon(dc, innerRight, 3);
            SelectObject(dc, prevPen);
            SelectObject(dc, prevBrush);

            Shape(dc, shellShade, quietPen, 94, 171, 193, 257, 38);
            Shape(dc, shell, quietPen, 80, 162, 207, 240, 36);
            Shape(dc, turquoise, quietPen, 129, 187, 160, 220, 25);

            Shape(dc, shell, glowPen, 29, 54, 259, 194, 72);
            Shape(dc, face, quietPen, 43, 69, 245, 180, 60);
            const bool blink = (gTick % 180 >= 168 && gTick % 180 <= 173);
            if (blink) {
                Shape(dc, turquoise, glowPen, 78, 119, 124, 125, 6);
                Shape(dc, turquoise, glowPen, 169, 119, 215, 125, 6);
            } else {
                Shape(dc, turquoise, glowPen, 79, 106, 123, 137, 22);
                Shape(dc, turquoise, glowPen, 170, 106, 214, 137, 22);
                Shape(dc, face, quietPen, 85, 105, 116, 122, 14);
                Shape(dc, face, quietPen, 176, 105, 207, 122, 14);
            }
            Shape(dc, turquoise, quietPen, 131, 150, 164, 158, 9);

            DeleteObject(quietPen);
            DeleteObject(glowPen);
            DeleteObject(turquoise);
            DeleteObject(navy);
            DeleteObject(shell);
            DeleteObject(shellShade);
            DeleteObject(face);
            EndPaint(window, &paint);
            return 0;
        }
        default:
            return DefWindowProcW(window, message, wParam, lParam);
    }
}

void SetPage(const wchar_t* title, const wchar_t* detail) {
    if (gPageTitle) SetWindowTextW(gPageTitle, title);
    if (gPageSubtitle) SetWindowTextW(gPageSubtitle, detail);
}

}  // namespace

void DashboardInstall(HWND window, HINSTANCE instance) {
    gDarkBrush = CreateSolidBrush(kDark);
    gTopBrush = CreateSolidBrush(kTop);
    gRightBrush = CreateSolidBrush(kRight);
    gLightBrush = CreateSolidBrush(kLight);
    gWhiteBrush = CreateSolidBrush(kWhite);

    WNDCLASSEXW cls{};
    cls.cbSize = sizeof(cls);
    cls.lpfnWndProc = MascotProc;
    cls.hInstance = instance;
    cls.lpszClassName = L"MatickMascotVector";
    cls.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    RegisterClassExW(&cls);

    // Encabezado superior.
    Label(window, instance, 40, L"◈  Matick Studio LM", 20, 16, 267, 38, 24, FW_BOLD);
    Label(window, instance, 41, L"Chat", 320, 22, 76, 29, 18, FW_SEMIBOLD);
    Label(window, instance, 42, L"Trabajo", 425, 22, 92, 29, 18);
    Label(window, instance, 43, L"Codex", 560, 22, 86, 29, 18);
    Label(window, instance, 44, L"Agentes", 668, 22, 100, 29, 18);
    Label(window, instance, 45, L"Modelos", 801, 22, 100, 29, 18);
    Label(window, instance, 46, L"Herramientas", 927, 22, 142, 29, 18);
    Label(window, instance, 47, L"DirectX 12", 1306, 22, 156, 29, 17, FW_SEMIBOLD);
    HWND workButton = CreateWindowExW(0, L"BUTTON", L"Abrir Matick Work",
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
        1097, 15, 193, 39, window, reinterpret_cast<HMENU>(250), instance, nullptr);
    SendMessageW(workButton, WM_SETFONT,
        reinterpret_cast<WPARAM>(NewFont(17, FW_SEMIBOLD)), TRUE);

    // Navegación lateral (primera fase: vistas de demostración).
    Label(window, instance, 1, L"+  Nuevo chat", 21, 89, 253, 36, 21, FW_SEMIBOLD);
    Label(window, instance, 10, L"⌂   Inicio", 25, 153, 245, 29, 17, FW_SEMIBOLD);
    Label(window, instance, 11, L"▤   Chat", 25, 191, 245, 29, 17);
    Label(window, instance, 12, L"▣   Matick Codex", 25, 229, 245, 29, 17);
    Label(window, instance, 13, L"◉   Agentes (6 frentes)", 25, 267, 245, 29, 17);
    Label(window, instance, 14, L"◈   Modelos de IA", 25, 305, 245, 29, 17);
    Label(window, instance, 15, L"⚙   Herramientas", 25, 343, 245, 29, 17);
    Label(window, instance, 16, L"▣   Archivos", 25, 381, 245, 29, 17);
    Label(window, instance, 17, L"☁   Dispositivos", 25, 419, 245, 29, 17);
    Label(window, instance, 18, L"⚙   Configuración", 25, 457, 245, 29, 17);
    Label(window, instance, 30, L"PROYECTOS", 25, 523, 235, 27, 16, FW_BOLD);
    Label(window, instance, 31, L"Matick Studio LM Cloud", 25, 558, 260, 27, 16);
    Label(window, instance, 32, L"Manguito.exe", 25, 597, 255, 27, 16);
    Label(window, instance, 33, L"Alexa + Echo Dot 5", 25, 636, 255, 27, 16);
    Label(window, instance, 34, L"Matick Reloj (Galaxy Fit 3)", 25, 675, 255, 29, 16);
    Label(window, instance, 35, L"GitHub: IA-Local-Cursor", 25, 714, 255, 29, 16);
    Label(window, instance, 36, L"DISEÑO EN PROGRESO", 25, 791, 245, 26, 15);

    // Área de trabajo central clara.
    gPageTitle = Label(window, instance, 70, L"Matick Studio LM", 327, 120, 778, 49, 31, FW_BOLD);
    gPageSubtitle = Label(window, instance, 71, L"¿En qué trabajamos hoy?", 327, 171, 810, 37, 23);
    Label(window, instance, 72, L"Chat  ·  Codex  ·  Analizar archivos  ·  Crear proyecto  ·  Control del PC", 327, 228, 806, 31, 17);
    Label(window, instance, 73, L"Chat en la nube  ·  requiere MATICK_TOKEN y proveedor configurado:", 328, 283, 816, 25, 15);
    gChatInput = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_AUTOHSCROLL,
        329, 318, 641, 40, window, reinterpret_cast<HMENU>(200), instance, nullptr);
    SendMessageW(gChatInput, WM_SETFONT, reinterpret_cast<WPARAM>(NewFont(18)), TRUE);
    HWND send = CreateWindowExW(0, L"BUTTON", L"Enviar",
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
        990, 318, 132, 40, window,
        reinterpret_cast<HMENU>(201), instance, nullptr);
    SendMessageW(send, WM_SETFONT, reinterpret_cast<WPARAM>(NewFont(17, FW_SEMIBOLD)), TRUE);
    Label(window, instance, 74, L"Chat: solo funciona al configurar un modelo. /health no prueba IA.", 329, 377, 818, 27, 16);
    gRendererStatus = Label(window, instance, 75,
        L"Iniciando interfaz visual...", 329, 405, 818, 27, 15);

    Label(window, instance, 80, L"6 FRENTES DE TRABAJO  ·  NO ACTIVOS AÚN", 324, 472, 520, 28, 18, FW_BOLD);
    Label(window, instance, 81, L"Arquitectura", 334, 526, 158, 26, 17, FW_SEMIBOLD);
    Label(window, instance, 82, L"Interfaz DX12", 512, 526, 157, 26, 17, FW_SEMIBOLD);
    Label(window, instance, 83, L"Modelos IA", 689, 526, 154, 26, 17, FW_SEMIBOLD);
    Label(window, instance, 84, L"Programación", 334, 602, 156, 26, 17, FW_SEMIBOLD);
    Label(window, instance, 85, L"Integraciones", 512, 602, 158, 26, 17, FW_SEMIBOLD);
    Label(window, instance, 86, L"Pruebas / CI", 689, 602, 156, 26, 17, FW_SEMIBOLD);
    Label(window, instance, 90, L"MODELOS  ·  ESTADO REAL", 895, 472, 262, 31, 18, FW_BOLD);
    Label(window, instance, 91, L"Matick-Gemma 4    pendiente", 896, 523, 261, 28, 16);
    Label(window, instance, 92, L"Qwen               pendiente", 896, 579, 261, 28, 16);
    Label(window, instance, 93, L"Phi / NPU          pendiente", 896, 635, 261, 28, 16);
    Label(window, instance, 94, L"Sin modelo cloud conectado", 896, 702, 260, 29, 15);
    Label(window, instance, 100, L"ACTIVIDAD RECIENTE", 324, 702, 500, 28, 18, FW_BOLD);
    gChatOutput = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT",
        L"Respuestas de Matick Cloud aparecerán aquí. Sin modelo configurado, se indicará el error.",
        WS_CHILD | WS_VISIBLE | ES_MULTILINE | ES_READONLY |
        ES_AUTOVSCROLL | WS_VSCROLL,
        323, 741, 530, 61, window, reinterpret_cast<HMENU>(202), instance, nullptr);
    SendMessageW(gChatOutput, WM_SETFONT, reinterpret_cast<WPARAM>(NewFont(15)), TRUE);

    // Panel derecho: mascota y telemetría sin métricas inventadas.
    Label(window, instance, 120, L"MATICK  ·  MASCOTA", 1202, 89, 278, 30, 20, FW_BOLD);
    gMascot = CreateWindowExW(0, L"MatickMascotVector", L"",
        WS_CHILD | WS_VISIBLE, 1202, 126, 282, 298,
        window, nullptr, instance, nullptr);
    Label(window, instance, 121, L"¡Aquí ando!   ◡̈", 1224, 425, 238, 30, 20, FW_BOLD);
    Label(window, instance, 125, L"Parpadeo animado  ·  avatar provisional", 1204, 451, 276, 22, 13);
    Label(window, instance, 123, L"ESTADO DE CONEXIÓN", 1212, 496, 267, 27, 18, FW_BOLD);
    gApiStatus = Label(window, instance, 122, L"API: comprobando...", 1213, 541, 265, 27, 17, FW_SEMIBOLD);
    Label(window, instance, 126, L"ChatGPT: no integrado", 1213, 584, 261, 26, 16);
    Label(window, instance, 127, L"Alexa: no integrada", 1213, 621, 261, 26, 16);
    Label(window, instance, 128, L"Reloj: no integrado", 1213, 658, 261, 26, 16);
    Label(window, instance, 129, L"Matick Codex: pendiente", 1213, 695, 264, 26, 16);
    Label(window, instance, 130, L"GPU / CPU / NPU: sin lecturas", 1213, 746, 267, 30, 15);
}

LRESULT DashboardControlColor(HDC dc, HWND control) {
    const int id = GetDlgCtrlID(control);
    SetBkMode(dc, OPAQUE);
    if (id >= 120) {
        SetBkColor(dc, kRight);
        SetTextColor(dc, id == 122 && gCloudHealthy ? RGB(80, 239, 160) : RGB(222, 240, 246));
        return reinterpret_cast<LRESULT>(gRightBrush);
    }
    if (id >= 70) {
        SetBkColor(dc, kWhite);
        SetTextColor(dc, id == 73 || id == 74 || id == 94 || id == 102 ? kMuted : kText);
        return reinterpret_cast<LRESULT>(gWhiteBrush);
    }
    if (id >= 40) {
        SetBkColor(dc, kTop);
        SetTextColor(dc, id == 41 ? kCyan : RGB(221, 237, 247));
        return reinterpret_cast<LRESULT>(gTopBrush);
    }
    SetBkColor(dc, kDark);
    SetTextColor(dc, id == 36 ? kCyan : RGB(215, 236, 250));
    return reinterpret_cast<LRESULT>(gDarkBrush);
}

void DashboardSetCloudStatus(bool healthy) {
    gCloudHealthy = healthy;
    if (gApiStatus) {
        SetWindowTextW(gApiStatus, healthy
            ? L"API cloud: accesible /health"
            : L"API cloud: desconectada");
        InvalidateRect(gApiStatus, nullptr, TRUE);
    }
}

void DashboardCommand(HWND window, UINT id) {
    switch (id) {
        case 1:
        case 10:
        case 41:
            SetPage(L"Matick Studio LM", L"¿En qué trabajamos hoy?");
            break;
        case 11:
            SetPage(L"Matick Chat", L"Chat visual: conectar el modelo es el siguiente paso.");
            break;
        case 12:
        case 43:
            SetPage(L"Matick Codex", L"Agente de código propio: integración pendiente.");
            break;
        case 13:
        case 44:
            SetPage(L"Seis frentes de trabajo", L"Organización del proyecto, no agentes en ejecución.");
            break;
        case 14:
        case 45:
            SetPage(L"Modelos de IA", L"No hay un modelo cloud configurado.");
            break;
        case 15:
        case 46:
            SetPage(L"Herramientas", L"Conectores y herramientas en desarrollo.");
            break;
        case 16:
            SetPage(L"Archivos", L"Gestor de archivos: pendiente.");
            break;
        case 17:
            SetPage(L"Dispositivos", L"Alexa y reloj: todavía no conectados.");
            break;
        case 18:
            SetPage(L"Configuración", L"Parámetros de Matick: próximamente.");
            break;
        case 42:
            SetPage(L"Trabajo", L"Panel de tareas en desarrollo.");
            break;
        case 250: {
            std::wstring base = MatickReadEnv(L"MATICK_CLOUD_URL");
            if (base.empty()) base = L"http://127.0.0.1:8787";
            if (base.rfind(L"http://127.0.0.1:", 0) != 0 &&
                base.rfind(L"http://localhost:", 0) != 0 &&
                base.rfind(L"https://", 0) != 0) {
                MessageBoxW(window, L"Solo HTTP local o HTTPS remoto.", L"Matick Work", MB_ICONWARNING);
                break;
            }
            while (!base.empty() && base.back() == L'/') base.pop_back();
            const std::wstring url = base + L"/app";
            HINSTANCE handle = ShellExecuteW(window, L"open", url.c_str(),
                nullptr, nullptr, SW_SHOWNORMAL);
            if (reinterpret_cast<INT_PTR>(handle) <= 32)
                MessageBoxW(window, L"No se pudo abrir Matick Work en el navegador.",
                            L"Matick Work", MB_ICONWARNING);
            break;
        }
        case 201:
            PostMessageW(window, WM_APP + 2, 0, 0);
            break;
        default:
            break;
    }
}

void DashboardTick() {
    ++gTick;
    // Los ojos parpadean cada seis segundos aprox. El avatar no realiza inferencia.
    if (gMascot && gTick % 6 == 0) InvalidateRect(gMascot, nullptr, FALSE);
}

void DashboardShutdown() {
    for (HFONT font : gFonts) DeleteObject(font);
    gFonts.clear();
    if (gDarkBrush) DeleteObject(gDarkBrush);
    if (gTopBrush) DeleteObject(gTopBrush);
    if (gRightBrush) DeleteObject(gRightBrush);
    if (gLightBrush) DeleteObject(gLightBrush);
    if (gWhiteBrush) DeleteObject(gWhiteBrush);
}

std::wstring DashboardReadChatInput() {
    if (!gChatInput) return {};
    const int size = GetWindowTextLengthW(gChatInput);
    if (size <= 0 || size > 3000) return {};
    std::wstring text(static_cast<size_t>(size) + 1, L'\0');
    GetWindowTextW(gChatInput, &text[0], size + 1);
    text.resize(static_cast<size_t>(size));
    return text;
}

void DashboardSetChatResponse(const std::wstring& result, bool ok) {
    if (!gChatOutput) return;
    const std::wstring output = result.size() > 12000
        ? result.substr(0, 12000) : result;
    SetWindowTextW(gChatOutput, output.c_str());
    SendMessageW(gChatOutput, EM_SETSEL, 0, 0);
    (void)ok;
}

void DashboardSetRendererStatus(bool dx12Ready) {
    if (!gRendererStatus) return;
    SetWindowTextW(gRendererStatus, dx12Ready
        ? L"Interfaz: DirectX 12 operativo"
        : L"Interfaz: modo seguro GDI - revisa %LOCALAPPDATA%\\MatickStudioLM\\logs\\render.log");
    InvalidateRect(gRendererStatus, nullptr, TRUE);
}
