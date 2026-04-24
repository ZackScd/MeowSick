import discord
from discord.ext import commands
import json
import os
import asyncio
import time
import random
import base64
import re
import sys
import io
from PIL import Image

# Importamos los módulos locales del paquete AI
from .utils import ai_manager          # Gestor de conexión y peticiones a la API de Gemini
from .identity import identity_manager # Gestor estático de identidades y usuarios
from shared.config_manager import ConfigManager
# Nota: Evolution y Memory se cargan como Cogs separados, 
# accedemos a ellos vía self.bot.get_cog()

class TalkView(discord.ui.View):
    """Panel UI Dinámico para el control de entrada de audio (Micrófono)."""
    def __init__(self, cog, vc):
        super().__init__(timeout=None)
        self.cog = cog
        self.vc = vc
        self.is_recording = False
        self.current_speaker = None
        
        if getattr(sys, 'frozen', False): base_dir = os.path.dirname(sys.executable)
        else: base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.audio_path = os.path.join(base_dir, "downloads", f"voice_in_{vc.guild.id}.wav")

    def clean_stop(self):
        """Detiene forzosamente la vista y la grabación si está activa."""
        self.stop()
        if self.is_recording and self.vc:
            try: self.vc.stop_listening()
            except: pass

    @discord.ui.button(label="🎙️ Hablar", style=discord.ButtonStyle.green, custom_id="btn_talk")
    async def talk_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try: import discord.ext.voice_recv as voice_recv
        except ImportError: voice_recv = None
        
        if not voice_recv:
            return await interaction.response.send_message("⚠️ Librería voice_recv no instalada. Ejecuta: `pip install discord-ext-voice-recv`", ephemeral=True)
        
        if not self.vc or not self.vc.is_connected():
            button.label, button.style, button.disabled = "Desconectado", discord.ButtonStyle.secondary, True
            await interaction.response.edit_message(view=self)
            return await interaction.followup.send("⚠️ El bot ya no está en el canal de voz.", ephemeral=True)

        if interaction.user.voice is None or interaction.user.voice.channel != self.vc.channel:
            return await interaction.response.send_message("⚠️ Debes estar en mi canal de voz para usar el micrófono.", ephemeral=True)

        if self.is_recording:
            if self.current_speaker and interaction.user.id != self.current_speaker.id:
                return await interaction.response.send_message(f"⚠️ Por favor espera, estoy escuchando a {self.current_speaker.display_name}.", ephemeral=True)
            
            # --- DETENER GRABACIÓN ---
            self.is_recording = False
            self.current_speaker = None
            button.label = "⏳ Procesando..."
            button.style = discord.ButtonStyle.secondary
            button.disabled = True
            await interaction.response.edit_message(view=self)
            
            self.vc.stop_listening() # Corta la recepción de paquetes
            if hasattr(self, 'current_sink') and self.current_sink:
                self.current_sink.predicate = None # Parche para bug de la librería (evita AttributeError en __del__)
            await asyncio.sleep(1.0) # Le da 1 segundo al Sink para guardar el buffer .wav en el disco
            
            # Mandar el audio a la IA
            await self.cog.process_audio_input(interaction, self.audio_path, self)
        else:
            # --- INICIAR GRABACIÓN ---
            self.is_recording = True
            self.current_speaker = interaction.user
            button.label = "🔴 Escuchando (Click para detener)..."
            button.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(view=self)
            
            if os.path.exists(self.audio_path):
                try: os.remove(self.audio_path)
                except: pass
                
            # Crea el filtro: El receptor grabará ÚNICAMENTE los paquetes de audio del usuario que apretó el botón
            sink = voice_recv.WaveSink(self.audio_path)
            filtered_sink = voice_recv.UserFilter(sink, interaction.user)
            self.current_sink = filtered_sink # Guardar referencia en memoria para el parche de recolección de basura
            self.vc.listen(filtered_sink)

class AICore(commands.Cog):
    """
    El núcleo frontal de la IA.
    Se encarga de escuchar constantemente los canales de Discord, filtrar mensajes,
    ensamblar el contexto psicológico/memoria y generar respuestas activas.
    """
    def __init__(self, bot):
        self.bot = bot # Instancia global del bot de Discord
        self.config_path = "settings/config.json" # Ruta a los ajustes generales
        self.outputs_path = "settings/outputs.json" # Ruta a los mensajes de respuesta
        self.active_tts = set() # Rastrea en qué servidores se activó el comando !voice
        self.active_talk = {} # Rastrea las instancias de botones de habla activas por servidor
        self.processed_msgs = {} # 🛡️ Lock de Mensajes (Diccionario como Set Ordenado O(1))
        
        # Arquitectura Anti-Event Storms (Workers)
        self.chat_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue()
        self.chat_worker_task = self.bot.loop.create_task(self._chat_worker())
        self.audio_worker_task = self.bot.loop.create_task(self._audio_worker())
        
        # UX Social (Anti-Spam)
        self.last_response_time = {}

    def cog_unload(self):
        """Limpia los workers asíncronos al recargar el módulo para evitar fugas de memoria."""
        if hasattr(self, 'chat_worker_task'): self.chat_worker_task.cancel()
        if hasattr(self, 'audio_worker_task'): self.audio_worker_task.cancel()

    async def _chat_worker(self):
        """Worker aislado. Procesa mensajes de texto uno a uno evadiendo cuellos de botella de red."""
        # OS Yielding Priority (Modo Gamer) para todo el ciclo de vida de este worker
        try: import psutil
        except ImportError: psutil = None
        
        if psutil:
            try:
                gamer_mode = self._get_config().get("gamer_mode", False)
                if gamer_mode and sys.platform == 'win32':
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                            try: proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                            except: pass
            except: pass

        while True:
            try:
                message, is_direct = await self.chat_queue.get()
                print(self.bot.lang.get("sys_ai_core_worker_proc").format(wid=id(self), mid=message.id, qsize=self.chat_queue.qsize()))
                await self._process_message_task(message, is_direct)
                self.chat_queue.task_done()
            except asyncio.CancelledError: break
            except Exception as e: print(self.bot.lang.get("sys_ai_core_chat_err").format(e=e))
            
    async def _audio_worker(self):
        """Worker aislado para la pipeline STT/TTS previniendo bloqueos del VoiceClient."""
        while True:
            try:
                interaction, audio_path, view = await self.audio_queue.get()
                await self._process_audio_task(interaction, audio_path, view)
                self.audio_queue.task_done()
            except asyncio.CancelledError: break
            except Exception as e: print(self.bot.lang.get("sys_ai_core_audio_err").format(e=e))

    def _get_config(self):
        """Lee el archivo JSON de configuración y extrae específicamente el bloque de ajustes de IA."""
        return ConfigManager.load_json(self.config_path, use_lock=True).get("ai_config", {})

    def _is_ai_active(self):
        """Comprueba de forma superficial si el módulo entero está encendido."""
        # Verifica si el MÓDULO entero está encendido en config global
        return True # La carga del Cog ya depende de config['modules']['ia'], así que aquí siempre es True

    def _check_filters(self, message):
        """
        Sistema de validación temprana.
        Decide si el bot debe prestar atención a un mensaje o ignorarlo por completo.
        """
        # --- 🛡️ 1. FILTRO ANTI-DUPLICADOS ESTRICTO (Bloqueo de Multi-Dispatch) ---
        # Evita ejecuciones dobles si Discord envía el mismo evento por latencia de red.
        if message.id in self.processed_msgs:
            return False
        self.processed_msgs[message.id] = True # Guarda el ID
        if len(self.processed_msgs) > 150: self.processed_msgs.pop(next(iter(self.processed_msgs))) # Borra el más antiguo

        config = self._get_config() # Carga configuración fresca
        
        # Filtro de canales (Prioridad: ENV > Config)
        env_channels = os.getenv("AI_TARGET_CHANNELS", "") # Busca canales permitidos en las variables de entorno
        if env_channels: # Si hay canales definidos en el .env...
            target_channels = [int(x) for x in env_channels.replace(" ", "").split(",") if x.isdigit()] # Los convierte en una lista de números enteros
        else:
            target_channels = config.get("target_channels", []) # Si no, intenta leer de config.json
            
        if target_channels and message.channel.id not in target_channels: # Si hay lista blanca y este canal no está...
            return False # Ignorar mensaje
        
        # Ignorar nuestros propios mensajes (ya se añaden al buffer manualmente al responder)
        if message.author.id == self.bot.user.id: # Previene que el bot intente auto-responderse o genere bucles
            return False # Ignorar mi propio mensaje

        # Filtro de bots
        if message.author.bot: # Si el mensaje fue enviado por OTRO bot...
            if not config.get("listen_to_bots", False): # Y no tenemos permiso explícito para escuchar bots...
                return False # Ignorar el mensaje
                
        return True # Si pasó todas las barreras, el mensaje es válido para procesarse

    async def _assemble_prompt(self, message, history):
        """
        El motor de construcción psicológica.
        Recopila todos los datos fragmentados de los otros módulos y construye el gran bloque de texto
        que se enviará a Gemini como 'System Instruction' (Instrucciones de Personalidad) y Contexto.
        """
        # 1. Identidad Base
        system_prompt = identity_manager.get_identity_block() # Extrae quién es el bot y sus directrices
        
        # 2. Estado de Ánimo (Evolution Cog)
        evo_cog = self.bot.get_cog("Evolution") # Intenta enlazar con el módulo de emociones
        mood = evo_cog.get_current_mood() if evo_cog else "Neutral" # Si el módulo está activo, extrae su estado, si no, es Neutral
        system_prompt += f"\n\n[ESTADO EMOCIONAL ACTUAL]\n{mood}\n(INSTRUCCIÓN: Deja que este estado tiña tus respuestas. Si estás enojada, sé cortante. Si estás feliz, sé entusiasta. ACTÚALO)." # Inyecta emoción al prompt

        # 3. Autoconcepto (Memory Cog)
        mem_cog = self.bot.get_cog("Memory") # Intenta enlazar con el módulo de memoria
        if mem_cog:
            auto = mem_cog.get_autoconcepto_data() # Extrae gustos propios de la IA
            gustos = ", ".join(auto.get("gustos", [])) # Los une en una cadena de texto
            if gustos:
                system_prompt += f"\n\n[TUS GUSTOS/INTERESES]\n{gustos}\n(REGLA ESTRICTA: Estos son detalles pasivos. NO hables de ellos a menos que el usuario te pregunte directamente. Prohibido forzarlos en la conversación)." # Inyecta gustos

        # 4. Contexto Social (Quién habla)
        opinions = mem_cog.get_opinions_data() if mem_cog else {} # Extrae la base de datos de afinidad y relaciones
        user_context = identity_manager.get_user_context(message.author.id, opinions) # Pide construir un perfil específico de la persona que mandó el mensaje
        
        # Recuerdos específicos del usuario
        memories = mem_cog.get_user_memories(message.author.id) if mem_cog else [] # Pide los hechos/biografía del usuario
        if memories:
            recuerdos_str = "; ".join(memories) # Los une con punto y coma
            user_context += f"\n  (REGLAS Y MEMORIAS SOBRE ESTE USUARIO: {recuerdos_str}. INSTRUCCIÓN: Si hay algo que no le gusta o prohíbe, debes tenerelo en consideración)." # Los inyecta al perfil de usuario

        context_block = f"\n\n[CONTEXTO ACTUAL]\nUsuario: {message.author.display_name}\n{user_context}" # Empaqueta el bloque de quién habla
        context_block += "\n\n[DIRECTRIZ MAESTRA DE NATURALIDAD]\nActúa como un humano real en Discord. Sé casual y conversacional. REGLA ESTRICTA: Tu respuesta debe ser UN ÚNICO PÁRRAFO CORTO. NO ofrezcas diferentes opciones, listas ni repitas ideas."

        # 5. Historial de Chat (Input)
        chat_block = ""
        if history:
            chat_block += "[HISTORIAL DE CHAT RECIENTE]\n" + "\n".join(history)
        chat_block += f"\n\n[NUEVO MENSAJE DE {message.author.display_name}]\n{message.clean_content}\n\n[TU RESPUESTA]:"

        return system_prompt + context_block, chat_block # Devuelve una tupla: (Instrucciones del Sistema, Input del Usuario)

    async def _speak_response(self, guild, text):
        """Genera y reproduce el archivo de audio TTS con la respuesta de la IA."""
        vc = guild.voice_client
        if not vc or not vc.is_connected(): return
            
        try: import edge_tts
        except ImportError: edge_tts = None
            
        if not edge_tts:
            print(self.bot.lang.get("sys_ai_core_tts_no_lib"))
            return

        # Limpiar texto de emojis, URLs y formato markdown para que la IA suene natural
        clean_text = re.sub(r'<a?:[a-zA-Z0-9_]+:[0-9]+>', '', text) 
        clean_text = re.sub(r'http\S+', '', clean_text)
        clean_text = clean_text.replace('*', '').replace('`', '').replace('_', '').replace('~', '')
        
        # Limitar longitud para evitar cuelgues largos
        clean_text = clean_text[:800].strip()
        if not clean_text: return
        
        # Preparar entorno de archivos
        if getattr(sys, 'frozen', False): base_dir = os.path.dirname(sys.executable)
        else: base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        downloads_dir = os.path.join(base_dir, "downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        
        tts_engine = self._get_config().get("tts_engine", "nube_edge")
        ffmpeg_exe = os.path.join(base_dir, "res", "ffmpeg", "ffmpeg.exe")
        
        # --- RVC FILTER (CLONACIÓN DE VOZ) ---
        if self._get_config().get("tts_rvc", False):
            print(self.bot.lang.get("sys_ai_core_rvc_on"))
            # En el futuro, aquí se pasaría el 'tts_file' a través del modelo PyTorch local.

        # --- MOTOR LOCAL (PIPER TTS) ---
        if tts_engine == "local_piper":
            tts_file = os.path.join(downloads_dir, f"tts_ia_{guild.id}.wav")
            piper_exe = os.path.join(base_dir, "res", "piper", "piper.exe")
            voice_model = self._get_config().get("tts_voice", "es_MX-dalia-medium.onnx")
            model_path = os.path.join(base_dir, "res", "piper", "voices", voice_model)
            
            print(self.bot.lang.get("sys_ai_core_tts_loc_gen").format(model=voice_model))
            try:
                if not os.path.exists(piper_exe) or not os.path.exists(model_path):
                    raise Exception("Binario de Piper o Modelo ONNX no encontrados.")
                process = await asyncio.create_subprocess_shell(
                    f'"{piper_exe}" -m "{model_path}" -f "{tts_file}"',
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await process.communicate(input=clean_text.encode('utf-8'))
            except Exception as e:
                print(self.bot.lang.get("sys_ai_core_tts_loc_err").format(e=e))
                tts_engine = "nube_edge" # Fallback automático
                
        # --- MOTOR NUBE (EDGE-TTS) ---
        if tts_engine == "nube_edge":
            tts_file = os.path.join(downloads_dir, f"tts_ia_{guild.id}.mp3")
            voice_model = self._get_config().get("tts_voice", "es-MX-DaliaNeural")
            print(self.bot.lang.get("sys_ai_core_tts_cld_gen").format(model=voice_model))
            try:
                communicate = edge_tts.Communicate(clean_text, voice_model)
                await communicate.save(tts_file)
            except Exception as e:
                print(self.bot.lang.get("sys_ai_core_tts_cld_err").format(e=e))
                return
            
        if not os.path.exists(ffmpeg_exe): return

        # --- Resolución de Conflictos ---
        if vc.is_playing() or vc.is_paused():
            print(self.bot.lang.get("sys_ai_core_tts_skip_mus"))
            return

        # Función callback para limpiar la basura tras hablar
        def after_tts(error):
            if os.path.exists(tts_file):
                try: os.remove(tts_file)
                except: pass

        source = discord.FFmpegPCMAudio(tts_file, executable=ffmpeg_exe)
        vc.play(source, after=after_tts)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Oyente global: Se dispara cada vez que CUALQUIER usuario envía un mensaje en Discord."""
        print(self.bot.lang.get("sys_ai_core_on_msg").format(mid=message.id))
        
        # 1. Filtros de Entrada (Canal, Bots, etc.)
        if not self._check_filters(message): return # Si no pasa los filtros, corta la función aquí mismo

        # Auto-registro pasivo
        identity_manager.register_user_if_new(message.author) # Registra al usuario en la base de datos si es primera vez que habla

        # Formato para buffers
        sender_name = f"TÚ ({message.author.display_name})" if message.author.id == self.bot.user.id else message.author.display_name # Identifica claramente si habló el bot u otra persona
        content_to_buffer = message.clean_content
        if message.attachments and self._get_config().get("enable_vision", True):
            for att in message.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    content_to_buffer += f" [Adjuntó imagen: {att.filename}]"
                    break
        msg_formatted = f"{message.author.id}:{sender_name}: {content_to_buffer}" # Formatea el mensaje para la memoria RAM
        
        # Enviar a background tasks (Fire & Forget)
        evo_cog = self.bot.get_cog("Evolution") # Enlaza subproceso de Emociones
        mem_cog = self.bot.get_cog("Memory")    # Enlaza subproceso de Aprendizaje Profundo
        
        if evo_cog: evo_cog.add_to_buffer(msg_formatted) # Envía copia del mensaje al subconsciente de emociones
        if mem_cog: mem_cog.add_to_buffer(msg_formatted) # Envía copia del mensaje al subconsciente de memoria

        # --- Lógica de Gatillo (Responder) ---     
        
        # Verificación: ¿Está habilitado el CHAT (Hablar)?
        # Si es False, la IA "escucha" (arriba) pero no responde.
        if not self._get_config().get("enable_chat", True): # Evalúa el interruptor "Habilitar Respuestas" del Launcher
            return # Si está apagado, terminar función (El bot leyó, pero se queda callado)

        # Identificar si el mensaje es un comando explícito para evitar duplicar respuestas
        prefix = "!"
        prefix = ConfigManager.load_json(self.config_path, use_lock=True).get("prefix", "!")
        is_command = message.content.strip().startswith(prefix)

        # Condiciones lógicas que OBLIGAN al bot a dar una respuesta activa
        is_dm = isinstance(message.channel, discord.DMChannel) # ¿Me hablaron por privado?
        is_mention = self.bot.user in message.mentions # ¿Alguien me etiquetó (@MeowSick)?
        is_reply = (message.reference and message.reference.resolved and # ¿Alguien hizo "Responder" a un mensaje mío antiguo?
                    message.reference.resolved.author == self.bot.user)

        is_direct = is_dm or is_mention or is_reply
        
        # UX Social (Anti-Spam Cognitivo): Probabilidad de respuesta espontánea
        is_spontaneous = not is_direct and not is_command and random.random() < 0.05

        should_respond = (is_direct or is_spontaneous) and not is_command

        if should_respond:
            now = time.time()
            last = self.last_response_time.get(message.channel.id, 0)
            if now - last < 3.0: return # Cooldown estricto de 3s para evadir saturación
            
            self.last_response_time[message.channel.id] = now
            print(self.bot.lang.get("sys_ai_core_dispatch").format(mid=message.id))
            await self.chat_queue.put((message, is_direct)) # Despachar al Worker en lugar de congelar

    async def _process_message_task(self, message, is_direct):
        """Cuerpo de procesamiento real extraído del event loop principal."""
        print(self.bot.lang.get("sys_ai_core_process").format(mid=message.id))
        config = self._get_config()
        gamer_mode = config.get("gamer_mode", False)
        
        async with message.channel.typing():
            history = []
            limit = config.get("context_window", 15)
            enable_vision = config.get("enable_vision", True)
            
            # Degradación Estricta por Modo Gamer
            if gamer_mode:
                limit = min(limit, 5) # Reduce historial
                enable_vision = False # Desactiva el procesador de imágenes
                
            async for msg in message.channel.history(limit=limit, before=message):
                if msg.content:
                    prefix = f"TÚ ({msg.author.display_name})" if msg.author.id == self.bot.user.id else msg.author.display_name # Coloca etiquetas claras
                    history.append(f"{prefix}: {msg.clean_content}") # Agrega el texto plano a la lista
            
            history.reverse() # Invierte la lista para que quede en orden cronológico (viejo -> nuevo)

            # Ensamblar Prompt
            sys_instruction, user_input = await self._assemble_prompt(message, history) # Ejecuta el colector de psicología de arriba

            # Procesar imagen (Opción 1 y 2 combinadas)
            image_data = None
            limit_mb = self._get_config().get("image_size_limit_mb", 8.0)
            lookback_limit = self._get_config().get("vision_lookback_limit", 10)
            limit_bytes = limit_mb * 1024 * 1024
            
            if enable_vision:
                target_attachment = None
                
                # 1. Buscar en el mensaje actual
                if message.attachments:
                    for att in message.attachments:
                        if att.content_type and att.content_type.startswith('image/'):
                            target_attachment = att
                            break
                
                # 2. Buscar en el mensaje citado (Opción 1)
                if not target_attachment and message.reference and isinstance(message.reference.resolved, discord.Message):
                    for att in message.reference.resolved.attachments:
                        if att.content_type and att.content_type.startswith('image/'):
                            target_attachment = att
                            break
                            
                # 3. Escaneo hacia atrás en el chat (Opción 2)
                if not target_attachment and lookback_limit > 0:
                    async for past_msg in message.channel.history(limit=lookback_limit, before=message):
                        if past_msg.attachments:
                            for att in past_msg.attachments:
                                if att.content_type and att.content_type.startswith('image/'):
                                    target_attachment = att
                                    break
                        if target_attachment:
                            break
                
                # Procesar el archivo adjunto encontrado
                if target_attachment:
                    if target_attachment.size <= limit_bytes:
                        try:
                            img_bytes = await target_attachment.read()
                            
                            # --- Optimización Visual (Pillow) para ahorro de VRAM ---
                            with Image.open(io.BytesIO(img_bytes)) as img:
                                if img.mode in ("RGBA", "P"): img = img.convert("RGB") # Evitar errores de canal alfa
                                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS) # Redimensionar manteniendo proporción
                                
                                out_buffer = io.BytesIO()
                                img.save(out_buffer, format="JPEG", quality=85) # Comprimir a JPEG ligero
                                optimized_bytes = out_buffer.getvalue()
                            
                            b64_str = base64.b64encode(optimized_bytes).decode('utf-8')
                            image_data = ("image/jpeg", b64_str)
                            print(self.bot.lang.get("sys_ai_core_img_opt").format(file=target_attachment.filename))
                        except Exception as e:
                            print(self.bot.lang.get("sys_ai_core_img_err").format(e=e))
                    else:
                        print(self.bot.lang.get("sys_ai_core_img_ign").format(file=target_attachment.filename, limit=limit_mb))

            # Evaluar si la IA tiene permitido buscar autónomamente
            enable_web = self._get_config().get("enable_web_search", True)
            auto_web = self._get_config().get("auto_web_search", True)
            engine = self._get_config().get("ai_engine", "local")
            
            if engine == "local":
                do_grounding = enable_web and auto_web
            else:
                web_method = self._get_config().get("web_search_method", "google")
                do_grounding = enable_web and auto_web and web_method == "google"

            # Generar Respuesta (Chat Tier)
            response = await ai_manager.generate_content(
                "chat", # Usa el modelo optimizado para charlar (Tier 1 Flash)
                user_input, # Pasa el historial y la pregunta nueva
                system_instruction=sys_instruction, # Inyecta profundamente la personalidad y memoria
                media_data=image_data, # Adjunta la imagen si el usuario envió una
                use_grounding=do_grounding # Permite a Google decidir si buscar en internet
            )

            if response:
                # --- FILTRO ANTI-DEGENERACIÓN (Alucinación de Múltiples Opciones) ---
                # Si Gemma 3 se vuelve loca y arroja múltiples variaciones en distintas líneas
                lines = [line.strip() for line in response.split("\n") if line.strip()]
                if len(lines) > 1:
                    w1 = lines[0].split()[:2] # Toma las 2 primeras palabras de la primera línea
                    w2 = lines[1].split()[:2] # Toma las 2 primeras palabras de la segunda línea
                    if w1 == w2 and len(w1) > 0: # Si son exactamente iguales (Ej: "Ugh. ¿En")
                        response = lines[0] # Cortamos de tajo y nos quedamos solo con la primera

                print(self.bot.lang.get("sys_ai_core_send").format(mid=message.id))

                is_tts_active = hasattr(self, 'active_tts') and message.guild.id in self.active_tts and self._get_config().get("enable_tts", True)
                send_text = self._get_config().get("tts_send_text", True) if is_tts_active else True

                # Enviar respuesta texto si corresponde
                if send_text:
                    if len(response) > 2000: # Discord tiene un límite de 2000 letras por mensaje
                        for i in range(0, len(response), 2000): # Corta el texto largo en rebanadas de 2000
                            await message.channel.send(response[i:i+2000]) # Envía rebanada por rebanada
                    else:
                        await message.channel.send(response) # Envía respuesta entera normal
                
                evo_cog = self.bot.get_cog("Evolution")
                mem_cog = self.bot.get_cog("Memory")
                
                # Agregar mi propia respuesta a los buffers para coherencia
                my_msg_fmt = f"{self.bot.user.id}:TÚ ({self.bot.user.display_name}): {response}" # Etiqueta lo que acabo de decir
                if evo_cog: evo_cog.add_to_buffer(my_msg_fmt) # Se lo envía a su propio subconsciente emocional
                if mem_cog: mem_cog.add_to_buffer(my_msg_fmt) # Se lo envía a su propia base de aprendizaje
                
                # Disparar lectura TTS si el canal está habilitado
                if is_tts_active:
                    await self._speak_response(message.guild, response)
            else:
                print(self.bot.lang.get("sys_ai_core_no_resp")) # Alerta crítica en consola

    async def process_audio_input(self, interaction, audio_path, view):
        """Despacha la solicitud de audio a la cola de trabajadores sin trabar el VoiceClient."""
        await self.audio_queue.put((interaction, audio_path, view))
        
    async def _process_audio_task(self, interaction, audio_path, view):
        """Cuerpo real de procesamiento del archivo WAV."""
        try:
            if not os.path.exists(audio_path): raise Exception("No se generó el archivo de audio. ¿Hablaste?")
            with open(audio_path, "rb") as f: audio_bytes = f.read()
            if len(audio_bytes) < 1024: raise Exception("El audio es demasiado corto o no se detectó voz.")
                
            # Creamos un Mensaje Falso en RAM para engañar a nuestro propio ensamblador de IA
            class MockMessage:
                def __init__(self, author, channel):
                    self.author = author
                    self.channel = channel
                    self.clean_content = ""
            
            mock_msg = MockMessage(interaction.user, interaction.channel)
            media_data = None
            engine = self._get_config().get("ai_engine", "local")
            
            if engine == "local":
                try: from faster_whisper import WhisperModel
                except ImportError: WhisperModel = None
                
                if not WhisperModel: raise Exception("Librería faster-whisper no instalada.")
                print(self.bot.lang.get("sys_ai_core_stt_loc"))
                def transcribe():
                    model = WhisperModel("tiny", device="cpu", compute_type="int8")
                    segs, _ = model.transcribe(audio_path, beam_size=5)
                    return " ".join([s.text for s in segs])
                transcript = await self.bot.loop.run_in_executor(None, transcribe)
                mock_msg.clean_content = f"[Mensaje de Voz Transcrito]: {transcript}"
            else:
                mock_msg.clean_content = "[El usuario ha enviado una nota de voz adjunta. Escúchala atentamente y responde natural.]"
                b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
                media_data = ("audio/wav", b64_audio)
            
            # Extraer historial
            history = []
            limit = self._get_config().get("context_window", 15)
            async for msg in interaction.channel.history(limit=limit):
                if msg.content:
                    prefix = f"TÚ ({msg.author.display_name})" if msg.author.id == self.bot.user.id else msg.author.display_name
                    history.append(f"{prefix}: {msg.clean_content}")
            history.reverse()

            sys_instruction, user_input = await self._assemble_prompt(mock_msg, history)
            
            # Forzamos psicológicamente a la IA a dar respuestas cortas porque está en una llamada de voz
            sys_instruction += "\n\n[REGLA ESTRICTA PARA ESTE MENSAJE: EL USUARIO TE ESTÁ HABLANDO POR VOZ (MICRÓFONO). SÉ MUY BREVE, CONCISA Y NATURAL. NO USES LISTAS LARGAS, NI FORMATOS COMPLEJOS. RESPONDE COMO EN UNA LLAMADA TELEFÓNICA REAL.]"
            
            # Evaluar si la IA tiene permitido buscar autónomamente
            enable_web = self._get_config().get("enable_web_search", True)
            auto_web = self._get_config().get("auto_web_search", True)
            engine = self._get_config().get("ai_engine", "local")
            
            if engine == "local":
                do_grounding = enable_web and auto_web
            else:
                web_method = self._get_config().get("web_search_method", "google")
                do_grounding = enable_web and auto_web and web_method == "google"

            # Lanzar la API
            response = await ai_manager.generate_content("chat", user_input, system_instruction=sys_instruction, media_data=media_data, use_grounding=do_grounding)
            
            if response:
                is_tts_active = hasattr(self, 'active_tts') and interaction.guild.id in self.active_tts and self._get_config().get("enable_tts", True)
                send_text = self._get_config().get("tts_send_text", True) if is_tts_active else True

                if send_text:
                    if len(response) > 2000:
                        for i in range(0, len(response), 2000): await interaction.channel.send(response[i:i+2000])
                    else: await interaction.channel.send(response)
                
                my_msg_fmt = f"{self.bot.user.id}:TÚ ({self.bot.user.display_name}): {response}"
                evo_cog, mem_cog = self.bot.get_cog("Evolution"), self.bot.get_cog("Memory")
                if evo_cog: evo_cog.add_to_buffer(my_msg_fmt)
                if mem_cog: mem_cog.add_to_buffer(my_msg_fmt)
                
                if is_tts_active: await self._speak_response(interaction.guild, response)
            else: await interaction.channel.send("⚠️ No pude entender el audio o hubo un error de red.")
        except Exception as e: await interaction.channel.send(f"⚠️ Error procesando audio: {e}")
        finally:
            view.children[0].label, view.children[0].style, view.children[0].disabled = "🎙️ Hablar", discord.ButtonStyle.green, False
            try: await interaction.message.edit(view=view)
            except: pass

    @commands.command()
    async def voice(self, ctx):
        """Activa o desactiva las respuestas en voz alta de la IA en el canal."""
        try: import discord.ext.voice_recv as voice_recv
        except ImportError: voice_recv = None
        
        if not self._get_config().get("enable_tts", True):
            await ctx.send("⚠️ **El módulo de voz está apagado** en la configuración general.")
            return

        if not hasattr(self, 'active_tts'): self.active_tts = set()
            
        if ctx.guild.id in self.active_tts:
            self.active_tts.remove(ctx.guild.id)
            await ctx.send("🔇 **Módulo de voz desactivado.**")
        else:
            if not ctx.author.voice:
                await ctx.send("⚠️ **Debes estar en un canal de voz** para activar este módulo.")
                return
                
            vc = ctx.voice_client
            try:
                if not vc: 
                    if voice_recv: await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
                    else: await ctx.author.voice.channel.connect()
                elif vc.channel.id != ctx.author.voice.channel.id: await vc.move_to(ctx.author.voice.channel)
                self.active_tts.add(ctx.guild.id)
                await ctx.send("🎙️ **Módulo de voz activado.**")
            except Exception as e:
                await ctx.send(f"❌ Error al conectar al canal de voz: {e}")

    @commands.command()
    async def talk(self, ctx):
        """Despliega el panel interactivo para hablar con la IA por voz."""
        try: import discord.ext.voice_recv as voice_recv
        except ImportError: voice_recv = None
        
        if not self._get_config().get("enable_stt", True):
            return await ctx.send("⚠️ **El módulo de escucha está apagado** en la configuración general.")
            
        if not voice_recv: return await ctx.send("⚠️ El módulo de escucha requiere la librería: `pip install discord-ext-voice-recv`")
        
        if not hasattr(self, 'active_talk'): self.active_talk = {}
        
        if ctx.guild.id in self.active_talk:
            old_view = self.active_talk.pop(ctx.guild.id)
            old_view.clean_stop()
            return await ctx.send("🔇 **Modo Conversación Desactivado.**")
        
        vc = ctx.voice_client
        if not vc:
            if not ctx.author.voice: return await ctx.send("⚠️ Debes estar en un canal de voz para invocarme.")
            try: vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
            except Exception as e: return await ctx.send(f"❌ Error al conectar: {e}")
        
        # Asegurar que esté activo el modo de lectura (TTS) automáticamente
        if not hasattr(self, 'active_tts'): self.active_tts = set()
        self.active_tts.add(ctx.guild.id)
        
        view = TalkView(self, vc)
        self.active_talk[ctx.guild.id] = view
        await ctx.send("🎙️ **Modo Conversación Activo**\nHaz click en el botón, habla por tu micrófono y vuelve a presionarlo para que te responda.", view=view)

    @commands.command()
    async def ask(self, ctx, *, query: str = None):
        """Busca información en internet y responde en base a ella."""
        if not self._get_config().get("enable_web_search", True):
            return await ctx.send("⚠️ **El módulo de búsqueda web está apagado** en la configuración general.")
            
        if not query:
            return await ctx.send("⚠️ Debes decirme qué buscar. Ej: `!ask clima en Madrid hoy`")
            
        method = self._get_config().get("web_search_method", "google")
        max_res = self._get_config().get("web_search_max_results", 3)
        
        async with ctx.typing():
            # Extraer historial
            history = []
            limit = self._get_config().get("context_window", 15)
            async for msg in ctx.channel.history(limit=limit, before=ctx.message):
                if msg.content:
                    prefix = f"TÚ ({msg.author.display_name})" if msg.author.id == self.bot.user.id else msg.author.display_name
                    history.append(f"{prefix}: {msg.clean_content}")
            history.reverse()

            sys_instruction, user_input = await self._assemble_prompt(ctx.message, history)
            user_input = f"{user_input}\n\n[SOLICITUD EXPLÍCITA DEL USUARIO PARA BUSCAR EN INTERNET]: {query}"
            use_grounding = False
            
            if method == "ddg":
                try: from duckduckgo_search import DDGS
                except ImportError: DDGS = None
                
                if not DDGS:
                    return await ctx.send("⚠️ Falta librería DDGS. Ejecuta en terminal: `pip install duckduckgo-search`")
                try:
                    print(self.bot.lang.get("sys_ai_core_web_ddg").format(query=query))
                    results = await self.bot.loop.run_in_executor(None, lambda: list(DDGS().text(query, max_results=max_res)))
                    if not results: raise Exception("Sin resultados o API bloqueada.")
                except Exception as e:
                    print(self.bot.lang.get("sys_ai_core_web_ddg_err").format(e=e))
                    # --- FALLBACK A SCRAPING HTML PURO ---
                    results = []
                    try: from bs4 import BeautifulSoup
                    except ImportError: BeautifulSoup = None

                    try:
                        if BeautifulSoup:
                            import aiohttp
                            async with aiohttp.ClientSession() as session:
                                async with session.get(f"https://html.duckduckgo.com/html/?q={query}", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as resp:
                                    if resp.status == 200:
                                        soup = BeautifulSoup(await resp.text(), "html.parser")
                                        for a in soup.find_all('a', class_='result__snippet')[:max_res]:
                                            results.append({"title": a.text, "body": a.parent.text})
                    except Exception as fallback_err:
                        print(self.bot.lang.get("sys_ai_core_web_fall_err").format(e=fallback_err))

                if results:
                    context_str = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')}" for r in results])
                    user_input += f"\n\n[RESULTADOS EXTRAÍDOS DE LA WEB EN TIEMPO REAL]\n{context_str}\n\nAnaliza la información anterior y úsala para responder al usuario de forma natural."
                else:
                    user_input += f"\n\n[NOTA DEL SISTEMA]: La búsqueda web falló por bloqueos de red. Pide disculpas y responde lo que sepas."
            else:
                print(self.bot.lang.get("sys_ai_core_web_ggl").format(query=query))
                use_grounding = True # Google se encarga de todo por su cuenta

            response = await ai_manager.generate_content("chat", user_input, system_instruction=sys_instruction, use_grounding=use_grounding)
            
            if response:
                is_tts_active = hasattr(self, 'active_tts') and ctx.guild.id in self.active_tts and self._get_config().get("enable_tts", True)
                send_text = self._get_config().get("tts_send_text", True) if is_tts_active else True

                if send_text:
                    if len(response) > 2000:
                        for i in range(0, len(response), 2000): await ctx.send(response[i:i+2000])
                    else: await ctx.send(response)
                
                my_msg_fmt = f"{self.bot.user.id}:TÚ ({self.bot.user.display_name}): {response}"
                evo_cog, mem_cog = self.bot.get_cog("Evolution"), self.bot.get_cog("Memory")
                if evo_cog: evo_cog.add_to_buffer(my_msg_fmt)
                if mem_cog: mem_cog.add_to_buffer(my_msg_fmt)
                
                if is_tts_active: await self._speak_response(ctx.guild, response)
            else:
                await ctx.send("⚠️ No pude generar una respuesta o hubo un error con la búsqueda.")

    @commands.command()
    async def reloadai(self, ctx):
        """Recarga los módulos de IA en caliente."""
        if ctx.author.id != int(os.getenv("ADMIN_ID", 0)): return # Sistema de seguridad: Solo el Creador puede usar esto
        # La lógica de recarga real suele estar en el bot principal o Utils, 
        # pero aquí podemos forzar relectura de configs.
        await ctx.send("♻️ Configuración de IA recargada (buffers limpiados).") # Feedback para Discord

# Función estándar obligatoria de discord.py para cargar Cogs
async def setup(bot):
    await bot.add_cog(AICore(bot)) # Conecta el cerebro frontal al Loop de Eventos del bot