import os
import sys
# Importar perfil primero para saber si activar el fix
try:
    from src.profile import PROFILES, ACTIVE_PROFILE
except ImportError:
    from profile import PROFILES, ACTIVE_PROFILE
# Obtener configuración del perfil activo
profile_config = PROFILES[ACTIVE_PROFILE]

# Configuración pre-importación de SDL2 para PyInstaller
# Solo si el perfil lo requiere (FIX_SDL2_PATH) Y estamos en modo empaquetado
if hasattr(sys, '_MEIPASS') and profile_config.get("FIX_SDL2_PATH", False):
    # Le decimos a PySDL2 que busque las librerías en el directorio temporal de extracción
    # Apuntamos directamente al archivo de librería
    os.environ["PYSDL2_DLL_PATH"] = os.path.join(sys._MEIPASS, "libSDL2-2.0.so.0")

import sdl2
import sdl2.sdlmixer as mix
import sdl2.sdlttf as ttf
import ctypes

# Configuración de directorios
if hasattr(sys, '_MEIPASS'):
    # Ejecutando desde PyInstaller bundle
    PROJECT_ROOT = sys._MEIPASS
    ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

else:
    # Ejecutando desde código fuente
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

# Configuración de la pantalla
# Resolución Lógica (Diseño interno, las coordenadas se basan en esto)
WIDTH = 700
HEIGHT = 680

# (profile ya importado arriba)

# Aplicar configuración del perfil
WINDOW_WIDTH = profile_config["WINDOW_WIDTH"]
WINDOW_HEIGHT = profile_config["WINDOW_HEIGHT"]

CAPTION = b"Reproductor MP3 SDL2"

WINDOW = None
RENDERER = None

# --- CONFIGURACION DE BOTONES ---
BUTTON_B = profile_config["BUTTON_B"]
BUTTON_A = profile_config["BUTTON_A"]
BUTTON_X = profile_config["BUTTON_X"]
BUTTON_Y = profile_config["BUTTON_Y"]
BUTTON_START = profile_config["BUTTON_START"]
BUTTON_DUP = profile_config.get("BUTTON_DUP", 14) # Default 14 if not present
BUTTON_DDOWN = profile_config.get("BUTTON_DDOWN", 15) # Default 15 if not present

# ---------------------------------------------------------------




def init_sdl2():
    global WINDOW, RENDERER, FONT_LARGE, FONT_MEDIUM, FONT_SMALL
    
    # Inicializar SDL2
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO | sdl2.SDL_INIT_JOYSTICK) != 0:
        print(f"Error inicializando SDL2: {sdl2.SDL_GetError()}")
        return None

    # Inicializar TTF
    if ttf.TTF_Init() != 0:
        print(f"Error inicializando SDL_ttf: {ttf.TTF_GetError()}")
        return None

    # Inicializar Mixer
    if mix.Mix_OpenAudio(44100, mix.MIX_DEFAULT_FORMAT, 2, 2048) != 0:
        print(f"Error inicializando SDL_mixer: {mix.Mix_GetError()}")
        return None

    # Crear ventana
    WINDOW = sdl2.SDL_CreateWindow(CAPTION,
                                  sdl2.SDL_WINDOWPOS_CENTERED,
                                  sdl2.SDL_WINDOWPOS_CENTERED,
                                  WINDOW_WIDTH, WINDOW_HEIGHT,
                                  sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_RESIZABLE)
    
    if not WINDOW:
        print(f"Error creando ventana: {sdl2.SDL_GetError()}")
        return None

    # Crear renderizador
    RENDERER = sdl2.SDL_CreateRenderer(WINDOW, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC)
    
    if not RENDERER:
        # Fallback a software renderer si falla acelerado
        print("Fallback a software renderer")
        RENDERER = sdl2.SDL_CreateRenderer(WINDOW, -1, sdl2.SDL_RENDERER_SOFTWARE)

    # Establecer resolución lógica (Virtual Display)
    # Esto escala automáticamente el contenido para ajustarse a la ventana
    # Si queremos que se estire sin importar el aspect ratio, NO usamos RenderSetLogicalSize directamente
    # porque impone letterboxing.
    
    # Intento fallido con Hints en versiones viejas de SDL2.
    # Estrategia definitiva: ESCALADO MANUAL.
    
    # 1. No llamamos a SDL_RenderSetLogicalSize.
    # 2. Calculamos la escala inicial basada en el tamaño de ventana actual vs el diseño (700x680).
    
    w_w = ctypes.c_int()
    w_h = ctypes.c_int()
    sdl2.SDL_GetWindowSize(WINDOW, ctypes.byref(w_w), ctypes.byref(w_h))
    
    scale_x = w_w.value / WIDTH
    scale_y = w_h.value / HEIGHT
    
    sdl2.SDL_RenderSetScale(RENDERER, ctypes.c_float(scale_x), ctypes.c_float(scale_y))
    
    # Nota: Si el usuario redimensiona la ventana, esto debe actualizarse en el bucle de eventos (main.py).
    
    # Cargar fuentes
    FONT_LARGE = load_font(24)
    FONT_MEDIUM = load_font(27)
    FONT_SMALL = load_font(18)
    
    return WINDOW, RENDERER

# Colores (SDL_Color)
WHITE = sdl2.SDL_Color(255, 255, 255, 255)
BLACK = sdl2.SDL_Color(30, 30, 30, 255)
GRAY = sdl2.SDL_Color(255, 255, 255, 255)
LIGHT_GRAY = sdl2.SDL_Color(255, 255, 255, 255)
ACCENT = sdl2.SDL_Color(255, 255, 255, 255)
TEXT_COLOR = sdl2.SDL_Color(255, 255, 255, 255)

# Fuentes
def load_font(size):
    font_path = os.path.join(ASSETS_DIR, 'PublicPixel.ttf')
    if os.path.exists(font_path):
        return ttf.TTF_OpenFont(font_path.encode('utf-8'), size)
    # Fallback si no existe la fuente (podríamos intentar cargar una del sistema o error)
    print(f"Warning: Font not found at {font_path}")
    return None

FONT_LARGE = None
FONT_MEDIUM = None
FONT_SMALL = None

# Botones
BUTTON_SIZE = (100, 100)
