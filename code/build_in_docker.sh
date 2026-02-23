#!/bin/bash
set -e

# Find SDL2 library
SDL_LIB=$(find /usr/lib -name "libSDL2-2.0.so.0" | head -n 1)

if [ -z "$SDL_LIB" ]; then
    echo "Error: libSDL2-2.0.so.0 not found!"
    exit 1
fi

echo "Found SDL2 at $SDL_LIB"

# Build with PyInstaller
# We add the binary to the root (.) so PYSDL2_DLL_PATH=. (or sys._MEIPASS) works
# --add-data "assets:assets" includes the assets folder (use : for Linux separator)
python3.11 -m PyInstaller --clean --onefile  --name hello_aarch64 --add-binary "$SDL_LIB:." --add-data "assets:assets" main.py

# Move the result to /output if mounted, or leave in dist
if [ -d "/output" ]; then
    cp dist/hello_aarch64 /output/
    echo "Copied hello_aarch64 to /output"
fi
