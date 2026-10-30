// Matick Studio LM - Interfaz nativa Direct3D 12 para Windows 11.
// Este MVP comprueba GET /health sin secretos. La mensajería privada es trabajo futuro.
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <winhttp.h>
#include "dashboard.h"

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
constexpr UINT kWidth = 1500;
constexpr UINT kHeight = 850;
constexpr UINT kHealthMessage = WM_APP + 1;

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
        // La composición de paneles usa Direct3D 12; controles y mascota son Win32.
        const FLOAT background[4] = {0.043f, 0.073f, 0.126f, 1.0f};
        const FLOAT sidebar[4] = {0.037f, 0.070f, 0.124f, 1.0f};
        const FLOAT topbar[4] = {0.043f, 0.067f, 0.113f, 1.0f};
        const FLOAT workspace[4] = {0.946f, 0.963f, 0.984f, 1.0f};
        const FLOAT white[4] = {1.0f, 1.0f, 1.0f, 1.0f};
        const FLOAT cards[4] = {0.974f, 0.983f, 0.995f, 1.0f};
        const FLOAT accent[4] = {0.0f, 0.69f, 0.95f, 1.0f};
        const FLOAT rightCard[4] = {0.070f, 0.109f, 0.181f, 1.0f};

        const auto fill = [&](const FLOAT* color, LONG l, LONG t, LONG r, LONG bot) {
            const RECT region{l, t, r, bot};
            commands->ClearRenderTargetView(rtv, color, 1, &region);
        };
        commands->ClearRenderTargetView(rtv, background, 0, nullptr);
        fill(workspace, 290, 66, 1180, static_cast<LONG>(kHeight));
        fill(sidebar, 0, 66, 290, static_cast<LONG>(kHeight));
        fill(topbar, 0, 0, static_cast<LONG>(kWidth), 66);
        fill(white, 308, 91, 1164, 417);
        fill(accent, 308, 91, 1164, 95);
        fill(white, 308, 457, 862, 675);
        fill(white, 880, 457, 1164, 803);
        fill(white, 308, 689, 862, 803);
        for (const LONG y : {510L, 584L}) {
            for (const LONG x : {321L, 498L, 675L}) {
                fill(cards, x, y, x + 166, y + 63);
            }
        }
        fill(rightCard, 1196, 477, 1484, 798);
        fill(accent, 1209, 476, 1467, 479);

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

LRESULT CALLBACK MainWndProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    Renderer* renderer = reinterpret_cast<Renderer*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    switch (message) {
        case WM_NCCREATE: {
            auto* info = reinterpret_cast<CREATESTRUCTW*>(lParam);
            SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(info->lpCreateParams));
            return TRUE;
        }
        case WM_CTLCOLORSTATIC:
            return DashboardControlColor(reinterpret_cast<HDC>(wParam),
                                         reinterpret_cast<HWND>(lParam));
        case WM_COMMAND:
            DashboardCommand(window, LOWORD(wParam));
            return 0;
        case WM_TIMER:
            DashboardTick();
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
            DashboardSetCloudStatus(wParam != 0);
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

    WNDCLASSEXW cls = {};
    cls.cbSize = sizeof(cls);
    cls.lpfnWndProc = MainWndProc;
    cls.hInstance = instance;
    cls.lpszClassName = L"MatickStudioLMDirectX12";
    cls.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    if (!RegisterClassExW(&cls)) {
        MessageBoxW(nullptr, L"No se pudo registrar la ventana.", L"Matick Studio LM", MB_ICONERROR);
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
        return 1;
    }

    DashboardInstall(window, instance);

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
    DashboardShutdown();
    return static_cast<int>(message.wParam);
}
