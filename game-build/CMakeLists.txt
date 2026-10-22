# SPDX-License-Identifier: GPL-3.0-or-later
# mpr.exe: the runtime (../runtime) + the four lifted game libraries (built by ../recomp/scripts/build_mpr.cmd into ../work/build/mpr).
#   pwsh scripts\build.ps1            configure + build into game-build\build\release
# Nothing derived from the game lives here: the libraries are imported from the work folder, the NSOs are read at run time.
cmake_minimum_required(VERSION 3.25)
project(mpr_game C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(MPR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
set(MPR_LIB_DIR "${MPR_ROOT}/work/build/mpr" CACHE PATH "folder with mpr_main.lib mpr_sdk.lib mpr_subsdk0.lib mpr_rtld.lib (built by recomp scripts build_mpr.cmd)")
set(MPR_EXEFS_DEFAULT "${MPR_ROOT}/game/exefs" CACHE PATH "default ExeFS folder baked into mpr.exe (--exefs / MPR_EXEFS override it)")

# MPR_RUNTIME_DIR: which runtime checkout compiles in (default the main one; a worktree such as runtime-wt/boot2 for branch work)
set(MPR_RUNTIME_DIR "${MPR_ROOT}/runtime" CACHE PATH "runtime source tree compiled into mpr.exe")
set(NXRT_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(NXRT_RECOMP_INCLUDE "${MPR_ROOT}/recomp/include" CACHE PATH "")
add_subdirectory("${MPR_RUNTIME_DIR}" runtime)

foreach(m main sdk subsdk0 rtld)
    add_library(mpr_${m} STATIC IMPORTED GLOBAL)
    set_target_properties(mpr_${m} PROPERTIES IMPORTED_LOCATION "${MPR_LIB_DIR}/mpr_${m}.lib")
endforeach()

add_executable(mpr src/mpr_main.cpp)
target_compile_definitions(mpr PRIVATE MPR_EXEFS_DEFAULT="${MPR_EXEFS_DEFAULT}")
target_link_libraries(mpr PRIVATE mpr_main mpr_sdk mpr_subsdk0 mpr_rtld nxrt_gfx nxrt)
# Same link options as the runtime's test executables: a linker map next to the exe (host frames get names), a big main stack (lifted
# code nests deeply), low host allocations so the guest ranges at 0x71_0000_0000 and up stay free.
target_link_options(mpr PRIVATE /MAP /STACK:134217728 /HIGHENTROPYVA:NO /DEBUG)

# The ASTC decoder DLLs astc2bc7 loads at run time (NVN textures in ASTC are transcoded to BC7 on first use): next to mpr.exe.
file(GLOB MPR_A2B_DLLS "${MPR_ROOT}/tools/textures/build/release/astcdec-*-shared.dll")
foreach(dll ${MPR_A2B_DLLS})
    add_custom_command(TARGET mpr POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy_if_different "${dll}" "$<TARGET_FILE_DIR:mpr>")
endforeach()
