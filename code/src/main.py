import sys
import os
import platform
import ctypes
import config


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
    print(f"Activando fix de path para SDL2: {sys._MEIPASS}")
    os.environ["PYSDL2_DLL_PATH"] = os.path.join(sys._MEIPASS, "/mnt/SDCARD/.tmp_update/lib/parasyte/")



import sdl2
import sdl2.ext
import sdl2.sdlimage as img
import sdl2.sdlmixer as mix
import sdl2.sdlttf as ttf

from player import MusicPlayer, draw_button
from input_handler import InputHandler
from playlist import PlaylistScreen
from server import start_servers

def load_texture(renderer, path):
    if not os.path.exists(path):
        print(f"Error: Archivo no encontrado {path}")
        return None
        
    # Cargar superficie
    surface = img.IMG_Load(path.encode('utf-8'))
    if not surface:
        print(f"Error cargando imagen {path}: {img.IMG_GetError()}")
        return None
        
    # Crear textura
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    sdl2.SDL_FreeSurface(surface)
    
    if not texture:
        print(f"Error creando textura para {path}: {sdl2.SDL_GetError()}")
        return None
        
    return texture

def render_text(renderer, font, text, color, x, y, centered=False):
    if not font:
        return
        
    if not text:
        return

    surface = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
    if not surface:
        return
        
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    
    # Obtener dimensiones
    w = surface.contents.w
    h = surface.contents.h
    
    sdl2.SDL_FreeSurface(surface)
    
    dest_rect = sdl2.SDL_Rect(x, y, w, h)
    
    if centered:
        dest_rect.x = x - (w // 2)
        
    sdl2.SDL_RenderCopy(renderer, texture, None, ctypes.byref(dest_rect))
    sdl2.SDL_DestroyTexture(texture)

def _screen_power(on):
    """Enciende o apaga la pantalla física en Linux (consola r36t)."""
    import subprocess
    try:
        # Intentar via backlight
        backlight_paths = [
            "/sys/class/backlight/backlight/brightness",
            "/sys/class/backlight/backlight/bl_power",
        ]
        
        if on:
            # Intentar restaurar brillo
            for path in ["/sys/class/backlight/backlight/brightness"]:
                if os.path.exists(path):
                    # Leer max_brightness
                    max_path = os.path.dirname(path) + "/max_brightness"
                    max_val = "128"
                    if os.path.exists(max_path):
                        with open(max_path, 'r') as f:
                            max_val = f.read().strip()
                    subprocess.run(["sh", "-c", f"echo {max_val} > {path}"], timeout=2)
                    print(f"Pantalla encendida: brightness={max_val}")
                    return
            
            # Fallback: fb0 unblank
            if os.path.exists("/sys/class/graphics/fb0/blank"):
                subprocess.run(["sh", "-c", "echo 0 > /sys/class/graphics/fb0/blank"], timeout=2)
                print("Pantalla encendida: fb0 unblank")
                return
        else:
            # Apagar: poner brillo a 0
            for path in ["/sys/class/backlight/backlight/brightness"]:
                if os.path.exists(path):
                    subprocess.run(["sh", "-c", f"echo 0 > {path}"], timeout=2)
                    print("Pantalla apagada: brightness=0")
                    return
            
            # Fallback: fb0 blank
            if os.path.exists("/sys/class/graphics/fb0/blank"):
                subprocess.run(["sh", "-c", "echo 1 > /sys/class/graphics/fb0/blank"], timeout=2)
                print("Pantalla apagada: fb0 blank")
                return
                
        print(f"No se encontró método para {'encender' if on else 'apagar'} la pantalla")
    except Exception as e:
        print(f"Error controlando pantalla: {e}")

def main():
    # Inicializar SDL2 via config
    window, renderer = config.init_sdl2()
    if not window or not renderer:
        print("Fallo crítico inicializando SDL2. Saliendo.")
        return

    # Iniciar servidores (FTP y Telnet)
    ftp_server, telnet_server = start_servers()

    player = MusicPlayer()
    input_handler = InputHandler(player)
    playlist_screen = PlaylistScreen(renderer, player)
    
    current_view = "player" # player | playlist
    
    # Cargar música automáticamente
    player.load_music()
    
    # Cargar assets (Texturas)
    background_tex = None
    album_cover_tex = None
    btn_prev_tex = None
    btn_play_tex = None
    btn_next_tex = None
    
    bg_path = os.path.join(config.ASSETS_DIR, 'bk1.jpg')
    cover_path = os.path.join(config.ASSETS_DIR, 'sl1.jpg')
    
    path_b = os.path.join(config.ASSETS_DIR, 'b.jpg')
    path_p = os.path.join(config.ASSETS_DIR, 'p.jpg')
    path_pause = os.path.join(config.ASSETS_DIR, 'pause.jpg')
    path_f = os.path.join(config.ASSETS_DIR, 'f.jpg')
    
    background_tex = load_texture(renderer, bg_path)
    album_cover_tex = load_texture(renderer, cover_path)
    btn_prev_tex = load_texture(renderer, path_b)
    btn_play_tex = load_texture(renderer, path_p)
    btn_pause_tex = load_texture(renderer, path_pause)
    btn_next_tex = load_texture(renderer, path_f)

    # Definir áreas de botones
    center_x = config.WIDTH // 2
    y_pos = 610
    spacing = 110
    
    btn_w, btn_h = config.BUTTON_SIZE
    
    rect_prev = (center_x - spacing - btn_w//2, y_pos - btn_h//2, btn_w, btn_h)
    rect_play = (center_x - btn_w//2, y_pos - btn_h//2, btn_w, btn_h)
    rect_next = (center_x + spacing - btn_w//2, y_pos - btn_h//2, btn_w, btn_h)

    running = True
    event = sdl2.SDL_Event()
    
    # Variables para marquee
    marquee_offset = 0
    marquee_direction = 1 # 1: Adelante, -1: Atrás
    marquee_wait = 0 # Contador para pausas
    last_track_name = ""
    
    # Textura de portada por defecto
    default_cover_tex = album_cover_tex
    current_cover_tex = default_cover_tex
    
    # Variables para animación de botones
    btn_highlight_time = 0
    btn_highlight_target = None # "prev" o "next"
    manual_transition = False

    # Variables para pantalla negra (screensaver)
    last_input_time = sdl2.SDL_GetTicks()
    screensaver_active = False
    screen_off = False  # True si la pantalla física está apagada (Linux ARM64)
    SCREENSAVER_TIMEOUT = 30000  # 30 segundos en milisegundos
    SCREEN_OFF_TIMEOUT = 35000   # 35 segundos - apagar pantalla en Linux ARM64
    is_linux_arm64 = (platform.system() == "Linux" and platform.machine() in ("aarch64", "arm64", "armv7l"))

    while running:
        # Procesar eventos
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            
            # Manejar redimensionamiento de ventana para mantener stretch
            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED or \
                   event.window.event == sdl2.SDL_WINDOWEVENT_SIZE_CHANGED:
                    new_w = event.window.data1
                    new_h = event.window.data2
                    
                    # Recalcular escala
                    scale_x = new_w / config.WIDTH
                    scale_y = new_h / config.HEIGHT
                    
                    sdl2.SDL_RenderSetScale(renderer, ctypes.c_float(scale_x), ctypes.c_float(scale_y))
                
            action = input_handler.handle_input(event)

            # Detectar cualquier input para el screensaver
            if event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_JOYBUTTONDOWN, sdl2.SDL_JOYHATMOTION, sdl2.SDL_MOUSEBUTTONDOWN):
                last_input_time = sdl2.SDL_GetTicks()
                if screensaver_active:
                    screensaver_active = False
                    # Encender pantalla si estaba apagada
                    if screen_off and is_linux_arm64:
                        _screen_power(True)
                        screen_off = False
                    continue  # Consumir el evento que despierta la pantalla

            if action == "QUIT":
                running = False
                break
            elif action == "TOGGLE_PLAYLIST":
                if current_view == "player":
                    current_view = "playlist"
                    input_handler.set_mode("playlist")
                    print("Cambiando a pantalla Playlist")
                else:
                    current_view = "player"
                    input_handler.set_mode("player")
                    print("Regresando a pantalla Player")
            
            # Navegación en Playlist
            elif action == "NAV_UP":
                if current_view == "playlist":
                    playlist_screen.move_up()
            elif action == "NAV_DOWN":
                if current_view == "playlist":
                    playlist_screen.move_down()
            elif action == "PLAY_DIR":
                if current_view == "playlist":
                    # Reproducir todo el directorio actual
                    files = [item['path'] for item in player.browser_items if item['type'] == 'file']
                    if files:
                        player.stop_music()
                        player.playlist = files
                        player.current_track_index = 0
                        player.play_music()
                        current_view = "player"
                        input_handler.set_mode("player")
            elif action == "SELECT_ITEM":
                if current_view == "playlist":
                    item = playlist_screen.get_selected_item()
                    if item:
                        if item['type'] == 'dir':
                            player.current_path = item['path']
                            player.update_browser_items()
                            playlist_screen.selected_index = 0
                        elif item['type'] == 'file':
                            # Reproducir archivo seleccionado pero cargando todo el contexto del directorio
                            # para permitir navegación (Next/Prev)
                            files = [i['path'] for i in player.browser_items if i['type'] == 'file']
                            
                            target_path = item['path']
                            start_index = 0
                            
                            if target_path in files:
                                start_index = files.index(target_path)
                            
                            player.stop_music()
                            player.playlist = files
                            player.current_track_index = start_index
                            player.play_music()
                            
                            current_view = "player"
                            input_handler.set_mode("player")

            elif action == "NAV_RIGHT": # Solo playlist
                if current_view == "playlist":
                    playlist_screen.move_down() # Asumimos right como down o similar
            
            # Acciones de Player (mapeadas desde input_handler que devuelve strings genéricos o ejecuta directo)
            # InputHandler ejecuta player.next_track() internamente para teclas directas, 
            # pero necesitamos saberlo aquí para la UI.
            # InputHandler devuelve None si ejecutó una acción interna que no retorna string.
            # Modificaremos input_handler para que retorne acciones explícitas para next/prev track si es posible,
            # O detectamos el cambio de estado aquí.
            
            # Hack: Detectar si se presionó la tecla/botón correspondiente revisando el evento raw
            # O mejor: InputHandler devuelve "NEXT_TRACK" / "PREV_TRACK"
            
            if action == "NEXT_TRACK":
                 btn_highlight_target = "next"
                 btn_highlight_time = 1 # ~16ms (1 frame), closest to 4ms
                 manual_transition = True
            elif action == "PREV_TRACK":
                 btn_highlight_target = "prev"
                 btn_highlight_time = 1 # ~16ms
                 manual_transition = True
            
            # Clics del mouse para botones en pantalla (solo en vista player)
            if current_view == "player" and event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                if event.button.button == sdl2.SDL_BUTTON_LEFT:
                    x, y = event.button.x, event.button.y
                    pt = sdl2.SDL_Point(x, y)
                    
                    # Chequear botones
                    r_play = sdl2.SDL_Rect(*rect_play)
                    if sdl2.SDL_PointInRect(pt, r_play):
                        player.toggle_play_pause()
                        
                    r_prev = sdl2.SDL_Rect(*rect_prev)
                    if sdl2.SDL_PointInRect(pt, r_prev):
                        player.prev_track()
                        btn_highlight_target = "prev"
                        btn_highlight_time = 1 # ~16ms
                        manual_transition = True
                        
                    r_next = sdl2.SDL_Rect(*rect_next)
                    if sdl2.SDL_PointInRect(pt, r_next):
                        player.next_track()
                        btn_highlight_target = "next"
                        btn_highlight_time = 1 # ~16ms
                        manual_transition = True

        # Renderizado
        player.update()

        # Verificar timeout de screensaver
        current_ticks = sdl2.SDL_GetTicks()
        idle_time = current_ticks - last_input_time

        if not screensaver_active and idle_time >= SCREENSAVER_TIMEOUT:
            screensaver_active = True

        # Apagar pantalla física a los 35 segundos (solo Linux ARM64)
        if screensaver_active and not screen_off and is_linux_arm64 and idle_time >= SCREEN_OFF_TIMEOUT:
            _screen_power(False)
            screen_off = True

        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(renderer)

        if screensaver_active:
            # Pantalla negra - solo renderizar negro y presentar
            sdl2.SDL_RenderPresent(renderer)
            sdl2.SDL_Delay(16)
            continue

        if current_view == "player":
            # Fondo
            if background_tex:
                sdl2.SDL_RenderCopy(renderer, background_tex, None, None)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 30, 30, 30, 255)
                sdl2.SDL_RenderClear(renderer)
                
            # Información de la canción
            track_name = player.get_current_track_name() or "No hay musica seleccionada"
            
            # Actualizar portada y marquee si cambia la canción
            if track_name != last_track_name:
                # Si no hubo acción manual reciente (manual_transition is False), asumir auto-advance (Next)
                if not manual_transition:
                    btn_highlight_target = "next"
                    btn_highlight_time = 1 # ~16ms
                
                # Resetear flag manual
                manual_transition = False

                last_track_name = track_name
                marquee_offset = 0
                marquee_direction = 1
                marquee_wait = 60 # Espera inicial
                
                # Intentar cargar portada del MP3
                cover_data = player.get_current_track_cover()
                if cover_data:
                    # Crear RWops desde memoria
                    rw = sdl2.SDL_RWFromConstMem(cover_data, len(cover_data))
                    surface = img.IMG_Load_RW(rw, 1) # 1 = auto-close RWops
                    if surface:
                        if current_cover_tex and current_cover_tex != default_cover_tex:
                            sdl2.SDL_DestroyTexture(current_cover_tex)
                        current_cover_tex = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
                        sdl2.SDL_FreeSurface(surface)
                    else:
                        current_cover_tex = default_cover_tex
                else:
                    # Volver a default si no hay cover
                    if current_cover_tex and current_cover_tex != default_cover_tex:
                         sdl2.SDL_DestroyTexture(current_cover_tex)
                    current_cover_tex = default_cover_tex

            # Portada del álbum
            if current_cover_tex:
                cover_rect = sdl2.SDL_Rect(config.WIDTH // 2 - 180, 30, 360, 360)
                
                # Marco
                border_width = 10
                border_rect = sdl2.SDL_Rect(
                    cover_rect.x - border_width,
                    cover_rect.y - border_width,
                    cover_rect.w + (border_width * 2),
                    cover_rect.h + (border_width * 2)
                )
                
                # Color del marco #17031D -> R=23, G=3, B=29
                sdl2.SDL_SetRenderDrawColor(renderer, 23, 3, 29, 255)
                sdl2.SDL_RenderFillRect(renderer, ctypes.byref(border_rect))
                
                sdl2.SDL_RenderCopy(renderer, current_cover_tex, None, ctypes.byref(cover_rect))
            else:
                # Placeholder portada
                rect = sdl2.SDL_Rect(config.WIDTH // 2 - 150, 70, 300, 300)
                sdl2.SDL_SetRenderDrawColor(renderer, 100, 100, 100, 255)
                sdl2.SDL_RenderFillRect(renderer, ctypes.byref(rect))
            
            
            max_width = int(config.WIDTH * 0.8)
            text_x = config.WIDTH // 2

            text_y = 420
            
            # Medir ancho del texto
            if config.FONT_MEDIUM:
                w_ptr = ctypes.c_int()
                h_ptr = ctypes.c_int()
                ttf.TTF_SizeUTF8(config.FONT_MEDIUM, track_name.encode('utf-8'), ctypes.byref(w_ptr), ctypes.byref(h_ptr))
                text_w = w_ptr.value
                
                if text_w > max_width:
                    # Cálculo del overflow (cuánto sobra)
                    overflow = text_w - max_width
                    
                    # Lógica de Ping-Pong
                    if marquee_wait > 0:
                        marquee_wait -= 1
                    else:
                        marquee_offset += marquee_direction
                        
                        # Si llegamos al final (texto desplazado a la izquierda)
                        if marquee_offset >= overflow:
                            marquee_offset = overflow
                            marquee_direction = -1
                            marquee_wait = 60 # Esperar 1 segundo antes de regresar
                        
                        # Si regresamos al inicio
                        elif marquee_offset <= 0:
                            marquee_offset = 0
                            marquee_direction = 1
                            marquee_wait = 60 # Esperar 1 segundo antes de avanzar
                            
                    # Renderizado con Clip
                    # El texto se dibuja en start_visible - marquee_offset
                    # marquee_offset va de 0 a overflow
                    
                    start_visible = (config.WIDTH - max_width) // 2
                    draw_x = start_visible - marquee_offset
                    
                    # Definir clip rect
                    clip_rect = sdl2.SDL_Rect(start_visible, text_y, max_width, h_ptr.value)
                    sdl2.SDL_RenderSetClipRect(renderer, ctypes.byref(clip_rect))
                    
                    render_text(renderer, config.FONT_MEDIUM, track_name, config.WHITE, draw_x, text_y, centered=False)
                    
                    sdl2.SDL_RenderSetClipRect(renderer, None) # Quitar clip
                    
                else:
                    # Renderizado normal centrado
                    marquee_offset = 0
                    render_text(renderer, config.FONT_MEDIUM, track_name, config.WHITE, text_x, text_y, centered=True)
            
            status_text = player.get_status_text()
            volume_text = f"Volumen: {int(player.get_volume() * 100)}%"
            
            render_text(renderer, config.FONT_SMALL, status_text, config.GRAY, config.WIDTH // 2, 470, centered=True)
            render_text(renderer, config.FONT_SMALL, volume_text, config.GRAY, config.WIDTH // 2, 510, centered=True)
            
            # Botones
            
            # Highlight PREV
            if btn_highlight_target == "prev":
                 highlight_rect = sdl2.SDL_Rect(
                    rect_prev[0] - 6,
                    rect_prev[1] - 6,
                    rect_prev[2] + 12,
                    rect_prev[3] + 12
                 )
                 sdl2.SDL_SetRenderDrawColor(renderer, 248, 187, 68, 255) # F8BB44
                 sdl2.SDL_RenderFillRect(renderer, ctypes.byref(highlight_rect))

            draw_button(renderer, rect_prev, btn_prev_tex)
            
            # Decidir qué textura usar para el botón Play/Pause
            current_play_tex = btn_play_tex
            if player.is_playing:
                current_play_tex = btn_pause_tex
            
            draw_button(renderer, rect_play, current_play_tex)
            
            # Highlight NEXT
            if btn_highlight_target == "next":
                 highlight_rect = sdl2.SDL_Rect(
                    rect_next[0] - 6,
                    rect_next[1] - 6,
                    rect_next[2] + 12,
                    rect_next[3] + 12
                 )
                 sdl2.SDL_SetRenderDrawColor(renderer, 248, 187, 68, 255) # F8BB44
                 sdl2.SDL_RenderFillRect(renderer, ctypes.byref(highlight_rect))

            draw_button(renderer, rect_next, btn_next_tex)
            
            # Instrucciones
            #render_text(renderer, config.FONT_SMALL, "Controles: Espacio (Play/Pause) | Flechas (Navegar/Volumen)", config.LIGHT_GRAY, config.WIDTH // 2, 650, centered=True)
        
        elif current_view == "playlist":
            playlist_screen.render()

        sdl2.SDL_RenderPresent(renderer)
        
        # Decrementar tiempo de highlight (al final del frame para que sea visible al menos 1 frame)
        if btn_highlight_time > 0:
            btn_highlight_time -= 1
        else:
            btn_highlight_target = None
            
        sdl2.SDL_Delay(16) # ~60 FPS cap

    # Limpieza
    # Asegurar que la pantalla quede encendida al salir
    if screen_off and is_linux_arm64:
        _screen_power(True)
    
    player.stop_music()
    
    # Detener servidores
    if ftp_server: ftp_server.stop()
    if telnet_server: telnet_server.stop()
    
    input_handler.cleanup()
    playlist_screen.cleanup()
    
    if background_tex: sdl2.SDL_DestroyTexture(background_tex)
    if album_cover_tex: sdl2.SDL_DestroyTexture(album_cover_tex)
    if btn_prev_tex: sdl2.SDL_DestroyTexture(btn_prev_tex)
    if btn_play_tex: sdl2.SDL_DestroyTexture(btn_play_tex)
    if btn_next_tex: sdl2.SDL_DestroyTexture(btn_next_tex)
    
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    mix.Mix_CloseAudio()
    ttf.TTF_Quit()
    sdl2.SDL_Quit()

if __name__ == "__main__":
    
    main()
