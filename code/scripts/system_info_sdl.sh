#!/bin/sh

# Directorio donde está el script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Archivo de salida en el mismo directorio
OUT="$SCRIPT_DIR/system_info.txt"

echo "==============================" > "$OUT"
echo " SYSTEM INFO - EmuELEC 4.7 " >> "$OUT"
echo "==============================" >> "$OUT"
echo "" >> "$OUT"

# Fecha
echo "Fecha:" >> "$OUT"
date >> "$OUT"
echo "" >> "$OUT"

# Kernel / arquitectura
echo "Kernel y arquitectura:" >> "$OUT"
uname -a >> "$OUT"
echo "" >> "$OUT"

# GCC
echo "GCC version:" >> "$OUT"
if command -v gcc >/dev/null 2>&1; then
    gcc --version | head -n 1 >> "$OUT"
else
    echo "gcc no instalado" >> "$OUT"
fi
echo "" >> "$OUT"

# Libc
echo "Libc info:" >> "$OUT"
if command -v ldd >/dev/null 2>&1; then
    ldd --version 2>&1 | head -n 2 >> "$OUT"
else
    echo "ldd no disponible" >> "$OUT"
fi
echo "" >> "$OUT"

echo "====================================" >> "$OUT"
echo " DETECCION DE SDL" >> "$OUT"
echo "====================================" >> "$OUT"

# ---------- SDL 1.2 ----------
echo "" >> "$OUT"
echo "SDL 1.2:" >> "$OUT"
SDL1_FOUND=0

for dir in /usr/lib /lib; do
    if ls "$dir"/libSDL-1.2.so* >/dev/null 2>&1; then
        SDL1_FOUND=1
        echo "Encontrado en $dir:" >> "$OUT"
        ls "$dir"/libSDL-1.2.so* >> "$OUT"
    fi
done

if [ "$SDL1_FOUND" -eq 0 ]; then
    echo "No encontrado" >> "$OUT"
fi

# ---------- SDL2 ----------
echo "" >> "$OUT"
echo "SDL2:" >> "$OUT"
SDL2_FOUND=0

for dir in /usr/lib /lib; do
    if ls "$dir"/libSDL2.so* >/dev/null 2>&1; then
        SDL2_FOUND=1
        echo "Encontrado en $dir:" >> "$OUT"
        ls "$dir"/libSDL2.so* >> "$OUT"
    fi
done

if [ "$SDL2_FOUND" -eq 0 ]; then
    echo "No encontrado" >> "$OUT"
fi

# ---------- Resumen ----------
echo "" >> "$OUT"
echo "====================================" >> "$OUT"
echo " RESUMEN SDL" >> "$OUT"
echo "====================================" >> "$OUT"

if [ "$SDL1_FOUND" -eq 1 ] && [ "$SDL2_FOUND" -eq 1 ]; then
    echo "SDL 1.2 y SDL2 disponibles" >> "$OUT"
elif [ "$SDL2_FOUND" -eq 1 ]; then
    echo "Solo SDL2 disponible" >> "$OUT"
elif [ "$SDL1_FOUND" -eq 1 ]; then
    echo "Solo SDL 1.2 disponible" >> "$OUT"
else
    echo "No se encontró SDL" >> "$OUT"
fi

#--revisa si existe instalada alguna version de python
echo "" >> "$OUT"
echo "Python:" >> "$OUT"
if command -v python >/dev/null 2>&1; then
    python --version >> "$OUT"
else
    echo "python no instalado" >> "$OUT"
fi


echo "" >> "$OUT"
echo "Reporte generado en: $OUT" >> "$OUT"
