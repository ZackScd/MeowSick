import discord
from discord.ext import commands
import asyncio
import os
import sys
import json
import threading
import shutil
import signal
import logging
from logging.handlers import RotatingFileHandler
import socket
from dotenv import load_dotenv
from shared.config_manager import ConfigManager
from shared.language_manager import LanguageManager

# --- 1. CONFIGURACIÓN DE ENTORNO Y RUTAS ---
# Determina el directorio base del proyecto. Es crucial para que el empaquetado con PyInstaller funcione.
# Si el script se ejecuta como un archivo congelado (.exe), `sys.executable` apunta al ejecutable.
# Si se ejecuta como un script .py, `__file__` apunta al propio script.
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# Determina el directorio de ejecución para los recursos internos.
# En un .exe, los archivos empaquetados (como los cogs) se extraen a una carpeta temporal `_MEIPASS`.
# En modo script, el directorio de ejecución es el mismo que el base.
RUNTIME_DIR = sys._MEIPASS if getattr(sys, 'frozen', False) else BASE_DIR

# Define rutas absolutas para directorios clave, asegurando consistencia.
SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
COGS_DIR = os.path.join(RUNTIME_DIR, "cogs") 

# Asegura la existencia de los directorios necesarios en tiempo de ejecución.
os.makedirs(SETTINGS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
# En modo script, esto asegura que la carpeta 'cogs' exista si se borra accidentalmente.
# En modo ejecutable (.exe), esta operación es inocua sobre el directorio temporal _MEIPASS,
# que es de solo lectura pero ya contiene los cogs empaquetados por el compilador.
os.makedirs(COGS_DIR, exist_ok=True)

# Carga las variables de entorno desde el archivo .env ubicado en el directorio de configuraciones.
load_dotenv(os.path.join(SETTINGS_DIR, ".env"))

# --- 2. CLASE PRINCIPAL DEL BOT (V3) ---
class MeowSickBot(commands.Bot):
    def __init__(self):
        # Carga la configuración principal desde 'config.json'. Si no existe, crea uno con valores por defecto.
        self.config = self._load_json("config.json", {"prefix": "!", "owner_id": 0})
        
        lang_code = self.config.get("language", "es")
        self.lang = LanguageManager(os.path.join(SETTINGS_DIR, "locales"), lang_code)
        
        # Define los 'Intents' del bot. 'all()' activa todos los eventos,
        # lo cual es necesario para funcionalidades como leer el contenido de los mensajes y rastrear miembros del servidor.
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix=self._get_prefix, # Utiliza una función para obtener el prefijo, permitiendo que se actualice en caliente.
            intents=intents,
            help_command=None, # Desactiva el comando de ayuda por defecto para implementar uno personalizado en un cog.
            case_insensitive=True
        )

    def _get_prefix(self, bot, message):
        """Callback para obtener el prefijo de comando actual desde la configuración en memoria."""
        return self.config.get("prefix", "!")

    def _load_json(self, filename, default):
        """
        Carga un archivo JSON desde el directorio de configuraciones.
        Si el archivo no existe, lo crea con el contenido 'default' proporcionado.
        Retorna el contenido del JSON o el valor por defecto en caso de error.
        """
        path = os.path.join(SETTINGS_DIR, filename)
        use_lock = filename == "config.json" or "outputs_" in filename
        if not os.path.exists(path):
            ConfigManager.save_json(path, default, use_lock=use_lock)
            return default
        
        data = ConfigManager.load_json(path, use_lock=use_lock)
        return data if data else default

    def send_ipc_progress(self, pct, msg):
        """Envía un paquete de progreso serializado al Launcher."""
        payload = {"type": "event", "name": "progress_update", "payload": {"percent": float(pct), "message": msg}}
        print(f"IPC>>{json.dumps(payload, ensure_ascii=False)}", flush=True)

    async def setup_hook(self):
        """
        Hook que se ejecuta automáticamente después del login pero antes de conectarse al WebSocket.
        Es el lugar ideal para la configuración asíncrona inicial, como la carga de cogs.
        """
        self.send_ipc_progress(0.1, self.lang.get('sys_ipc_prog_clean'))
        self.clean_cache() # Realiza una limpieza de archivos temporales al iniciar.
        await self.sync_modules()
        # La sincronización de comandos de barra (slash commands) se puede habilitar aquí si se utilizan.
        # await self.tree.sync() 

    async def sync_modules(self):
        """
        Sincroniza el estado de los cogs (módulos) con la configuración en 'config.json'.
        Carga, descarga o recarga extensiones dinámicamente sin necesidad de reiniciar el bot.
        """
        # Recarga la configuración desde el disco para asegurar que se usan los valores más recientes.
        self.config = self._load_json("config.json", {"prefix": "!", "modules": {}})
        
        # Refresca el idioma si fue modificado en el launcher
        self.lang.load_language(self.config.get("language", "es"))
        print(self.lang.get("sys_sync_modules"))
        
        modules_conf = self.config.get("modules", {})
        
        # Escanea el directorio de cogs para encontrar todos los módulos disponibles.
        # Identifica tanto archivos .py individuales como directorios que son paquetes (contienen __init__.py).
        files = [f[:-3] for f in os.listdir(COGS_DIR) if f.endswith(".py") and not f.startswith("_")]
        dirs = [d for d in os.listdir(COGS_DIR) if os.path.isdir(os.path.join(COGS_DIR, d)) and not d.startswith("_")]
        
        available_cogs = list(set(files + dirs))
        
        # Parche PyInstaller: Forzar inclusión de carpetas que el entorno virtual oculta
        for essential in ["AI", "music", "help"]:
            if essential not in available_cogs and essential.lower() not in available_cogs:
                available_cogs.append(essential)

        total_cogs = len(available_cogs)
        for i, cog_name in enumerate(available_cogs):
            # Escala del 20% al 80% progresivamente por cada módulo encontrado
            pct = 0.2 + (i / max(1, total_cogs)) * 0.6
            self.send_ipc_progress(pct, self.lang.get('sys_ipc_prog_load').format(module=cog_name))
            
            ext_name = f"cogs.{cog_name}"
            # Si no está en config, asumimos False (Desactivado) para seguridad
            # Intento 1: Nombre exacto
            should_load = modules_conf.get(cog_name, False)
            # Intento 2: Minúsculas (ej: carpeta 'Music' -> config 'music')
            if not should_load: should_load = modules_conf.get(cog_name.lower(), False)
            # Intento 3: Mapeo manual AI -> ia (Inglés/Español)
            if not should_load and cog_name.upper() == "AI": should_load = modules_conf.get("ia", False)

            # Lógica especial para cargar los submódulos de IA (Compatible con PyInstaller)
            if cog_name.upper() == "AI":
                if should_load:
                    print(self.lang.get("sys_ai_init").format(cog_name=cog_name))
                sub_cogs = ["cogs.AI.core", "cogs.AI.memory", "cogs.AI.evolution"]
                for sc in sub_cogs:
                    is_loaded = sc in self.extensions
                    try:
                        if should_load:
                            if is_loaded:
                                await self.reload_extension(sc)
                                print(self.lang.get("sys_ai_reload").format(sc=sc.split('.')[-1]))
                            else:
                                await self.load_extension(sc)
                                print(self.lang.get("sys_ai_load").format(sc=sc.split('.')[-1]))
                        else:
                            if is_loaded:
                                await self.unload_extension(sc)
                                print(self.lang.get("sys_ai_disable").format(sc=sc.split('.')[-1]))
                            else:
                                print(self.lang.get("sys_ai_ignore").format(sc=sc.split('.')[-1]))
                    except Exception as e:
                        print(self.lang.get("sys_ai_err").format(sc=sc, e=e))
                if should_load:
                    print(self.lang.get("sys_ai_online"))
                continue

            is_loaded = ext_name in self.extensions
            
            try:
                if should_load:
                    # Si debe estar cargado, se recarga si ya lo está, o se carga si no.
                    if is_loaded:
                        await self.reload_extension(ext_name)
                        print(self.lang.get("sys_cog_reload").format(cog_name=cog_name)) # Hot-reload
                    else:
                        await self.load_extension(ext_name)
                        print(self.lang.get("sys_cog_load").format(cog_name=cog_name))
                else:
                    if is_loaded:
                        await self.unload_extension(ext_name)
                        print(self.lang.get("sys_cog_disable").format(cog_name=cog_name))
                    else:
                        print(self.lang.get("sys_cog_ignore").format(cog_name=cog_name))
            except Exception as e:
                print(self.lang.get("sys_cog_err").format(cog_name=cog_name, e=e))
                
        if self.is_ready():
            self.send_ipc_progress(1.0, self.lang.get('sys_ipc_prog_done'))
        else:
            self.send_ipc_progress(0.8, self.lang.get('sys_ipc_prog_conn'))

    def clean_cache(self):
        """
        Elimina directorios y archivos temporales generados por Python (`__pycache__`)
        y por el módulo de música (`downloads`) para asegurar un estado limpio.
        """
        print(self.lang.get("sys_cleaning_cache"))
        targets = [
            os.path.join(BASE_DIR, "downloads"),
            os.path.join(BASE_DIR, "__pycache__"),
            os.path.join(COGS_DIR, "__pycache__")
        ]
        
        for target in targets:
            if os.path.exists(target):
                try:
                    if os.path.isdir(target): shutil.rmtree(target)
                    else: os.remove(target)
                except Exception as e:
                    print(self.lang.get("sys_clean_err").format(target=target, e=e))
        
        # Recrea el directorio de descargas después de limpiarlo.
        os.makedirs(os.path.join(BASE_DIR, "downloads"), exist_ok=True)

    async def on_ready(self):
        """
        Evento que se dispara cuando el bot ha establecido una conexión exitosa con Discord
        y ha finalizado su preparación interna.
        """
        self.send_ipc_progress(1.0, self.lang.get('sys_ipc_prog_online'))
        print(f"\n{self.lang.get('sys_online').format(user=self.user, uid=self.user.id)}")
        print(self.lang.get("sys_discord_conn"))
        print(self.lang.get("sys_wait_cmds"))
        
        # Lógica para enviar un mensaje de bienvenida a un canal específico.
        lang_code = self.config.get("language", "es")
        outputs = self._load_json(f"locales/outputs_{lang_code}.json", {})
        welcome_msg = outputs.get("welcome_message", "")
        
        if welcome_msg:
            channel_id = os.getenv("WELCOME_CHANNEL_ID")
            if channel_id and channel_id.isdigit():
                channel = self.get_channel(int(channel_id))
                if channel:
                    try: await channel.send(welcome_msg)
                    except Exception as e: print(self.lang.get("sys_welcome_err").format(e=e))

    async def close(self):
        """
        Sobrescribe el método `close` de la clase base para añadir lógica de limpieza personalizada
        antes de que el bot se desconecte completamente.
        """
        print(self.lang.get("sys_shutdown_conn"))
        
        # Itera sobre todos los clientes de voz activos y los desconecta forzosamente.
        for vc in self.voice_clients:
            try:
                await vc.disconnect(force=True)
            except Exception: 
                logging.getLogger("Daemon").error("Error al desconectar el cliente de voz durante el apagado", exc_info=True)
        
        # Llama al método `close` original para manejar la desconexión del WebSocket de Discord.
        await super().close()
        self.clean_cache() # Realiza una última limpieza de caché.
        print(self.lang.get("sys_shutdown_ok"))

# --- 3. GESTIÓN DE PROCESOS (IPC) ---
async def console_listener(bot):
    """
    Listener asíncrono para la comunicación entre procesos (IPC).
    Escucha comandos enviados desde el Launcher a través de la entrada estándar (stdin)
    sin bloquear el bucle de eventos principal del bot.
    """
    loop = asyncio.get_running_loop()
    
    while True:
        # `sys.stdin.readline()` es una operación de I/O bloqueante.
        # Se ejecuta en un `ThreadPoolExecutor` para no congelar el bucle de eventos de asyncio.
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line: # Se recibe EOF (End-of-File) cuando el pipe de stdin se cierra (ej. el Launcher se cierra).
                break
                
            line = line.strip()
            
            # Procesa JSON estructurado
            if line.startswith("IPC>>"):
                try:
                    data = json.loads(line[5:])
                    if data.get("type") == "command":
                        cmd_name = data.get("name")
                        
                        if cmd_name == "stop":
                            print(bot.lang.get("sys_ipc_stop"))
                            await bot.close()
                            break
                        
                        elif cmd_name == "reload":
                            print(bot.lang.get("sys_ipc_reload"))
                            load_dotenv(os.path.join(SETTINGS_DIR, ".env"), override=True)
                            asyncio.run_coroutine_threadsafe(bot.sync_modules(), bot.loop)
                        
                        elif cmd_name.startswith("music_"):
                            action = cmd_name.replace("music_", "")
                            arg = data.get("payload", {}).get("query", "")
                            
                            if not bot.voice_clients:
                                if action not in ["play", "next", "pls", "playlist", "eq"]:
                                    print(bot.lang.get("sys_ipc_mus_no_vc"))
                                    continue
                                if not bot.guilds:
                                    continue
                                guild_id = bot.guilds[0].id
                            else:
                                vc = bot.voice_clients[0]
                                guild_id = vc.guild.id
                            
                            music_cog = bot.get_cog("Music")
                            if not music_cog:
                                print(bot.lang.get("sys_ipc_mus_no_cog"))
                                continue
                            
                            print(bot.lang.get("sys_ipc_mus_invoke").format(action=action))
                            asyncio.run_coroutine_threadsafe(music_cog.ipc_invoke(guild_id, action, arg), bot.loop)
                except json.JSONDecodeError:
                    pass # Ignora líneas erróneas o ruido

        except RuntimeError:
            # Se lanza un RuntimeError si el bucle de eventos se cierra mientras `run_in_executor` espera.
            break

# --- BLOQUEO DE ZOMBIES ---
_instance_lock = None
def prevent_zombies():
    """Evita múltiples instancias del bot abriendo un puerto local."""
    global _instance_lock
    try:
        _instance_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _instance_lock.bind(("127.0.0.1", 47283))
        return True
    except socket.error:
        return False

# --- 4. PUNTO DE ENTRADA ---
async def main():
    """Función principal asíncrona que inicializa y ejecuta el bot."""
    # 👁️ INYECCIÓN DE SISTEMA RAW: Imprime todo el tráfico de red, HTTP y WebSockets sin censura.
    log_file = os.path.join(LOGS_DIR, "system.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

    bot = MeowSickBot()
    bot.send_ipc_progress(0.0, bot.lang.get("sys_ipc_prog_boot"))
    
    if not prevent_zombies():
        print(bot.lang.get("sys_zombie_warn"))
        return

    # Valida la existencia del token de Discord.
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print(bot.lang.get("sys_no_token"))
        return

    # Inicia el listener de IPC como una tarea en segundo plano.
    asyncio.create_task(console_listener(bot))

    try:
        # El bloque `async with bot:` gestiona el ciclo de vida del login y logout.
        # `bot.start()` inicia la conexión con Discord.
        async with bot:
            await bot.start(token)
    except KeyboardInterrupt:
        # Captura la interrupción del teclado (Ctrl+C) para un cierre limpio.
        await bot.close()
    except asyncio.CancelledError:
        # Silencia el error feo de apagado forzado desde el Launcher
        pass
    except Exception as e:
        print(bot.lang.get("sys_fatal_err").format(e=e))

if __name__ == "__main__":
    # Punto de entrada estándar para un script de Python.
    try:
        # Ejecuta la función principal `main` dentro del bucle de eventos de asyncio.
        asyncio.run(main())
    except KeyboardInterrupt:
        # Silencia el error de KeyboardInterrupt que se propaga al cerrar con Ctrl+C.
        pass
