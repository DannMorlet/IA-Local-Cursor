cmake_minimum_required(VERSION 3.21)

project(MatickStudioLM VERSION 1.2.0 LANGUAGES CXX RC)

if(NOT WIN32)
    message(FATAL_ERROR "Matick Studio LM DirectX 12 requiere Windows y Windows SDK.")
endif()

add_executable(MatickStudioLM WIN32 src/main.cpp src/dashboard.cpp src/chat_transport.cpp src/render_safety.cpp src/backend_bootstrap.cpp)
target_compile_features(MatickStudioLM PRIVATE cxx_std_17)
target_compile_definitions(MatickStudioLM PRIVATE
    UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX
)
target_link_libraries(MatickStudioLM PRIVATE d3d12 dxgi dxguid winhttp bcrypt)
if(MSVC)
    set_property(TARGET MatickStudioLM PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    target_compile_options(MatickStudioLM PRIVATE /W4 /EHsc /utf-8)
endif()

if(NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "Se requiere Windows x64.")
endif()
target_sources(MatickStudioLM PRIVATE MatickStudioLM.rc)
