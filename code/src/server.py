import threading
import socket
import os
import sys

# FTP Imports
try:
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import ThreadedFTPServer
    HAS_FTP_LIB = True
except ImportError:
    HAS_FTP_LIB = False
    print("pyftpdlib no está instalado. El servidor FTP no funcionará.")

class SimpleFTPServer:
    def __init__(self, port=2121, root_dir='.'):
        self.port = port
        self.root_dir = os.path.abspath(root_dir)
        self.server = None
        self.thread = None
        self.running = False

    def start(self):
        if not HAS_FTP_LIB:
            return

        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
        print(f"[FTP] Iniciado en puerto {self.port}. Root: {self.root_dir}")

    def _run_server(self):
        try:
            authorizer = DummyAuthorizer()
            # Usuario anónimo con permisos completos (elradfmwMT)
            # e=cambiar dir, l=listar, r=leer, a=agregar, d=borrar, f=renombrar, m=crear dir, w=escribir, M=cambiar modo, T=cambiar hora
            # ¡ADVERTENCIA! Sin seguridad.
            authorizer.add_anonymous(self.root_dir, perm='elradfmwMT')

            handler = FTPHandler
            handler.authorizer = authorizer
            handler.banner = "r36tmax FTP Server Ready."

            address = ('0.0.0.0', self.port)
            self.server = ThreadedFTPServer(address, handler)
            self.server.serve_forever()
        except OSError as e:
            print(f"[FTP] Error de red/puerto al iniciar: {e}. El servidor FTP no estará disponible.")
            self.running = False
        except Exception as e:
            print(f"[FTP] Error inesperado: {e}")
            self.running = False

    def stop(self):
        if self.server:
            self.server.close_all()
            self.running = False
            print("[FTP] Detenido.")

class SimpleTelnetServer:
    def __init__(self, port=2323):
        self.port = port
        self.server_socket = None
        self.thread = None
        self.running = False
        self.clients = []

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
        print(f"[Telnet] Iniciado en puerto {self.port}")

    def _run_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)

            while self.running:
                try:
                    client, addr = self.server_socket.accept()
                    print(f"[Telnet] Conexión desde {addr}")
                    client_thread = threading.Thread(target=self._handle_client, args=(client,))
                    client_thread.daemon = True
                    client_thread.start()
                    self.clients.append(client)
                except OSError:
                    # Socket cerrado
                    break
                except Exception as e:
                    print(f"[Telnet] Error aceptando conexión: {e}")

        except OSError as e:
            print(f"[Telnet] Error de red/puerto (bind falló): {e}. El servidor Telnet no estará disponible.")
        except Exception as e:
            print(f"[Telnet] Error fatal: {e}")
        finally:
            self.running = False

    def _handle_client(self, client_socket):
        # Contexto del cliente (directorio actual)
        cwd = os.getcwd()
        
        try:
            client_socket.send(b"Welcome to r36tmax Telnet Server\r\n")
            client_socket.send(b"Type 'help' for commands, 'exit' to disconnect.\r\n> ")

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # Procesar comando simple
                text = data.decode('utf-8', errors='ignore').strip()
                if not text:
                    client_socket.send(b"> ")
                    continue

                response, cwd = self._process_command(text, cwd)
                client_socket.send(response.encode('utf-8') + b"\r\n> ")
                
                if text.lower() == 'exit':
                    break

        except Exception as e:
            print(f"[Telnet] Cliente desconectado por error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            if client_socket in self.clients:
                self.clients.remove(client_socket)

    def _process_command(self, cmd_line, cwd):
        parts = cmd_line.split()
        if not parts:
            return "", cwd
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == 'help':
            return "Commands: hello, status, ls, cd <dir>, cat <file>, exit", cwd
        elif cmd == 'hello':
            return "Hello there!", cwd
        elif cmd == 'status':
            return "Server is running smoothly.", cwd
        elif cmd == 'ls':
            try:
                files = os.listdir(cwd)
                return "\n".join(files), cwd
            except Exception as e:
                return f"Error listing directory: {e}", cwd
        elif cmd == 'cd':
            if not args:
                return "Usage: cd <directory>", cwd
            
            target = args[0]
            try:
                new_path = os.path.join(cwd, target)
                new_path = os.path.abspath(new_path)
                if os.path.isdir(new_path):
                    return f"Changed directory to {new_path}", new_path
                else:
                    return f"Directory not found: {target}", cwd
            except Exception as e:
                return f"Error changing directory: {e}", cwd
        elif cmd == 'cat':
            if not args:
                return "Usage: cat <file>", cwd
            
            target = args[0]
            try:
                file_path = os.path.join(cwd, target)
                if os.path.isfile(file_path):
                    # Limitar tamaño de lectura por seguridad
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read(2048) # Leer máx 2KB
                        if len(content) == 2048:
                            content += "\n... (truncated)"
                        return content, cwd
                else:
                    return f"File not found: {target}", cwd
            except Exception as e:
                return f"Error reading file: {e}", cwd
        elif cmd == 'exit':
            return "Goodbye!", cwd
        else:
            return f"Unknown command: {cmd}", cwd

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Cerrar clientes
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients = []
        print("[Telnet] Detenido.")

# Función de utilidad para iniciar ambos
def start_servers(ftp_port=2121, telnet_port=2323, root_dir='.'):
    ftp = SimpleFTPServer(port=ftp_port, root_dir=root_dir)
    telnet = SimpleTelnetServer(port=telnet_port)
    
    ftp.start()
    telnet.start()
    
    return ftp, telnet

if __name__ == "__main__":
    # Prueba standalone
    print("Iniciando servidores en modo prueba (Ctrl+C para salir)...")
    ftp, telnet = start_servers()
    
    try:
        # Mantener vivo el hilo principal
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo servidores...")
        ftp.stop()
        telnet.stop()
        print("Hecho.")
