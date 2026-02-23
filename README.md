# Parasyte Music Player

A lightweight SDL2-based music player designed for handheld retro gaming consoles like the **R36T Max**, **R36T**, and **R36S Ultra**. Built with Python and PySDL2, it runs natively on Linux ARM64/ARMv7 devices and also on Windows for development. COPY YOUR MUSIC TO `/roms/music`.

## Features

- MP3 playback with album cover art display
- File browser / playlist navigation
- Joystick and D-pad controls (mapped per device profile)
- Volume control (ALSA on Linux, pycaw on Windows)
- Marquee scrolling for long track names
- Screensaver (black screen after 30s of inactivity, hardware screen-off on ARM Linux after 35s)
- Repeat modes (off / repeat all / repeat one)
- Built-in FTP and Telnet servers for remote file management
- Multi-device profile support with per-device button mapping and resolution

## Supported Devices

| Profile | Resolution | Notes |
|---------|-----------|-------|
| r36t max | 700×680 | Default profile |
| r36t | 640×480 | |
| r36s ultra | 700×680 | |

To change the active profile, edit `src/profile.py` and set `ACTIVE_PROFILE`.

## Controls

| Button | Player View | Playlist View |
|--------|------------|---------------|
| B | Play / Pause | Select item |
| A | Toggle Playlist | Toggle Playlist |
| Y | Previous track | Play directory |
| X | Next track | — |
| D-Up | Volume up | Navigate up |
| D-Down | Volume down | Navigate down |
| D-Right | Next track | Navigate down |
| D-Left | Previous track | — |
| Start | Toggle repeat mode | Toggle repeat mode |
| Select | Quit | Quit |

## Project Structure

```
src/
  main.py           # Main loop, rendering, event handling
  config.py         # SDL2 initialization, fonts, colors, dimensions
  profile.py        # Device profiles (resolution, button mapping)
  player.py         # Music player logic, file browser
  input_handler.py  # Keyboard and joystick input processing
  playlist.py       # Playlist screen rendering
  volume_control.py # System volume control (ALSA / Windows)
  server.py         # FTP and Telnet servers
assets/             # UI images (background, buttons, default cover)
music/              # Music files (MP3)
scripts/
  runme.sh          # Launch script for the device
```

## Requirements

- Python 3.11+
- SDL2, SDL2_image, SDL2_mixer, SDL2_ttf
- Docker Desktop (for cross-compiling to ARM64)

## Running from Source (Windows)

1. Create a virtual environment and install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
```

2. Run the application:

```powershell
python src/main.py
```

## Building the ARM64 Binary

The project uses Docker with QEMU emulation to cross-compile a standalone Linux ARM64 binary. This works from Windows with Docker Desktop installed.

### Prerequisites

- **Docker Desktop** installed and running
- Docker must have QEMU/binfmt support enabled (the build script handles this automatically)

### Build Steps

1. Open a PowerShell terminal in the project root.

2. Run the build script:

```powershell
.\build_aarch64.ps1
```

The script will:
1. **Configure QEMU emulators** via `tonistiigi/binfmt` for ARM64 emulation
2. **Build a Docker image** (`Dockerfile.aarch64`) using the `linux/arm64` platform — this installs all SDL2 dependencies and Python packages inside an emulated ARM64 Ubuntu container
3. **Run the container** to compile the binary with PyInstaller and extract it

3. The resulting binary `hello_aarch64` will be placed in the `dist/` directory.

4. Copy `hello_aarch64` and the `assets/` folder to your device, along with `scripts/runme.sh` as the launcher.

### Verifying the Binary

If you have WSL installed, you can verify the architecture:

```powershell
wsl file dist/hello_aarch64
```

Expected output should show `ELF 64-bit LSB executable, ARM aarch64`.

## Deploying to the Device

1. Copy the following launcher folder to your device (SD card):
   - `MusicPlayer.sh`
   - `gamelist.xml` 
   - `bin` (folder)
   - `bin/icon.png`
   - `bin/hello_aarch64`
   - COPY YOUR MUSIC TO `/roms/music`

2. Make sure `runme.sh` and `hello_aarch64` are executable:

```bash
chmod +x runme.sh hello_aarch64
```

3. Launch with `./runme.sh`.

## License

This project is provided as-is for personal use on retro handheld devices.
