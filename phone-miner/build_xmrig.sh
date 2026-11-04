#!/bin/bash
# ЭКСПЕРИМЕНТАЛЬНО: собирает движок XMRig для Android (arm64) в Codespaces.
# Запускать ПОСЛЕ первой сборки APK (нужен скачанный buildozer'ом NDK 25b).
set -e
NDK=$HOME/.buildozer/android/platform/android-ndk-r25b
TC=$NDK/build/cmake/android.toolchain.cmake
[ -f "$TC" ] || { echo "NDK не найден. Сначала один раз запусти buildozer."; exit 1; }
HERE=$(pwd)
mkdir -p ~/xm && cd ~/xm
[ -d libuv ] || git clone --depth 1 https://github.com/libuv/libuv.git
[ -d xmrig ] || git clone --depth 1 https://github.com/xmrig/xmrig.git
COMMON="-DCMAKE_TOOLCHAIN_FILE=$TC -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-24 -DCMAKE_BUILD_TYPE=Release"

cd libuv
cmake -B build $COMMON -DLIBUV_BUILD_SHARED=OFF -DLIBUV_BUILD_TESTS=OFF
cmake --build build -j4
cd ../xmrig
cmake -B build $COMMON \
  -DUV_INCLUDE_DIR=$HOME/xm/libuv/include -DUV_LIBRARY=$HOME/xm/libuv/build/libuv.a \
  -DWITH_HWLOC=OFF -DWITH_TLS=OFF -DWITH_OPENCL=OFF -DWITH_CUDA=OFF -DWITH_ENV_VARS=OFF
cmake --build build -j4

mkdir -p "$HERE/libs/arm64-v8a"
cp build/xmrig "$HERE/libs/arm64-v8a/libxmrig.so"
echo "ГОТОВО: libs/arm64-v8a/libxmrig.so"
