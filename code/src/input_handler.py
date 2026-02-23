import datetime
import sdl2
import config

class InputHandler:
    def __init__(self, player, log_file="input_log.txt"):
        self.player = player
        self.log_file = log_file
        self.joysticks = {}
        self.mode = "player"
        self._init_joysticks()
        
    def set_mode(self, mode):
        self.mode = mode
        self.log(f"Input mode set to: {mode}")
        
    def _init_joysticks(self):
        # SDL2 ya inicializado en config.py, pero los joysticks se abren aquí
        num_joysticks = sdl2.SDL_NumJoysticks()
        print(f"Encontrados {num_joysticks} joysticks.")
        
        for i in range(num_joysticks):
            joystick = sdl2.SDL_JoystickOpen(i)
            if joystick:
                instance_id = sdl2.SDL_JoystickInstanceID(joystick)
                name = sdl2.SDL_JoystickName(joystick)
                self.joysticks[instance_id] = joystick
                print(f"Joystick {i} conectado: {name.decode('utf-8') if name else 'Unknown'}")
            else:
                print(f"Error abriendo joystick {i}: {sdl2.SDL_GetError()}")

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        # Solo imprimir en consola, flush=True para asegurar salida inmediata
        print(log_entry, flush=True)

    def handle_input(self, event):
        # Event es un objeto SDL_Event
        
        # Teclado
        if event.type == sdl2.SDL_KEYDOWN:
            keysym = event.key.keysym
            scancode = keysym.scancode
            keycode = keysym.sym
            
            # Obtener nombre de tecla
            key_name = sdl2.SDL_GetKeyName(keycode)
            key_name_str = key_name.decode('utf-8') if key_name else "Unknown"
            
            self.log(f"Teclado presionado: {key_name_str} (Scancode: {scancode})")
            
            if keycode == sdl2.SDLK_ESCAPE or keycode == sdl2.SDLK_q:
                self.log("Acción: Salir (ESC/Q)")
                return "QUIT"
                
            # Mapeos de teclado para el reproductor
            if keycode == sdl2.SDLK_SPACE:
                if self.mode == "playlist":
                    return "SELECT_ITEM"
                self.player.toggle_play_pause()
            elif keycode == sdl2.SDLK_RETURN:
                if self.mode == "playlist":
                    return "SELECT_ITEM"
            elif keycode == sdl2.SDLK_RIGHT:
                if self.mode == "playlist": return "NAV_RIGHT"
                self.player.next_track()
                return "NEXT_TRACK"
            elif keycode == sdl2.SDLK_LEFT:
                if self.mode == "playlist": return "NAV_LEFT"
                self.player.prev_track()
                return "PREV_TRACK"
            elif keycode == sdl2.SDLK_UP:
                if self.mode == "playlist": return "NAV_UP"
                current_vol = self.player.get_volume()
                self.player.set_volume(current_vol + 0.1)
            elif keycode == sdl2.SDLK_DOWN:
                if self.mode == "playlist": return "NAV_DOWN"
                current_vol = self.player.get_volume()
                self.player.set_volume(current_vol - 0.1)
            elif keycode == sdl2.SDLK_p:
                return "TOGGLE_PLAYLIST"
            # Mapeo adicional para teclado similar a botones Y/X
            elif keycode == sdl2.SDLK_y: # Equivalente a Botón Y
                if self.mode == "playlist": return "PLAY_DIR"
                self.player.prev_track()
                return "PREV_TRACK"
            elif keycode == sdl2.SDLK_x: # Equivalente a Botón X
                if self.mode == "player": 
                    self.player.next_track() 
                    return "NEXT_TRACK" 

        # Joystick Botones
        elif event.type == sdl2.SDL_JOYBUTTONDOWN:
            which = event.jbutton.which # Instance ID
            button = event.jbutton.button
            self.log(f"Joystick {which} Botón presionado: {button}")
            
            # Asumir mapeos comunes (pueden variar según el control)
            # Select suele ser botón 8 o 9 en algunos mandos, Start 9 o 10
            # Mapeo genérico (ajustar según hardware real)
            if button == 8: # Select / Back (ejemplo)
                self.log("Acción: Salir (Select)")
                return "QUIT"
            
            if button == config.BUTTON_B: # B (0) -> Play/Pause / Select
                if self.mode == "playlist": return "SELECT_ITEM"
                self.player.toggle_play_pause()
            elif button == config.BUTTON_A: # A (1) -> Toggle Playlist
                return "TOGGLE_PLAYLIST" 
            elif button == config.BUTTON_Y: # Y -> Play Dir (Playlist) / Prev Track (Player)
                if self.mode == "playlist": return "PLAY_DIR"
                self.player.prev_track()
                return "PREV_TRACK"
            elif button == config.BUTTON_X: # X -> Next Track (Player)
                if self.mode == "player":
                    self.player.next_track()
                    return "NEXT_TRACK"
            elif button == config.BUTTON_DUP: # DUP
                if self.mode == "playlist": return "NAV_UP" # Page Down opcional
                self.player.next_track()
                return "NEXT_TRACK"
            elif button == config.BUTTON_DDOWN: # DDOWN
                if self.mode == "playlist": return "NAV_DOWN" # Page Up opcional
                self.player.prev_track()
                return "PREV_TRACK"
            elif button == config.BUTTON_START:
                self.player.toggle_repeat_mode()

        # Joystick Hat (D-Pad)
        elif event.type == sdl2.SDL_JOYHATMOTION:
            which = event.jhat.which
            hat = event.jhat.hat
            value = event.jhat.value
            
            hat_str = "CENTER"
            if value == sdl2.SDL_HAT_UP: hat_str = "UP"
            elif value == sdl2.SDL_HAT_RIGHT: hat_str = "RIGHT"
            elif value == sdl2.SDL_HAT_DOWN: hat_str = "DOWN"
            elif value == sdl2.SDL_HAT_LEFT: hat_str = "LEFT"
            
            if value != sdl2.SDL_HAT_CENTERED:
                self.log(f"Joystick {which} Hat {hat} movido: {hat_str}")
            
            if value == sdl2.SDL_HAT_RIGHT:
                if self.mode == "playlist": return "NAV_RIGHT"
                self.player.next_track()
                return "NEXT_TRACK"
            elif value == sdl2.SDL_HAT_LEFT:
                if self.mode == "playlist": return "NAV_LEFT"
                self.player.prev_track()
                return "PREV_TRACK"
            elif value == sdl2.SDL_HAT_UP:
                if self.mode == "playlist": return "NAV_UP"
                current_vol = self.player.get_volume()
                self.player.set_volume(current_vol + 0.1)
            elif value == sdl2.SDL_HAT_DOWN:
                if self.mode == "playlist": return "NAV_DOWN"
                current_vol = self.player.get_volume()
                self.player.set_volume(current_vol - 0.1)

        return None
        
    def cleanup(self):
        for joystick in self.joysticks.values():
            if sdl2.SDL_JoystickGetAttached(joystick):
                sdl2.SDL_JoystickClose(joystick)
        self.joysticks.clear()
