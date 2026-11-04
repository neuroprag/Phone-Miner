[app]
title = Miner
package.name = phoneminer
package.domain = org.phoneminer
source.dir = .
source.include_exts = py,png,jpg,kv,json
version = 0.1
icon.filename = %(source.dir)s/icon.png
requirements = python3,kivy==2.3.0,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, WAKE_LOCK
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.branch = v2024.01.21
android.ndk = 25b

# Когда положишь движок в libs/arm64-v8a/libxmrig.so, раскомментируй строку:
android.add_libs_arm64_v8a = libs/arm64-v8a/libxmrig.so

[buildozer]
log_level = 2
warn_on_root = 0
