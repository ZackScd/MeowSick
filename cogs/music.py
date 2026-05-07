import discord
from discord.ext import commands
from discord.ui import Button, View
import yt_dlp
import asyncio
import os
import json
import sys
import random
import math

try:
    import discord.ext.voice_recv as voice_recv
except ImportError:
    voice_recv = None
from shared.config_manager import ConfigManager

# --- 1. CONFIGURACIÓN DE ENTORNO Y RUTAS ---
# Determina el directorio base de ejecución, manejando la diferencia entre
# el entorno de desarrollo (script .py) y el entorno de producción (ejecutable compilado por PyInstaller).
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define las rutas absolutas a los recursos necesarios para el módulo.
SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
FFMPEG_DIR = os.path.join(BASE_DIR, "res", "ffmpeg", "ffmpeg.exe")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")

# --- 3. ESTRUCTURAS DE DATOS Y UI ---

class MusicQueue:
    """
    Estructura de datos personalizada para gestionar la cola de reproducción.
    Encapsula una lista estándar de Python proveyendo métodos específicos de control de flujo musical.
    """
    def __init__(self):
        self.queue = []     # Inicializa una lista vacía para almacenar las canciones pendientes.
        self.current = None # Variable para rastrear la canción que está sonando en este instante.


    def add(self, item):
        """Añade un ítem al final de la cola."""
        self.queue.append(item) # Añade el diccionario de la canción al final de la lista.

    def add_next(self, item):
        """Inserta un ítem al principio de la cola (índice 0), forzando su reproducción inmediata tras la pista actual."""
        self.queue.insert(0, item) # Coloca la canción en el índice 0, empujando las demás hacia atrás.

    def get_next(self):
        """Extrae y retorna el primer elemento de la cola, avanzando el flujo de reproducción."""
        if self.queue: # Verifica si hay elementos en la lista.
            return self.queue.pop(0) # Extrae y elimina el primer elemento, devolviéndolo para reproducirlo.
        return None # Retorna nulo si la cola está vacía.

    def clear(self):
        """Purga la cola y reinicia el estado de reproducción."""
        self.queue.clear() # Vacía la lista completa de canciones pendientes.
        self.current = None # Borra el registro de la canción actual.
    
    def shuffle(self):
        """Aleatoriza el orden de los elementos pendientes en la cola."""
        random.shuffle(self.queue) # Usa la librería random para desordenar la lista in-place.

class QueueView(View):
    """
    Interfaz de usuario interactiva basada en componentes (UI View) de Discord.
    Implementa paginación asíncrona para visualizar colas de reproducción extensas
    sin exceder el límite de caracteres de los mensajes (Embeds).
    """
    def __init__(self, ctx, queue, page_size, outputs, timeout=60):
        super().__init__(timeout=timeout) # Configura la vista para que expire tras el timeout.
        self.ctx = ctx # Guarda el contexto (canal, usuario) donde se envió el menú.
        self.queue = queue # Almacena la lista de canciones actual.
        self.page_size = page_size # Guarda cuántas canciones se mostrarán por cada página.
        self.current_page = 0 # Inicia siempre mostrando la página 0 (la primera).
        self.outputs = outputs # Guarda las traducciones/mensajes para personalizar el título.
        self.total_pages = math.ceil(len(queue) / page_size) # Calcula el total de páginas redondeando hacia arriba.
        self.update_buttons() # Ajusta el estado inicial de los botones (activos/inactivos).

    def update_buttons(self):
        """
        Evalúa el estado de la paginación y deshabilita los botones de navegación
        si el usuario se encuentra en los límites inferior o superior.
        """
        self.children[0].disabled = self.current_page == 0 # Apaga el botón 'Anterior' si estamos en la primera página.
        self.children[1].disabled = self.current_page >= self.total_pages - 1 # Apaga el botón 'Siguiente' si estamos en la última.

    def get_embed(self):
        """Genera dinámicamente un objeto discord.Embed representando el subconjunto de datos de la página actual."""
        start = self.current_page * self.page_size # Calcula el índice inicial para el corte de la lista.
        end = start + self.page_size # Calcula el límite final para el corte.
        page_items = self.queue[start:end] # Extrae solo el fragmento de la lista correspondiente a la página actual.
        
        desc = "" # Inicializa la cadena de texto para la descripción.
        
        for i, song in enumerate(page_items, start=start + 1): # Itera las canciones, enumerándolas correctamente.
            desc += f"`{i}.` **{song['title']}**\n" # Añade cada título al bloque de texto con formato Markdown.
        
        empty_text = self.outputs.get("list_empty", "Cola vacía.")
        embed = discord.Embed( # Crea el panel visual rico (Embed).
            title=self.outputs.get("list_title"), # Lee el título personalizado desde el archivo de configuración de salidas.
            description=desc or empty_text, # Muestra el texto compilado, o un aviso por defecto si no hay nada.
            color=0xbb9af7 # Define el color del borde izquierdo del panel (Morado/Violeta).
        )
        footer_text = self.outputs.get("list_footer", "Página {page}/{total} | Total: {len}").format(page=self.current_page + 1, total=self.total_pages, len=len(self.queue))
        embed.set_footer(text=footer_text) # Añade un pie de página con el rastreador de páginas.
        return embed # Devuelve el panel listo para enviarse.

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        """Callback del botón 'Anterior'. Disminuye el índice y refresca la vista interactiva."""
        self.current_page -= 1 # Retrocede el contador de página.
        self.update_buttons() # Actualiza los botones para bloquearlos si llegamos al principio.
        await interaction.response.edit_message(embed=self.get_embed(), view=self) # Edita el mensaje en Discord con los nuevos datos.

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        """Callback del botón 'Siguiente'. Aumenta el índice y refresca la vista interactiva."""
        self.current_page += 1 # Avanza el contador de página.
        self.update_buttons() # Actualiza los botones para bloquearlos si llegamos al final.
        await interaction.response.edit_message(embed=self.get_embed(), view=self) # Edita el mensaje en Discord con los nuevos datos.

# --- 4. MÓDULO (COG) PRINCIPAL ---

class Music(commands.Cog):
    """
    Implementa el conjunto de comandos y lógica de control del reproductor de audio.
    Gestiona estados independientes por cada servidor (Guild) utilizando diccionarios.
    """
    def __init__(self, bot):
        self.bot = bot # Guarda la referencia al cliente central del bot.
        self.queues = {} # Mapeo de diccionarios {ID del Servidor: Instancia de MusicQueue}
        self.disconnect_timers = {} # Mapeo de Tareas asíncronas de desconexión {ID del Servidor: asyncio.Task}
        self.config = self._load_json("config.json") or {} # Carga las variables de configuración genéricas.
        lang_code = self.config.get("language", "es")
        self.outputs = self._load_json(f"locales/outputs_{lang_code}.json") or {} # Carga las traducciones y respuestas.
        self.last_contexts = {} # Persistencia del último contexto de comando recibido, vital para comandos IPC desde el Launcher.

    async def cog_check(self, ctx):
        """Comprobación global para todos los comandos del módulo de Música."""
        # Excluye verificaciones si la llamada no proviene de un canal válido (e.g. contextos mock del IPC)
        if not getattr(ctx, "channel", None):
            return True
            
        music_channel_id = os.getenv("MUSIC_CHANNEL_ID")
        if music_channel_id and music_channel_id.strip().isdigit():
            expected_id = int(music_channel_id.strip())
            if ctx.channel.id != expected_id:
                try: await ctx.send(self.bot.lang.get("cmd_music_wrong_channel").format(channel_id=expected_id), delete_after=10)
                except: pass
                return False
        return True

    def get_ytdl_options(self):
        base = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': os.path.join(DOWNLOADS_DIR, '%(extractor)s-%(id)s-%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
        }
        music_cfg = self.config.get("music_config", {})
        base.update(music_cfg.get("ytdl_options", {}))
        return base

    def get_ffmpeg_options(self):
        base = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_on_network_error 1 -reconnect_on_http_error 4xx,5xx -reconnect_delay_max 15',
            'options': '-vn',
        }
        music_cfg = self.config.get("music_config", {})
        base.update(music_cfg.get("ffmpeg_options", {}))
        return base

    def _load_json(self, filename):
        """Utilidad interna para carga segura de archivos de configuración JSON."""
        path = os.path.join(SETTINGS_DIR, filename)
        use_lock = filename == "config.json" or "outputs_" in filename
        return ConfigManager.load_json(path, use_lock=use_lock)

    async def _send_msg(self, ctx, key, **kwargs):
        """
        Rutina de retroalimentación inteligente.
        Intercepta y resuelve claves contra 'outputs.json'. Si la clave no está definida
        o la cadena está intencionalmente vacía, silencia la salida de manera silenciosa.
        Soporta inyección de argumentos posicionales arbitrarios (kwargs) mediante str.format().
        """
        msg = self.outputs.get(key) # Busca el mensaje correspondiente a la llave en el JSON cargado.
        if msg: # Si el mensaje existe y no es una cadena vacía...
            await ctx.send(msg.format(**kwargs)) # Formatea el mensaje con las variables dadas e inyéctalo al chat.

    def get_queue(self, ctx):
        """Fábrica perezosa (Lazy instantiation) para garantizar la existencia de una cola por servidor."""
        if ctx.guild.id not in self.queues: # Si este servidor aún no tiene un objeto de cola asignado...
            self.queues[ctx.guild.id] = MusicQueue() # ...crea una instancia nueva y la asigna a la ID del servidor.
        return self.queues[ctx.guild.id] # Retorna la instancia de cola correspondiente.

    def send_ipc_update(self, guild_id):
        """
        Mecanismo de comunicación entre procesos (Inter-Process Communication).
        Serializa una porción de la cola activa y la transmite a través de la salida estándar (stdout)
        mediante un marcador reconocible (`IPC_QUEUE_UPDATE:`) para que el hilo de lectura del Launcher gráfico la capture y renderice.
        """
        if guild_id in self.queues: # Comprueba que realmente exista una cola para este servidor.
            titles = [s['title'] for s in self.queues[guild_id].queue[:50]] # Extrae un máximo de 50 títulos para evitar cuellos de botella al enviar datos al launcher.
            payload = {"type": "event", "name": "queue_update", "payload": titles}
            print(f"IPC>>{json.dumps(payload, ensure_ascii=False)}", flush=True) # Imprime con flush=True para evitar que los buffers se unan y rompan el JSON en el Launcher.

    async def ipc_invoke(self, guild_id, action, arg=""):
        """Invocador directo para comandos IPC desde el Launcher sin simular comandos de Discord."""
        ctx = self.last_contexts.get(guild_id)
        if not ctx:
            print(self.bot.lang.get("sys_ipc_mus_no_ctx").format(guild=guild_id))
            return
        
        commands_map = {
            "play": self.play.coro,
            "stop": self.stop.coro,
            "skip": self.skip.coro,
            "pause": self.pause.coro,
            "resume": self.resume.coro,
            "list": self.queue_list.coro,
            "shuffle": self.shuffle.coro,
            "leave": self.leave.coro,
            "next": self.next_song.coro,
            "pls": self.pls.coro
        }
        
        coro = commands_map.get(action)
        if coro:
            try:
                if action in ["play", "next"]: await coro(self, ctx, search=arg)
                else: await coro(self, ctx)
            except Exception as e: print(self.bot.lang.get("sys_ipc_mus_err").format(e=e))
        else:
            print(self.bot.lang.get("sys_ipc_mus_unknown").format(action=action))

    # --- 4.1. GESTIÓN DEL CICLO DE VIDA DE LA CONEXIÓN (TEMPORIZADORES) ---
    def cancel_timer(self, guild_id):
        """Revoca la tarea asíncrona de desconexión en espera si la actividad se reanuda."""
        if guild_id in self.disconnect_timers: # Chequea si hay un temporizador activo para el servidor.
            self.disconnect_timers[guild_id].cancel() # Cancela la corutina (impide que se ejecute la desconexión).
            del self.disconnect_timers[guild_id] # Borra el registro del temporizador del mapeo.

    def _schedule_disconnect(self, guild):
        """
        Inicia una corutina en segundo plano que evalúa el estado de inactividad
        tras un retardo predefinido, ejecutando la recolección de basura del VoiceClient si las condiciones se cumplen.
        """
        self.cancel_timer(guild.id) # Primero cancela cualquier temporizador anterior para evitar duplicados.
        
        async def timer_task():
            music_cfg = self.config.get("music_config", {})
            await asyncio.sleep(music_cfg.get("inactivity_sleep", 60)) # Suspende la ejecución según configuración.
            vc = guild.voice_client # Obtiene el estado actual del cliente de voz.
            if vc and vc.is_connected(): # Si el bot sigue conectado después de que pasó el minuto...
                # Evaluación de condiciones lógicas: Inactividad de flujo de audio o ausencia de clientes no-bot en el canal.
                no_playing = not vc.is_playing() and not vc.is_paused() # Cierto si está ocioso (ni tocando ni en pausa).
                no_humans = len([m for m in vc.channel.members if not m.bot]) == 0 # Cuenta miembros en el canal. Cierto si solo hay bots.

                if no_playing or no_humans: # Si se cumple CUALQUIERA de las condiciones de abandono...
                    await vc.disconnect() # Desconecta el bot del canal de voz de Discord.
                    print(self.bot.lang.get("sys_mus_auto_dc").format(guild=guild.name)) # Registra la acción en consola.
                    
                    ctx = self.last_contexts.get(guild.id) # Intenta recuperar dónde fue la última interacción de texto.
                    if ctx: await self._send_msg(ctx, "timeout_msg") # Envía el aviso de desconexión al chat de texto.

            if guild.id in self.disconnect_timers: # Limpieza final de la estructura de datos.
                del self.disconnect_timers[guild.id] # Borra el rastro de la tarea ejecutada.
        
        # Adjunta la tarea al loop de eventos principal
        self.disconnect_timers[guild.id] = self.bot.loop.create_task(timer_task()) # Lanza el temporizador asíncrono sin bloquear el bot.

    def start_timer(self, ctx):
        """Wrapper público para invocar la programación de desconexión mediante el contexto actual."""
        self._schedule_disconnect(ctx.guild)

    # --- 4.2. MOTOR DE REPRODUCCIÓN ---
    async def connect_to_voice(self, ctx):
        """
        Resuelve el enrutamiento del VoiceClient hacia el canal del autor del comando.
        Realiza transferencias automáticas ('move_to') si el bot se encuentra en un canal distinto dentro del mismo servidor.
        """
        if not ctx.author.voice: # Valida que el usuario que mandó el mensaje esté metido en un canal de voz.
            await self._send_msg(ctx, "connect_voice") # Advierte al usuario sobre el requerimiento.
            return False # Fracaso temprano.
        
        vc = ctx.voice_client # Extrae el enlace de voz actual del bot.
        try:
            if vc: # Si el bot ya está ocupando un canal en el servidor...
                if vc.channel.id != ctx.author.voice.channel.id: # ...y no es el mismo canal en el que estás tú...
                    await vc.move_to(ctx.author.voice.channel) # ...pídele al bot que se teletransporte a tu canal.
            else: # Si el bot está totalmente desconectado del servidor de voz...
                if voice_recv:
                    await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
                else:
                    await ctx.author.voice.channel.connect()
            return True # Conexión establecida.
        except Exception as e:
            print(self.bot.lang.get("sys_mus_err_vc").format(e=e)) # Log del error crudo.
            await self._send_msg(ctx, "connect_error", error=e) # Aviso formal al usuario.
            return False # Fracaso al intentar conectar.

    async def play_next(self, ctx):
        """
        Bucle de eventos recursivo secundario.
        Desencola el siguiente ítem, invoca al extractor (yt-dlp) para resolver la URL en tiempo real
        y delega el flujo de bits a la instancia de discord.FFmpegPCMAudio.
        """
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            # Fix: intenta reconectar si el VoiceClient cayó por lag pero el usuario sigue en el canal
            try:
                if ctx.author and ctx.author.voice and ctx.author.voice.channel:
                    print(self.bot.lang.get("sys_mus_vc_dc_reconn"))
                    if voice_recv:
                        await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
                    else:
                        await ctx.author.voice.channel.connect()
                    print(self.bot.lang.get("sys_mus_reconn_ok"))
                else:
                    return  # No hay canal al que volver, detener cola limpiamente
            except Exception as e:
                print(self.bot.lang.get("sys_mus_reconn_fail").format(e=e))
                return

        queue = self.get_queue(ctx)
        
        if not queue.queue:
            queue.current = None
            await self._send_msg(ctx, "queue_finished")
            self.start_timer(ctx)
            self.send_ipc_update(ctx.guild.id)
            return

        self.cancel_timer(ctx.guild.id)
        song = queue.get_next()
        queue.current = song
        self.send_ipc_update(ctx.guild.id)

        # Fix: reintentos con backoff exponencial para tolerar tokens expirados o lag de red
        music_cfg = self.config.get("music_config", {})
        max_retries = music_cfg.get("max_retries", 3)
        last_error = None
        data = None

        for attempt in range(max_retries):
            try:
                loop = self.bot.loop
                if attempt > 0:
                    wait_time = 2 ** attempt  # 2s, 4s
                    print(self.bot.lang.get("sys_mus_retry").format(attempt=attempt, max_retries=max_retries-1, title=song['title'], wait=wait_time))
                    await asyncio.sleep(wait_time)

                data = await loop.run_in_executor(
                    None,
                    lambda: yt_dlp.YoutubeDL(self.get_ytdl_options()).extract_info(song['webpage_url'], download=False)
                )
                last_error = None
                break  # Éxito, salir del bucle de reintentos
            except Exception as e:
                last_error = e
                print(self.bot.lang.get("sys_mus_extract_err").format(attempt=attempt+1, max_retries=max_retries, title=song['title'], e_type=type(e).__name__, e_msg=str(e)[:80]))

        if last_error or not data:
            print(self.bot.lang.get("sys_mus_all_retries_fail").format(title=song['title']))
            await self._send_msg(ctx, "play_error_skip")
            # Fix: usar after(0) en lugar de recursión directa para no apilar coroutines en el call stack
            await asyncio.sleep(0.5)
            await self.play_next(ctx)
            return

        try:
            if 'entries' in data:
                data = data['entries'][0]
            source_url = data['url']
            title = data.get('title', song['title'])
            
            if not os.path.exists(FFMPEG_DIR):
                print(self.bot.lang.get("sys_mus_no_ffmpeg").format(path=FFMPEG_DIR))
                await self._send_msg(ctx, "ffmpeg_error")
                return

            source = discord.FFmpegPCMAudio(source_url, **self.get_ffmpeg_options(), executable=FFMPEG_DIR)
            
            def after_play(error):
                if error:
                    print(self.bot.lang.get("sys_mus_play_err").format(title=title, error=error))
                # Fix: siempre encolar el siguiente, incluso si hubo error de stream
                # run_coroutine_threadsafe es thread-safe desde el callback síncrono de discord.py
                fut = asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                # Capturar excepciones del future para que no queden silenciosas
                def _handle_fut(f):
                    try: f.result()
                    except Exception as e: print(self.bot.lang.get("sys_mus_after_play_err").format(e=e))
                fut.add_done_callback(_handle_fut)

            # Fix: verificar que el VoiceClient siga conectado justo antes de play()
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                print(self.bot.lang.get("sys_mus_vc_lost_play"))
                queue.add_next(song)  # Devuelve la canción al frente de la cola
                await asyncio.sleep(1.0)
                await self.play_next(ctx)
                return

            ctx.voice_client.play(source, after=after_play)
            await self._send_msg(ctx, "playing_now", title=title)
            print(self.bot.lang.get("sys_mus_playing_log").format(title=title))
            payload = {"type": "event", "name": "now_playing", "payload": {"title": title}}
            print(f"IPC>>{json.dumps(payload, ensure_ascii=False)}", flush=True)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(self.bot.lang.get("sys_mus_play_exc").format(title=song['title'], e_type=type(e).__name__, e_msg=str(e)))
            await self._send_msg(ctx, "play_error_skip")
            await asyncio.sleep(0.5)
            await self.play_next(ctx)

    # --- 4.3. RUTAS DE COMANDOS PÚBLICOS ---

    @commands.command(name="play")
    async def play(self, ctx, *, search: str = None):
        """Busca y reproduce una canción o lista desde YouTube."""
        self.last_contexts[ctx.guild.id] = ctx # Captura y guarda la instancia del canal de texto usado por última vez (Útil para comandos forzados desde el Launcher externo).
        if not await self.connect_to_voice(ctx): return # Inicia maniobra de conexión. Frena todo si es imposible entrar al canal de voz.
        if not search: # Verifica que el usuario realmente haya escrito qué quiere buscar.
            await self._send_msg(ctx, "play_no_args") # Dispara mensaje de reprimenda por parámetros insuficientes.
            return # Frena el comando.

        async with ctx.typing(): # Pone al bot en estado de "escribiendo..." mientras procesa la búsqueda para dar feedback visual.
            try:
                loop = self.bot.loop # Consigue el puntero al loop de tareas principal de Python.
                print(self.bot.lang.get("sys_mus_search_log").format(search=search)) # Registro crudo de solicitud.
                
                # Lógica condicional: Desvío algorítmico para acelerar la extracción de listas de reproducción omitiendo la resolución profunda inicial.
                if "list=" in search and not search.startswith("ytsearch"):
                    fast_opts = {**self.get_ytdl_options(), 'extract_flat': 'in_playlist'} # Forzamos a yt-dlp a modo superficial (ignorar extraer data técnica en masa).
                    info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(fast_opts).extract_info(search, download=False)) # Extrae solo la capa superior de la playlist sin descargar.
                else:
                    ytdl_opts = self.get_ytdl_options()
                    info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ytdl_opts).extract_info(search, download=False)) # Ejecuta búsqueda normal en hilo secundario.
                
                queue = self.get_queue(ctx) # Invoca al administrador de cola del servidor correspondiente.
                added_song = None # Variable auxiliar para rastrear lo que pusimos.

                # Resolución de la estructura del resultado (Singular vs Múltiple)
                if 'entries' in info:
                    if search.startswith("ytsearch"):
                        # Es el resultado de una búsqueda por texto ('ytsearch'); aislamos el primer candidato.
                        entry = info['entries'][0] # Toma únicamente el video Top 1 de la respuesta de búsqueda de YouTube.
                        added_song = {'title': entry['title'], 'webpage_url': entry['webpage_url']} # Estructura un diccionario mini con lo vital.
                        queue.add(added_song) # Lo empuja dentro de la cola.
                    else:
                        # Es un objeto Iterable correspondiente a una Playlist; iteramos y anexamos de forma enlazada.
                        count = 0 # Inicia un contador de canciones logradas procesar.
                        for entry in info['entries']: # Repasa cada video crudo de la playlist extraída.
                            if entry: # Si el registro no está vacío o en formato erróneo.
                                web_url = entry.get('webpage_url') or entry.get('url') # Intenta pescar la URL.
                                if web_url and not web_url.startswith("http"): # Arregla links de modo 'flat' que a veces devuelven solo el ID numérico.
                                    web_url = f"https://www.youtube.com/watch?v={entry.get('id') or web_url}" # Parchea reconstruyendo la base de YouTube.
                                
                                queue.add({'title': entry.get('title', 'Track'), 'webpage_url': web_url}) # Construye registro seguro y empuja al arreglo.
                                count += 1 # Sube el contador.
                        await self._send_msg(ctx, "playlist_added", count=count) # Retroalimentación de inserción múltiple en masa.
                else:
                    # Extracción directa de URL singular
                    added_song = {'title': info['title'], 'webpage_url': info['webpage_url']} # Genera registro único estándar.
                    queue.add(added_song) # Empuja en modo FIFO.

                self.send_ipc_update(ctx.guild.id) # Trasmite ráfaga IPC al Launcher para actualizar su gráfico en tiempo real.

                # Gatillo de auto-arranque: Inicia el bucle si estaba ocioso.
                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused(): # Diagnóstico del reproductor: ¿Hay algo sonando o estamos en completo silencio?
                    await self.play_next(ctx) # Como estamos libres, jalamos e iniciamos el reproductor forzosamente ahora mismo.
                elif added_song: # Si ya había algo tocando de antes, simplemente damos retroalimentación al usuario.
                    await self._send_msg(ctx, "added_queue", title=added_song['title']) # Aviso "X fue añadido a la cola".

            except Exception as e:
                print(self.bot.lang.get("sys_mus_play_cmd_err").format(e=e)) # Desplome del motor extractor.
                await self._send_msg(ctx, "search_error") # Aviso "Error de búsqueda" genérico.

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Detiene la música y vacía la cola por completo."""
        self.last_contexts[ctx.guild.id] = ctx # Refresca origen en la caché de control.
        if ctx.voice_client: # Comprueba que haya un vínculo de voz activo sobre el cual operar.
            self.get_queue(ctx).clear() # Realiza una purga agresiva de toda la memoria estructural del reproductor en este servidor.
            self.send_ipc_update(ctx.guild.id) # Envía actualización al exterior (launcher) indicando que la cola colapsó a cero.
            await ctx.voice_client.disconnect() # Cancela violentamente el stream de audio TCP hacia Discord y sale del canal.
            await self._send_msg(ctx, "stop_msg") # Se despide.

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Salta la canción actual y pasa a la siguiente."""
        self.last_contexts[ctx.guild.id] = ctx # Refresca caché.
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()): # Condición de salto: Solo se puede omitir si el motor está renderizando audio activo o suspendido.
            ctx.voice_client.stop() # Mata el flujo de renderizado instantáneamente. Esto ES clave: al invocar stop(), la librería internamente dispara por detrás el callback `after_play`, por lo que el `play_next` se mandará a ejecutar sin que hagamos nada más.
            await self._send_msg(ctx, "skip_msg") # Confirma salto al chat.
        else: # Si el bot estaba callado y el usuario intenta saltar la nada.
            await self._send_msg(ctx, "nothing_playing") # Feedback sarcástico o nulo según el archivo json.

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pausa la reproducción actual."""
        self.last_contexts[ctx.guild.id] = ctx # Actualiza el puntero de contexto.
        if ctx.voice_client and ctx.voice_client.is_playing(): # Exige que el reproductor no solo exista, sino que fluya bits activamente.
            ctx.voice_client.pause() # Suspende la transferencia UDP del paquete PCM sin destruir el búfer.
            await self._send_msg(ctx, "paused") # Aviso de que está congelado.

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Reanuda la reproducción pausada."""
        self.last_contexts[ctx.guild.id] = ctx # Retiene contexto en la variable de clase.
        if ctx.voice_client and ctx.voice_client.is_paused(): # Exige que haya una instancia colgada en estado de pausa real.
            ctx.voice_client.resume() # Retoma el stream de red en el byte exacto donde se paralizó.
            await self._send_msg(ctx, "resumed") # Confirmación visual.

    @commands.command(name="list")
    async def queue_list(self, ctx):
        """Muestra la lista de canciones en la cola."""
        self.last_contexts[ctx.guild.id] = ctx # Refresco de contexto para el IPC backend.
        queue = self.get_queue(ctx) # Absorbe el objeto MusicQueue ligado a este grupo.
        if not queue.queue: # Análisis primario: ¿Tenemos arreglos repletos o vacíos?
            await self._send_msg(ctx, "list_empty") # Deriva hacia el rechazo por vacuidad.
            return # Cierre temprano.
        
        limit = self.config.get("queue_page_limit", 10) # Investiga cuántas páginas configurar leyendo el JSON global. Si no hay, usa 10 como medida predeterminada sensata.
        music_cfg = self.config.get("music_config", {})
        view_timeout = music_cfg.get("view_timeout", 60)
        view = QueueView(ctx, queue.queue, limit, self.outputs, timeout=view_timeout) # Instancia una vista UI enlazando la pila de datos con los componentes visuales de Discord.
        await ctx.send(embed=view.get_embed(), view=view) # Engancha el Embed inicial extraído de la instancia y anexa el administrador de eventos `view` al mensaje.

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        """Mezcla aleatoriamente las canciones de la cola."""
        self.last_contexts[ctx.guild.id] = ctx # Reemplaza el contexto en espera.
        queue = self.get_queue(ctx) # Busca los datos locales de enrutamiento musical.
        if queue.queue: # Comprueba que al menos posea un ítem extra más allá de lo que suena.
            queue.shuffle() # Interrumpe el orden dictado empleando la lógica encapsulada de MusicQueue.
            self.send_ipc_update(ctx.guild.id) # Escupe el nuevo desorden para que el visualizador de la ventana central de PC se entere.
            await self._send_msg(ctx, "shuffled") # Devuelve el estado feliz.
        else: # Intento de invocar el comando en vacío.
            await self._send_msg(ctx, "shuffle_error") # Imprime burla o error respectivo.

    @commands.command(name="leave")
    async def leave(self, ctx):
        """Desconecta al bot del canal de voz."""
        self.last_contexts[ctx.guild.id] = ctx # Caché.
        if ctx.voice_client: # Valida que haya un socket real conectado.
            self.get_queue(ctx).clear() # Pulveriza la lista como lo hace stop.
            self.send_ipc_update(ctx.guild.id) # Destruye registros visuales.
            await ctx.voice_client.disconnect() # Emite la orden a la API de salirse.
            await self._send_msg(ctx, "disconnected") # Despedida final.
        else: # Si el bot no tiene canal de voz...
            await self._send_msg(ctx, "not_connected") # Indica que está demente y ya está desconectado.

    @commands.command(name="next")
    async def next_song(self, ctx, *, search: str = None):
        """Añade una canción para que suene justo después de la actual."""
        self.last_contexts[ctx.guild.id] = ctx # Ajuste en sistema IPC auxiliar.
        if not await self.connect_to_voice(ctx): return # Pide paso y se cuelga en el canal de usuario si procede. Termina aquí en negativo si fracasa.
        if not search: # Demanda que envíen cadena de texto.
            await self._send_msg(ctx, "play_no_args") # Discute la ausencia de petición.
            return # Vaciado y escape.

        async with ctx.typing(): # Interfaz "..." interactiva.
            try:
                loop = self.bot.loop # Intercepta el bucle de eventos nativo de Python para uso en hilos paralelos.
                print(self.bot.lang.get("sys_mus_search_next_log").format(search=search)) # Inyección simple en consola local para debug visual en PC.
                
                ytdl_opts = self.get_ytdl_options()
                info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ytdl_opts).extract_info(search, download=False)) # Manda al motor de extracción profunda el texto asíncronamente en bloque de hilo ciego.
                if 'entries' in info: info = info['entries'][0] # Traga el primer índice caso sea listado o ytsearch nativo por debajo del capó.

                added_song = {'title': info['title'], 'webpage_url': info['webpage_url']} # Comprime de manera simple título limpio y url web (No el directo streaming, sino el de YouTube).
                queue = self.get_queue(ctx) # Invoca o fabrica la fila perteneciente a esta id de Discord Server.
                queue.add_next(added_song) # Enchufa brutalmente en el index[0], posponiendo las que ya estuvieran enlistadas para después.

                self.send_ipc_update(ctx.guild.id) # Altera forzadamente la lectura en el front del launcher si este está mirando.

                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused(): # Estudia el silencio absoluto...
                    await self.play_next(ctx) # ¡Estaba inactivo! Rompe el ocio de inmediato para tocar el índice inyectado.
                else: # Estaba ya tocando una canción de manera activa normal...
                    await self._send_msg(ctx, "next_added", title=added_song['title']) # Brinda confirmación de inyección agresiva exitosa para calmar la inquietud.

            except Exception as e:
                print(self.bot.lang.get("sys_mus_next_cmd_err").format(e=e)) # Log puro y duro del error para ver qué colapsó en yt-dlp.
                await self._send_msg(ctx, "search_error") # Transmite en canal final el descontento de extracción.

    @commands.command(name="playlist")
    async def playlist(self, ctx):
        """Carga y reproduce tu lista de canciones predeterminada."""
        self.last_contexts[ctx.guild.id] = ctx # Persiste ruta por enésima vez.
        url = os.getenv("PLAYLIST_URL") # Chupa directamente del archivo base .env la URL configurada estáticamente.
        if not url: # Chequea si el usuario está tonto y configuró de forma vacía las variables o nunca tocó el launcher interno.
            await self._send_msg(ctx, "playlist_no_config") # Lo recrimina.
            return # Para y huye.
        
        # Reutilizamos el comando play pasando la URL
        await self.play(ctx, search=url) # Engaña al bot invocando el comando general play internamente sin que el humano escribiera nada más, reusando código robustamente.

    @commands.command(name="pls")
    async def pls(self, ctx):
        """Carga tu lista predeterminada y la reproduce en orden aleatorio."""
        self.last_contexts[ctx.guild.id] = ctx # Anota caché.
        url = os.getenv("PLAYLIST_URL") # Indaga URL ambiental.
        if not url: # Examina que exista.
            await self._send_msg(ctx, "playlist_no_config") # Reporta fallo de usuario en panel central.
            return # Cancela función.

        if not await self.connect_to_voice(ctx): return # Requisito forzado de voz, entra si puede. Regresa si no.

        async with ctx.typing(): # Apariencia de pensar...
            try:
                loop = self.bot.loop # Intercepta el bucle local para meter las garras con el extractor.
                print(self.bot.lang.get("sys_mus_search_pls_log").format(url=url)) # Log inofensivo.
                
                # Directiva extract_flat: Optimización crítica para análisis superficial. Obtiene diccionarios minimalistas en vez de resolver datos de codificación masivos.
                fast_opts = {**self.get_ytdl_options(), 'extract_flat': 'in_playlist'} # Manda la navaja rápida en yt-dlp. Saca nombres e ids pero ignora la URL real M3U8 para no colapsar la RAM de inmediato.
                
                info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(fast_opts).extract_info(url, download=False)) # Manda al pozo sin fondo el cálculo.
                
                entries = list(info.get('entries', [])) # Castea todos los diccionarios rasos crudos a formato lista limpia iterable.
                random.shuffle(entries) # Modifica la lista local puramente y mezcla su integridad in-place en la RAM base.
                
                queue = self.get_queue(ctx) # Retorna cola real de música pertinente al server actual y vivo.
                count = 0 # Inicializa monitor conteo.
                for entry in entries: # Bucles con el array de canciones ya mezcladas localmente antes de indexarlas al final.
                    if entry: # Salvaguarda contra items nulos de YouTube si hay videos privados en la playlist.
                        # En modo flat, 'url' suele ser solo el ID. Construimos el link completo si falta.
                        web_url = entry.get('url') # Rasca el pedazo de id provisto por flat extraction.
                        if web_url and not web_url.startswith("http"): # Corrobora si es un link limpio o ID cortado huérfano "dsH4ds21s".
                            web_url = f"https://www.youtube.com/watch?v={web_url}" # Forma link funcional que el motor profundo pueda tragar.
                        
                        queue.add({'title': entry.get('title', 'Track'), 'webpage_url': web_url or entry.get('webpage_url')}) # Inserta en crudo.
                        count += 1 # Aumenta métrica iterativa.

                self.send_ipc_update(ctx.guild.id) # Expone actualización de índice local IPC.
                await self._send_msg(ctx, "playlist_added", count=count) # Brinda el número total metido al chat para orgullo humano.
                await self._send_msg(ctx, "shuffled") # Aclara que no va a seguir el mismo patrón aburrido gracias a su naturaleza pls aleatoria.

                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused(): # Chequeo profundo de inactividad de instancia.
                    await self.play_next(ctx) # Como el estado del motor era ocioso, lo rompe mandándolo a extraer el índice cero recién forzado.
            except Exception as e:
                print(self.bot.lang.get("sys_mus_pls_cmd_err").format(e=e)) # Documentación local crasheo profundo.
                await self._send_msg(ctx, "search_error") # Informe formal al gremio discord.

    # --- 4.4. OBSERVADORES DE EVENTOS DE SESIÓN (LISTENERS) ---

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Evento reactivo activado por Discord API tras el mutuo cambio de canal, mute, deafen, etc de cualquier usuario.
        Diseñado para monitorear la ocupación humana relativa a la sesión de voz del bot.
        """
        bot_user = self.bot.user # Extrae la instancia nativa que el programa tiene de sí mismo (MeowSick).
        if member == bot_user: return # Ignorar cambios del propio bot (como cuando él mismo entra o es movido).

        vc = member.guild.voice_client # Extrae el enlace actual que tiene el bot de ese mismo servidor específico.
        if not vc: return # Si el bot no está ni conectado en voz, ignora la charla y el movimiento ajeno en los canales.

        # Si el usuario salió del canal donde está el bot
        if before.channel and before.channel.id == vc.channel.id: # Comprueba que el usuario que generó la alerta antes SÍ compartía piso con el bot en el voice channel.
            human_count = sum(1 for m in vc.channel.members if not m.bot) # Emite un barrido iterativo evaluando quién de los restantes no tiene tag de BOT.
            
            if human_count == 0: # ¿Resultó en un número nulo de organismos reales vivos dentro?
                print(self.bot.lang.get("sys_mus_bot_alone").format(guild=member.guild.name)) # Anuncia su soledad existencial en consola de manera formal.
                self._schedule_disconnect(member.guild) # Dispara en segundo plano y asíncronamente el contador destructivo del bot mediante `create_task`.
        
        # Interrupción del disparador: Entrada de humano a canal del VoiceClient
        if after.channel and after.channel.id == vc.channel.id: # ¿Alguien acaba de reconectarse O moverse al mismo hueco exacto que ocupa el bot en red?
            if not member.bot: # ¿Es un humano?
                self.cancel_timer(member.guild.id) # ¡Excelente! Mata el temporizador, el bot ya no es abandonado a su suerte y seguirá ahí pasivo o cantando feliz.

# Registro del módulo en la pila asíncrona de discord.py
async def setup(bot):
    await bot.add_cog(Music(bot)) # Inyecta de forma masiva en el ecosistema superior toda la caja negra de la clase Music.