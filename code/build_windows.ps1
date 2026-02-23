# Check Python version
$version = python --version
Write-Host "Using $version"

#################correr la primera vez################
Write-Host "Creating virtual environment..."
python -m venv venv

#Write-Host "Installing requirements..."
.\venv\Scripts\python -m pip install -r requirements.txt
#################correr la primera vez################

# Build with PyInstaller using venv python
Write-Host "Building executable..."
# --collect-all pysdl2_dll ensures DLLs are bundled
# --add-data "assets;assets" incluye la carpeta de assets
.\venv\Scripts\python -m PyInstaller --noconfirm --onefile --windowed --name "hello_world_windows" --collect-all pysdl2_dll --add-data "assets;assets" src/main.py

Write-Host "Build complete. Executable is in dist/"
