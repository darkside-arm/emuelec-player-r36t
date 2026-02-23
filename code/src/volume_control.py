import platform
import subprocess
import time
import threading

class VolumeControl:
    def __init__(self):
        self.os_name = platform.system()
        self.interface = None
        self.current_volume = 50
        self.last_check = 0
        self.check_interval = 2.0 # Chequear cada 2 segundos
        self.controls_linux = ["Master", "PCM", "Headphone", "Speaker", "Digital"]
        self.active_control_linux = None
        
        if self.os_name == "Windows":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                # Inicialización COM necesaria si se ejecuta en hilo
                import comtypes
                comtypes.CoInitialize()
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.interface = cast(interface, POINTER(IAudioEndpointVolume))
                self.current_volume = int(self.interface.GetMasterVolumeLevelScalar() * 100)
            except Exception as e:
                print(f"Advertencia: No se pudo inicializar control de volumen Windows: {e}")
                self.os_name = "Generic" # Fallback

        elif self.os_name == "Linux":
            self._find_linux_control()
            self._update_linux_volume()

    def _find_linux_control(self):
        for control in self.controls_linux:
            try:
                subprocess.check_output(["amixer", "get", control], stderr=subprocess.DEVNULL)
                self.active_control_linux = control
                print(f"Control de volumen Linux encontrado: {control}")
                break
            except:
                continue

    def _update_linux_volume(self):
        if not self.active_control_linux:
            return

        try:
            res = subprocess.check_output(["amixer", "get", self.active_control_linux], stderr=subprocess.DEVNULL).decode()
            import re
            # Buscar patrón [50%]
            m = re.search(r"\[(\d+)%\]", res)
            if m:
                self.current_volume = int(m.group(1))
        except Exception:
            pass

    def get_volume(self):
        # Rate limiting para no bloquear el loop principal con llamadas al sistema
        now = time.time()
        if now - self.last_check > self.check_interval:
            self.last_check = now
            # Actualizar en hilo separado para no bloquear renderizado? 
            # Por simplicidad, lo hacemos aquí pero solo cada X segundos.
            # En Windows pycaw es rápido. En Linux subprocess toma tiempo.
            
            if self.os_name == "Windows" and self.interface:
                try:
                    self.current_volume = int(self.interface.GetMasterVolumeLevelScalar() * 100)
                except:
                    pass
            elif self.os_name == "Linux":
                # En Linux lanzar un hilo para no bloquear frame
                threading.Thread(target=self._update_linux_volume, daemon=True).start()
        
        return self.current_volume

    def set_volume(self, percent):
        # percent 0-100
        percent = max(0, min(100, int(percent)))
        self.current_volume = percent
        
        if self.os_name == "Windows" and self.interface:
            try:
                scalar = percent / 100.0
                self.interface.SetMasterVolumeLevelScalar(scalar, None)
            except:
                pass
        elif self.os_name == "Linux" and self.active_control_linux:
            try:
                subprocess.Popen(["amixer", "set", self.active_control_linux, f"{percent}%"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
