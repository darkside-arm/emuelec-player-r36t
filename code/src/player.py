import os
import sys
import glob
import ctypes
import sdl2
import sdl2.sdlmixer as mix
from volume_control import VolumeControl
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

class MusicPlayer:
    def __init__(self):
        self.playlist = []
        self.current_track_index = 0
        self.is_paused = False
        self.is_playing = False
        self.volume_control = VolumeControl()
        initial_vol = self.volume_control.get_volume()
        if initial_vol == 0:
            initial_vol = 40
            self.volume_control.set_volume(initial_vol)
        self.volume = initial_vol / 100.0 * 128 # Sincronizar inicial
        self.current_music = None
        self.repeat_mode = 0 # 0: No repeat, 1: Repeat all, 2: Repeat one
        
        # Explorador de archivos
        self.current_path = os.getcwd()
        self.browser_items = []
        self.update_browser_items()

    def update_browser_items(self):
        self.browser_items = []
        try:
            # Listar todo el contenido
            items = os.listdir(self.current_path)
            
            # Separar en carpetas y archivos
            dirs = []
            files = []
            
            for item in items:
                full_path = os.path.join(self.current_path, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                elif item.lower().endswith('.mp3'):
                    files.append(item)
            
            # Ordenar alfabéticamente cada lista
            dirs.sort()
            files.sort()
            
            # Opción para subir de directorio si no estamos en la raíz
            parent = os.path.dirname(self.current_path)
            if parent and parent != self.current_path:
                self.browser_items.append({
                    'name': '..',
                    'type': 'dir',
                    'path': parent
                })

            # Agregar carpetas primero
            for item in dirs:
                full_path = os.path.join(self.current_path, item)
                self.browser_items.append({
                    'name': item,
                    'type': 'dir',
                    'path': full_path
                })
                
            # Agregar archivos después
            for item in files:
                full_path = os.path.join(self.current_path, item)
                
                display_name = item
                try:
                    audio = MP3(full_path, ID3=EasyID3)
                    if 'title' in audio:
                        display_name = audio['title'][0]
                except:
                    pass
                
                self.browser_items.append({
                    'name': display_name,
                    'type': 'file',
                    'path': full_path
                })
                
        except Exception as e:
            print(f"Error listando directorio {self.current_path}: {e}")

    def load_music(self):
        # Buscar archivos mp3 (Comportamiento original preservado para inicio automático o búsqueda general)
        self.playlist = []
        
        # Prioridad: ../music (Solicitado)
        # Fallback: music, .
        search_dirs = ["music", "/storage/roms/music"]
        if hasattr(sys, '_MEIPASS') and os.name == 'nt':
            search_dirs = ["C:\\Users\\sivan\\source\\repos\\r36tmax\\music"]
        
        # Intentar establecer un directorio inicial lógico para el browser
        for d in search_dirs:
            if os.path.exists(d):
                self.current_path = os.path.abspath(d)
                self.update_browser_items()
                break

        for d in search_dirs:
            if os.path.exists(d):
                # Usar os.path.join para compatibilidad de SO
                pattern = os.path.join(d, "*.mp3")
                for file in glob.glob(pattern):
                    abs_path = os.path.abspath(file)
                    if abs_path not in self.playlist:
                        self.playlist.append(abs_path)


        if self.playlist:
            self.current_track_index = 0
            print(f"Cargadas {len(self.playlist)} canciones. (Buscado en: {', '.join(search_dirs)})")
        else:
            print(f"No se encontraron archivos .mp3 en: {', '.join(search_dirs)}")

    def play_from_directory(self):
        """Carga y reproduce todos los mp3 del directorio actual del browser"""
        new_playlist = [item['path'] for item in self.browser_items if item['type'] == 'file']
        if new_playlist:
            self.stop_music()
            self.playlist = new_playlist
            self.current_track_index = 0
            self.play_music()
            print(f"Reproduciendo directorio: {self.current_path}")
        else:
            print("No hay archivos mp3 en este directorio")

    def play_music(self):
        if self.playlist:
            if self.is_paused:
                mix.Mix_ResumeMusic()
                self.is_paused = False
                self.is_playing = True
            else:
                try:
                    if self.current_music:
                        mix.Mix_FreeMusic(self.current_music)
                    
                    track_path = self.playlist[self.current_track_index].encode('utf-8')
                    self.current_music = mix.Mix_LoadMUS(track_path)
                    
                    if not self.current_music:
                        print(f"Error cargando música: {mix.Mix_GetError()}")
                        return

                    mix.Mix_PlayMusic(self.current_music, 1)
                    self.is_playing = True
                    self.is_paused = False
                    # Aplicar volumen inicial
                    mix.Mix_VolumeMusic(int(self.volume))
                    
                except Exception as e:
                    print(f"Error al reproducir: {e}")

    def pause_music(self):
        if self.is_playing:
            mix.Mix_PauseMusic()
            self.is_paused = True
            self.is_playing = False

    def stop_music(self):
        mix.Mix_HaltMusic()
        self.is_playing = False
        self.is_paused = False

    def next_track(self):
        if self.playlist:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            self.is_paused = False
            self.play_music()

    def prev_track(self):
        if self.playlist:
            self.current_track_index = (self.current_track_index - 1) % len(self.playlist)
            self.is_paused = False
            self.play_music()

    def toggle_play_pause(self):
        if not self.playlist:
            return
            
        if self.is_playing:
            self.pause_music()
        elif self.is_paused:
            self.play_music()
        else:
            self.play_music()
            
    def set_volume(self, vol_percent):
        # vol_percent is 0.0 to 1.0
        # Actualizar volumen del sistema
        percent = int(max(0.0, min(1.0, vol_percent)) * 100)
        self.volume_control.set_volume(percent)
        
        # También actualizar volumen interno de SDL Mixer por si acaso
        sdl_vol = int(max(0.0, min(1.0, vol_percent)) * 128)
        self.volume = sdl_vol
        mix.Mix_VolumeMusic(self.volume)
        
    def get_volume(self):
        # Obtener volumen real del sistema (o caché)
        sys_vol = self.volume_control.get_volume()
        return sys_vol / 100.0
        
    def get_current_track_name(self):
        if self.playlist and 0 <= self.current_track_index < len(self.playlist):
            track_path = self.playlist[self.current_track_index]
            try:
                audio = MP3(track_path, ID3=EasyID3)
                if 'title' in audio:
                    return audio['title'][0]
            except Exception:
                pass
            return os.path.basename(track_path)
        return None
        
    def get_current_track_cover(self):
        """
        Intenta extraer la imagen de portada (APIC) del archivo MP3 actual.
        Retorna los datos binarios de la imagen o None si no hay.
        """
        if self.playlist and 0 <= self.current_track_index < len(self.playlist):
            track_path = self.playlist[self.current_track_index]
            try:
                # Usar MP3 de mutagen para acceder a tags ID3 raw
                audio = MP3(track_path)
                # Buscar tags APIC (Attached Picture)
                for tag in audio.tags.values():
                    if tag.FrameID == 'APIC':
                        return tag.data
            except Exception:
                pass
        return None

    def get_status_text(self):
        status = "Detenido"
        if self.is_paused:
            status = "Pausado"
        elif self.is_playing:
            status = "Reproduciendo"
            
        repeat_texts = ["No repeat", "Repeat all", "Repeat this one"]
        return f"{status} / {repeat_texts[self.repeat_mode]}"

    def toggle_repeat_mode(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3

    def update(self):
        # Verificar si la música terminó
        if self.is_playing and not self.is_paused:
            if mix.Mix_PlayingMusic() == 0:
                self.on_music_finished()
                
    def on_music_finished(self):
        if self.repeat_mode == 2: # Repeat one
            self.play_music()
        elif self.repeat_mode == 1: # Repeat all
            self.next_track()
        else: # No repeat
            if self.current_track_index < len(self.playlist) - 1:
                self.next_track()
            else:
                self.stop_music()

def draw_button(renderer, rect, image_texture, action=None, input_handler=None):
    # Detección simple de clic
    # En SDL2 puro, la detección de colisión de mouse se suele hacer en el bucle de eventos
    # Pero para mantener la estructura, podemos chequear el estado del mouse aquí
    
    x = ctypes.c_int(0)
    y = ctypes.c_int(0)
    mouse_state = sdl2.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
    
    mouse_point = sdl2.SDL_Point(x.value, y.value)
    sdl_rect = sdl2.SDL_Rect(rect[0], rect[1], rect[2], rect[3])
    
    # SDL_PointInRect en pysdl2 es una función python que espera objetos, no punteros
    is_hover = sdl2.SDL_PointInRect(mouse_point, sdl_rect)
    is_clicked = (mouse_state & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_LEFT))
    
    # Dibujar textura
    if image_texture:
        sdl2.SDL_RenderCopy(renderer, image_texture, None, ctypes.byref(sdl_rect))
    else:
        # Fallback rectángulo
        r, g, b, a = 50, 50, 50, 255
        if is_hover:
            r, g, b = 80, 80, 80
            
        sdl2.SDL_SetRenderDrawColor(renderer, r, g, b, a)
        sdl2.SDL_RenderFillRect(renderer, ctypes.byref(sdl_rect))
    
    # Lógica de clic (simple debouncing externo necesario o flag)
    # Nota: Es mejor manejar los clics en el bucle de eventos para evitar múltiples disparos
    # Esta función ahora solo debería dibujar y quizás retornar si fue clicada para que el main loop actúe
    
    return is_hover and is_clicked
