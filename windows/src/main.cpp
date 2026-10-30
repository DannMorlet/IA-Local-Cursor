// Matick Studio LM - Interfaz nativa Direct3D 12 para Windows 11.
// Este MVP comprueba GET /health sin secretos. La mensajería privada es trabajo futuro.
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <winhttp.h>

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using Microsoft::WRL::ComPtr;

namespace {
constexpr UINT kFrames = 2;
constexpr UINT kWidth = 1160;
constexpr UINT kHeight = 740;
constexpr UINT kHealthMessage = WM_APP + 1;
HWND gStatus = nullptr;
HBRUSH gSideBrush = nullptr;
HBRUSH gCardBrush = nullptr;

void Check(HRESULT result) {
    if (FAILED(result)) {
        throw std::runtime_error("No se pudo inicializar o dibujar con Direct3D 12.");
    }
}

struct Renderer {
    ComPtr<ID3D12Device> device;
    ComPtr<ID3D12CommandQueue> queue;
    ComPtr<IDXGISwapChain3> swapChain;
    ComPtr<ID3D12DescriptorHeap> rtvHeap;
    ComPtr<ID3D12Resource> targets[kFrames];
    ComPtr<ID3D12CommandAllocator> allocators[kFrames];
    ComPtr<ID3D12GraphicsCommandList> commands;
    ComPtr<ID3D12Fence> fence;
    UINT rtvSize = 0;
    UINT current = 0;
    UINT64 nextFence = 0;
    UINT64 frameFence[kFrames] = {};
    HANDLE fenceEvent = nullptr;
    bool initialized = false;

    void Init(HWND window) {
        ComPtr<IDXGIFactory4> factory;
        Check(CreateDXGIFactory2(0, IID_PPV_ARGS(&factory)));
        Check(D3D12CreateDevice(nullptr, D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&device)));

        D3D12_COMMAND_QUEUE_DESC queueDesc = {};
        queueDesc.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
        Check(device->CreateCommandQueue(&queueDesc, IID_PPV_ARGS(&queue)));

        DXGI_SWAP_CHAIN_DESC1 swapDesc = {};
        swapDesc.Width = kWidth;
        swapDesc.Height = kHeight;
        swapDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
        swapDesc.SampleDesc.Count = 1;
        swapDesc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
        swapDesc.BufferCount = kFrames;
        swapDesc.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
        ComPtr<IDXGISwapChain1> swap1;
        Check(factory->CreateSwapChainForHwnd(
            queue.Get(), window, &swapDesc, nullptr, nullptr, &swap1
        ));
        Check(factory->MakeWindowAssociation(window, DXGI_MWA_NO_ALT_ENTER));
        Check(swap1.As(&swapChain));
        current = swapChain->GetCurrentBackBufferIndex();

        D3D12_DESCRIPTOR_HEAP_DESC heapDesc = {};
        heapDesc.NumDescriptors = kFrames;
        heapDesc.Type = D3D12_DESCRIPTOR_HEAP_TYPE_RTV;
        Check(device->CreateDescriptorHeap(&heapDesc, IID_PPV_ARGS(&rtvHeap)));
        rtvSize = device->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_RTV);

        D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvHeap->GetCPUDescriptorHandleForHeapStart();
        for (UINT index = 0; index < kFrames; ++index) {
            Check(swapChain->GetBuffer(index, IID_PPV_ARGS(&targets[index])));
            device->CreateRenderTargetView(targets[index].Get(), nullptr, rtv);
            rtv.ptr += rtvSize;
            Check(device->CreateCommandAllocator(
                D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(&allocators[index])
            ));
        }
        Check(device->CreateCommandList(
            0, D3D12_COMMAND_LIST_TYPE_DIRECT,
            allocators[current].Get(), nullptr, IID_PPV_ARGS(&commands)
        ));
        Check(commands->Close());
        Check(device->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fence)));
        fenceEvent = CreateEventW(nullptr, FALSE, FALSE, nullptr);
        if (!fenceEvent) {
            throw std::runtime_error("No se pudo crear el evento de sincronización.");
        }
        initialized = true;
    }

    void WaitValue(UINT64 value) {
        if (value == 0 || fence->GetCompletedValue() >= value) {
            return;
        }
        Check(fence->SetEventOnCompletion(value, fenceEvent));
        WaitForSingleObject(fenceEvent, INFINITE);
    }

    void Render() {
        if (!initialized) {
            return;
        }
        WaitValue(frameFence[current]);
        Check(allocators[current]->Reset());
        Check(commands->Reset(allocators[current].Get(), nullptr));

        D3D12_RESOURCE_BARRIER barrier = {};
        barrier.Type = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
        barrier.Transition.pResource = targets[current].Get();
        barrier.Transition.Subresource = D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
        barrier.Transition.StateBefore = D3D12_RESOURCE_STATE_PRESENT;
        barrier.Transition.StateAfter = D3D12_RESOURCE_STATE_RENDER_TARGET;
        commands->ResourceBarrier(1, &barrier);

        D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvHeap->GetCPUDescriptorHandleForHeapStart();
        rtv.ptr += static_cast<SIZE_T>(current) * rtvSize;
        const FLOAT background[4] = {0.035f, 0.055f, 0.095f, 1.0f};
        const FLOAT sidebar[4] = {0.055f, 0.086f, 0.145f, 1.0f};
        const FLOAT panel[4] = {0.078f, 0.122f, 0.200f, 1.0f};
        const FLOAT highlight[4] = {0.0f, 0.72f, 0.76f, 1.0f};
        const FLOAT topbar[4] = {0.067f, 0.106f, 0.165f, 1.0f};

        commands->ClearRenderTargetView(rtv, background, 0, nullptr);
        const RECT sideRect = {0, 0, 270, static_cast<LONG>(kHeight)};
        const RECT headerRect = {270, 0, static_cast<LONG>(kWidth), 76};
        const RECT panelRect = {302, 111, 1125, 514};
        const RECT lineRect = {302, 111, 1125, 115};
        const RECT bottomRect = {302, 536, 1125, 678};
        commands->ClearRenderTargetView(rtv, sidebar, 1, &sideRect);
        commands->ClearRenderTargetView(rtv, topbar, 1, &headerRect);
        commands->ClearRenderTargetView(rtv, panel, 1, &panelRect);
        commands->ClearRenderTargetView(rtv, highlight, 1, &lineRect);
        commands->ClearRenderTargetView(rtv, panel, 1, &bottomRect);

        std::swap(barrier.Transition.StateBefore, barrier.Transition.StateAfter);
        commands->ResourceBarrier(1, &barrier);
        Check(commands->Close());
        ID3D12CommandList* lists[] = {commands.Get()};
        queue->ExecuteCommandLists(1, lists);
        Check(swapChain->Present(1, 0));
        ++nextFence;
        Check(queue->Signal(fence.Get(), nextFence));
        frameFence[current] = nextFence;
        current = swapChain->GetCurrentBackBufferIndex();
    }

    void Finish() {
        if (!initialized || !fenceEvent) {
            return;
        }
        ++nextFence;
        if (SUCCEEDED(queue->Signal(fence.Get(), nextFence))) {
            try {
                WaitValue(nextFence);
            } catch (...) {
                // Liberar el evento incluso si se pierde el dispositivo.
            }
        }
        CloseHandle(fenceEvent);
        fenceEvent = nullptr;
        initialized = false;
    }

    ~Renderer() {
        Finish();
    }
};

std::wstring CloudURL() {
    DWORD length = GetEnvironmentVariableW(L"MATICK_CLOUD_URL", nullptr, 0);
    if (length == 0 || length > 4096) {
        return L"http://127.0.0.1:8787";
    }
    std::vector<wchar_t> buffer(length, L'\0');
    if (!GetEnvironmentVariableW(L"MATICK_CLOUD_URL", buffer.data(), length)) {
        return L"http://127.0.0.1:8787";
    }
    std::wstring value(buffer.data());
    while (!value.empty() && value.back() == L'/') {
        value.pop_back();
    }
    return value;
}

bool IsCloudHealthy(const std::wstring& base) {
    URL_COMPONENTS parts = {};
    parts.dwStructSize = sizeof(parts);
    parts.dwHostNameLength = static_cast<DWORD>(-1);
    parts.dwUrlPathLength = static_cast<DWORD>(-1);
    if (!WinHttpCrackUrl(base.c_str(), 0, 0, &parts)) {
        return false;
    }
    if (parts.nScheme != INTERNET_SCHEME_HTTP && parts.nScheme != INTERNET_SCHEME_HTTPS) {
        return false;
    }
    std::wstring host(parts.lpszHostName, parts.dwHostNameLength);
    std::wstring path = parts.dwUrlPathLength
        ? std::wstring(parts.lpszUrlPath, parts.dwUrlPathLength) : L"/";
    if (!path.empty() && path.back() == L'/') {
        path.pop_back();
    }
    path += L"/health";
    HINTERNET session = WinHttpOpen(
        L"MatickStudioLM/0.1", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0
    );
    if (!session) {
        return false;
    }
    WinHttpSetTimeouts(session, 2500, 2500, 2500, 2500);
    HINTERNET connection = WinHttpConnect(session, host.c_str(), parts.nPort, 0);
    HINTERNET request = nullptr;
    bool healthy = false;
    if (connection) {
        request = WinHttpOpenRequest(
            connection, L"GET", path.c_str(), nullptr,
            WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES,
            parts.nScheme == INTERNET_SCHEME_HTTPS ? WINHTTP_FLAG_SECURE : 0
        );
        if (request && WinHttpSendRequest(
                request, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                WINHTTP_NO_REQUEST_DATA, 0, 0, 0
            ) && WinHttpReceiveResponse(request, nullptr)) {
            DWORD status = 0;
            DWORD bytes = sizeof(status);
            if (WinHttpQueryHeaders(
                    request, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                    WINHTTP_HEADER_NAME_BY_INDEX, &status, &bytes, WINHTTP_NO_HEADER_INDEX)) {
                healthy = status == 200;
            }
        }
    }
    if (request) WinHttpCloseHandle(request);
    if (connection) WinHttpCloseHandle(connection);
    WinHttpCloseHandle(session);
    return healthy;
}

HWND CreateLabel(
    HWND parent, HINSTANCE instance, int id, const wchar_t* text,
    int x, int y, int width, int height, int pointSize = 17
) {
    HWND label = CreateWindowExW(
        0, L"STATIC", text, WS_CHILD | WS_VISIBLE | SS_LEFT,
        x, y, width, height, parent, reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)),
        instance, nullptr
    );
    HFONT font = CreateFontW(
        -pointSize, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Segoe UI"
    );
    SendMessageW(label, WM_SETFONT, reinterpret_cast<WPARAM>(font), TRUE);
    return label;
}

LRESULT CALLBACK MainWndProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    Renderer* renderer = reinterpret_cast<Renderer*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    switch (message) {
        case WM_NCCREATE: {
            auto* info = reinterpret_cast<CREATESTRUCTW*>(lParam);
            SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(info->lpCreateParams));
            return TRUE;
        }
        case WM_CTLCOLORSTATIC: {
            HDC dc = reinterpret_cast<HDC>(wParam);
            HWND label = reinterpret_cast<HWND>(lParam);
            const int id = GetDlgCtrlID(label);
            if (id < 100) {
                SetBkColor(dc, RGB(14, 22, 37));
                SetTextColor(dc, RGB(194, 229, 237));
                return reinterpret_cast<INT_PTR>(gSideBrush);
            }
            SetBkColor(dc, RGB(20, 31, 51));
            SetTextColor(dc, id == 101 ? RGB(60, 224, 229) : RGB(210, 228, 239));
            return reinterpret_cast<INT_PTR>(gCardBrush);
        }
        case WM_TIMER:
            if (renderer) {
                try {
                    renderer->Render();
                } catch (...) {
                    KillTimer(window, 1);
                    MessageBoxW(window, L"Error de renderizado DirectX 12. Revisa el driver de tu GPU.",
                                L"Matick Studio LM", MB_ICONERROR);
                    DestroyWindow(window);
                }
            }
            return 0;
        case kHealthMessage:
            if (gStatus) {
                SetWindowTextW(gStatus, wParam
                    ? L"API cloud: EN LINEA /health"
                    : L"API cloud: DESCONECTADA");
            }
            return 0;
        case WM_DESTROY:
            KillTimer(window, 1);
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProcW(window, message, wParam, lParam);
    }
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int show) {
    Renderer renderer;
    gSideBrush = CreateSolidBrush(RGB(14, 22, 37));
    gCardBrush = CreateSolidBrush(RGB(20, 31, 51));

    WNDCLASSEXW cls = {};
    cls.cbSize = sizeof(cls);
    cls.lpfnWndProc = MainWndProc;
    cls.hInstance = instance;
    cls.lpszClassName = L"MatickStudioLMDirectX12";
    cls.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    if (!RegisterClassExW(&cls)) {
        MessageBoxW(nullptr, L"No se pudo registrar la ventana.", L"Matick Studio LM", MB_ICONERROR);
        DeleteObject(gSideBrush);
        DeleteObject(gCardBrush);
        return 1;
    }

    RECT bounds = {0, 0, static_cast<LONG>(kWidth), static_cast<LONG>(kHeight)};
    constexpr DWORD style = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX;
    AdjustWindowRect(&bounds, style, FALSE);
    HWND window = CreateWindowExW(
        0, cls.lpszClassName, L"Matick Studio LM | DirectX 12 + Cloud",
        style, CW_USEDEFAULT, CW_USEDEFAULT,
        bounds.right - bounds.left, bounds.bottom - bounds.top,
        nullptr, nullptr, instance, &renderer
    );
    if (!window) {
        DeleteObject(gSideBrush);
        DeleteObject(gCardBrush);
        return 1;
    }
    try {
        renderer.Init(window);
    } catch (...) {
        MessageBoxW(window,
            L"DirectX 12 no se pudo iniciar. Actualiza el controlador de video y Windows.",
            L"Matick Studio LM", MB_ICONERROR
        );
        DestroyWindow(window);
        DeleteObject(gSideBrush);
        DeleteObject(gCardBrush);
        return 1;
    }

    CreateLabel(window, instance, 1, L"MATICK", 30, 28, 220, 40, 29);
    CreateLabel(window, instance, 2, L"STUDIO LM", 30, 71, 220, 32, 21);
    CreateLabel(window, instance, 3, L"LOCAL  /  MORLET", 30, 149, 225, 30);
    CreateLabel(window, instance, 4, L"DirectX 12  [activo]", 30, 206, 220, 30);
    CreateLabel(window, instance, 5, L"GPU / WINDOWS 11", 30, 249, 225, 30);
    CreateLabel(window, instance, 6, L"Cloud / API", 30, 292, 220, 30);
    CreateLabel(window, instance, 100, L"MATICK STUDIO LM  /  CLOUD", 321, 144, 700, 35, 26);
    gStatus = CreateLabel(window, instance, 101, L"API cloud: verificando...", 321, 204, 650, 34, 21);
    CreateLabel(window, instance, 102, L"Interfaz: Windows nativo + Direct3D 12", 321, 272, 680, 30);
    CreateLabel(window, instance, 103, L"Mensajería y autenticación: disponibles en cloud API", 321, 322, 750, 30);
    CreateLabel(window, instance, 104, L"ChatGPT / Codex / Reloj / Alexa: conectores pendientes", 321, 372, 770, 30);
    CreateLabel(window, instance, 105, L"Modelo IA cloud: pendiente de implementar", 321, 422, 730, 30);
    CreateLabel(window, instance, 106, L"Proyecto independiente de LM Studio", 321, 577, 690, 31, 20);
    CreateLabel(window, instance, 107, L"Estado inicial: MVP - Sin servicios de terceros conectados", 321, 627, 760, 28, 17);

    ShowWindow(window, show);
    UpdateWindow(window);
    SetTimer(window, 1, 33, nullptr);

    std::atomic<bool> running{true};
    std::thread monitor([&running, window]() {
        const std::wstring address = CloudURL();
        while (running.load()) {
            const bool healthy = IsCloudHealthy(address);
            PostMessageW(window, kHealthMessage, healthy ? 1 : 0, 0);
            for (int i = 0; i < 50 && running.load(); ++i) {
                Sleep(100);
            }
        }
    });

    MSG message = {};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    running.store(false);
    monitor.join();
    renderer.Finish();
    DeleteObject(gSideBrush);
    DeleteObject(gCardBrush);
    return static_cast<int>(message.wParam);
}
