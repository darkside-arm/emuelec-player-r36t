import os
import ctypes
import sdl2
import sdl2.ext
import sdl2.sdlimage as img
import sdl2.sdlttf as ttf
import config

class PlaylistScreen:
    def __init__(self, renderer, player):
        self.renderer = renderer
        self.player = player # Referencia al player para acceder a browser_items
        self.background_tex = None
        self.folder_icon = None
        self.file_icon = None
        self.font_browser = None
        self.selected_index = 0  # Índice del elemento seleccionado
        self.scroll_offset = 0   # Desplazamiento de visualización
        
        # Variables Marquee
        self.marquee_offset = 0
        self.marquee_direction = 1
        self.marquee_wait = 0
        self.last_selected_index = -1
        
        self._load_assets()

    def move_up(self):
        if self.selected_index > 0:
            self.selected_index -= 1
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index

    def move_down(self):
        if self.selected_index < len(self.player.browser_items) - 1:
            self.selected_index += 1
            item_height = 70
            max_items = (config.HEIGHT - 100) // item_height
            if self.selected_index >= self.scroll_offset + max_items:
                self.scroll_offset = self.selected_index - max_items + 1

    def get_selected_item(self):
        if 0 <= self.selected_index < len(self.player.browser_items):
            return self.player.browser_items[self.selected_index]
        return None

    def _load_assets(self):
        # Fondo
        bg_path = os.path.join(config.ASSETS_DIR, 'bk1.jpg')
        if os.path.exists(bg_path):
            surface = img.IMG_Load(bg_path.encode('utf-8'))
            if surface:
                self.background_tex = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
                sdl2.SDL_FreeSurface(surface)
        
        # Iconos
        fold_path = os.path.join(config.ASSETS_DIR, 'fold.png')
        file_path = os.path.join(config.ASSETS_DIR, 'filemp3.png')
        
        self.folder_icon = self._load_texture(fold_path)
        self.file_icon = self._load_texture(file_path)

        # Fuente
        font_path = os.path.join(config.ASSETS_DIR, 'PublicPixel.ttf')
        if os.path.exists(font_path):
            self.font_browser = ttf.TTF_OpenFont(font_path.encode('utf-8'), 18)
        else:
            print(f"Fuente no encontrada: {font_path}")

    def _load_texture(self, path):
        if os.path.exists(path):
            surface = img.IMG_Load(path.encode('utf-8'))
            if surface:
                tex = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
                sdl2.SDL_FreeSurface(surface)
                return tex
        return None

    def render(self):
        # Dibujar Fondo
        if self.background_tex:
            sdl2.SDL_RenderCopy(self.renderer, self.background_tex, None, None)
        else:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 50, 0, 0, 255)
            sdl2.SDL_RenderClear(self.renderer)

        # Dibujar lista de archivos
        self._draw_browser()

        # Dibujar leyenda
        self._draw_legend()

    def _draw_browser(self):
        if not self.font_browser:
            return

        start_x = 50
        start_y = 50
        item_height = 70 # 64px icono + padding
        
        max_items = (config.HEIGHT - 100) // item_height
        
        # Obtener items visibles según scroll
        visible_items = self.player.browser_items[self.scroll_offset : self.scroll_offset + max_items]
        
        for i, item in enumerate(visible_items):
            real_index = self.scroll_offset + i
            y = start_y + i * item_height
            
            # Dibujar selección
            if real_index == self.selected_index:
                # Rectángulo de selección
                sel_rect = sdl2.SDL_Rect(start_x - 5, y - 5, config.WIDTH - 2 * start_x + 10, item_height)
                
                sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_BLEND)
                # Blanco con 30% opacidad (aprox 76)
                sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 255, 76)
                sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(sel_rect))
                sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_NONE)

            # Dibujar icono (64x64)
            icon = self.folder_icon if item['type'] == 'dir' else self.file_icon
            if icon:
                icon_rect = sdl2.SDL_Rect(start_x, y, 64, 64)
                sdl2.SDL_RenderCopy(self.renderer, icon, None, ctypes.byref(icon_rect))
            
            # Dibujar texto
            
            # Gestión de Marquee si es el seleccionado
            is_selected = (real_index == self.selected_index)
            draw_offset_x = 0
            use_clip = False
            
            # Ancho máximo disponible para texto
            # start_x (50) + 74 (icono+pad) = 124 inicio texto
            # config.WIDTH - 124 - 50 (margen derecho)
            max_text_width = config.WIDTH - 174 
            
            # Medir texto primero
            w_ptr = ctypes.c_int()
            h_ptr = ctypes.c_int()
            ttf.TTF_SizeUTF8(self.font_browser, item['name'].encode('utf-8'), ctypes.byref(w_ptr), ctypes.byref(h_ptr))
            text_w = w_ptr.value
            text_h = h_ptr.value
            
            if is_selected:
                if self.selected_index != self.last_selected_index:
                    self.last_selected_index = self.selected_index
                    self.marquee_offset = 0
                    self.marquee_direction = 1
                    self.marquee_wait = 60
                
                if text_w > max_text_width:
                    overflow = text_w - max_text_width
                    
                    if self.marquee_wait > 0:
                        self.marquee_wait -= 1
                    else:
                        self.marquee_offset += self.marquee_direction
                        if self.marquee_offset >= overflow:
                            self.marquee_offset = overflow
                            self.marquee_direction = -1
                            self.marquee_wait = 60
                        elif self.marquee_offset <= 0:
                            self.marquee_offset = 0
                            self.marquee_direction = 1
                            self.marquee_wait = 60
                            
                    draw_offset_x = -self.marquee_offset
                    use_clip = True
            
            # Renderizar
            text_surface = ttf.TTF_RenderUTF8_Blended(self.font_browser, item['name'].encode('utf-8'), config.WHITE)
            if text_surface:
                text_tex = sdl2.SDL_CreateTextureFromSurface(self.renderer, text_surface)
                
                # Centrar texto verticalmente respecto al icono
                text_y = y + (64 - text_h) // 2
                text_x_pos = start_x + 74
                
                if use_clip:
                    # Clip al área de texto disponible
                    clip_rect = sdl2.SDL_Rect(text_x_pos, text_y, max_text_width, text_h)
                    sdl2.SDL_RenderSetClipRect(self.renderer, ctypes.byref(clip_rect))
                    
                    text_rect = sdl2.SDL_Rect(text_x_pos + draw_offset_x, text_y, text_w, text_h)
                    sdl2.SDL_RenderCopy(self.renderer, text_tex, None, ctypes.byref(text_rect))
                    
                    sdl2.SDL_RenderSetClipRect(self.renderer, None)
                else:
                    # Si es muy largo pero no seleccionado, o cabe bien, cortar o dibujar normal
                    # Aquí dibujamos normal, pero si excede se cortará visualmente por el borde de pantalla o
                    # podemos forzar clip si queremos que no se salga
                    
                    if text_w > max_text_width and not is_selected:
                         # Opcional: Cortar si es muy largo y no está seleccionado
                         clip_rect = sdl2.SDL_Rect(text_x_pos, text_y, max_text_width, text_h)
                         sdl2.SDL_RenderSetClipRect(self.renderer, ctypes.byref(clip_rect))
                         
                         text_rect = sdl2.SDL_Rect(text_x_pos, text_y, text_w, text_h)
                         sdl2.SDL_RenderCopy(self.renderer, text_tex, None, ctypes.byref(text_rect))
                         
                         sdl2.SDL_RenderSetClipRect(self.renderer, None)
                    else:
                        text_rect = sdl2.SDL_Rect(text_x_pos, text_y, text_w, text_h)
                        sdl2.SDL_RenderCopy(self.renderer, text_tex, None, ctypes.byref(text_rect))
                
                sdl2.SDL_DestroyTexture(text_tex)
                sdl2.SDL_FreeSurface(text_surface)

    def _draw_legend(self):
        text = "A: Play current directory"
        font = config.FONT_SMALL
        
        if not font:
            return

        # Renderizar texto para obtener dimensiones
        # Usamos config.WHITE para el texto
        surface = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), config.WHITE)
        if not surface:
            return

        w = surface.contents.w
        h = surface.contents.h

        # Posición (centrado abajo)
        x = (config.WIDTH - w) // 2
        y = config.HEIGHT - 60 # Un poco arriba del borde inferior

        # Padding para el frame
        padding_x = 20
        padding_y = 10
        
        # Rectángulo del frame
        rect = sdl2.SDL_Rect(x - padding_x, y - padding_y, w + padding_x * 2, h + padding_y * 2)

        # Dibujar frame con transparencia
        # 70% transparencia = 30% opacidad. 255 * 0.3 ~= 76.
        sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 76) 
        sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(rect))
        sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_NONE)

        # Dibujar texto
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        text_rect = sdl2.SDL_Rect(x, y, w, h)
        sdl2.SDL_RenderCopy(self.renderer, texture, None, ctypes.byref(text_rect))

        sdl2.SDL_DestroyTexture(texture)
        sdl2.SDL_FreeSurface(surface)
            
    def cleanup(self):
        if self.background_tex:
            sdl2.SDL_DestroyTexture(self.background_tex)
        if self.folder_icon:
            sdl2.SDL_DestroyTexture(self.folder_icon)
        if self.file_icon:
            sdl2.SDL_DestroyTexture(self.file_icon)
        if self.font_browser:
            ttf.TTF_CloseFont(self.font_browser)
