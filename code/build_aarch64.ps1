# Script para construir el ejecutable Linux AArch64 usando Docker y emulación QEMU

Write-Host "Iniciando construcción para AArch64 (ARM64)..."
Write-Host "Nota: Esto requiere Docker Desktop con soporte para emulación (QEMU)."

# 0. Instalar/Habilitar emuladores QEMU (Soluciona 'exec format error')
Write-Host "Paso 0: Configurando emuladores QEMU (binfmt)..."
docker run --privileged --rm tonistiigi/binfmt --install all
if ($LASTEXITCODE -ne 0) {
    Write-Host "Advertencia: No se pudieron instalar los emuladores. Si ya están configurados, ignora este mensaje." -ForegroundColor Yellow
} else {
    Write-Host "Emuladores QEMU configurados correctamente." -ForegroundColor Green
}

# 1. Construir la imagen forzando la plataforma linux/arm64
# Esto hará que Docker descargue la imagen base de arm64 y ejecute todo como si fuera una máquina arm64.
Write-Host "Paso 1: Construyendo imagen Docker (esto puede tardar debido a la emulación)..."
docker build --platform linux/arm64 -f Dockerfile.aarch64 -t hello-pysdl-aarch64 .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Falló la construcción de la imagen Docker." -ForegroundColor Red
    exit 1
}

# 2. Ejecutar el contenedor para extraer el binario
Write-Host "Paso 2: Extrayendo ejecutable..."
docker run --rm --platform linux/arm64 -v .\dist:/output hello-pysdl-aarch64

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Falló la extracción del ejecutable." -ForegroundColor Red
    exit 1
}

Write-Host "Éxito! El ejecutable 'hello_aarch64' debería estar en tu directorio actual." -ForegroundColor Green
Write-Host "Verifica el tipo de archivo con: wsl file hello_aarch64 (si tienes WSL) o probándolo en el dispositivo destino."
