import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import sys
from .utils import ai_manager
from .identity import identity_manager
from shared.config_manager import ConfigManager

class Evolution(commands.Cog):
    """
    Submódulo de Emociones (Subconsciente).
    Se encarga de evaluar pasivamente el tono de la conversación en segundo plano
    y altera el estado de ánimo general del bot, lo que a su vez afecta sus futuras respuestas.
    """
    def __init__(self, bot):
        self.bot = bot # Instancia principal del bot
        
        # Ruta al archivo de configuración general
        if getattr(sys, 'frozen', False):
            self.settings_path = os.path.join(os.path.dirname(sys.executable), "settings", "config.json")
            self.base_path = os.path.join(os.path.dirname(sys.executable), "cogs", "AI", "memory") 
        else:
            self.settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "settings", "config.json")
            self.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory") 
            
        self.state_file = os.path.join(self.base_path, "estado_animo.json") # Guarda el mood actual
        self.history_file = os.path.join(self.base_path, "historial_estados.json") # Log histórico de cambios de mood
        self.prompts_file = os.path.join(self.base_path, "prompts.json") # Plantillas de instrucciones
        
        self.mood_buffer = [] # Lista temporal en RAM para almacenar los últimos mensajes leídos
        
        os.makedirs(self.base_path, exist_ok=True) # Crea la carpeta memory si no existe
        self._ensure_files() # Crea los archivos base si se borraron

        # Temporizador de inactividad
        self.last_activity = discord.utils.utcnow()
        self.mood_decay_loop.start() # Inicia el reloj en segundo plano

        # Arquitectura Anti-Event Storms
        self.mood_queue = asyncio.Queue()
        self.worker_task = self.bot.loop.create_task(self._evolution_worker())

    def cog_unload(self):
        """Limpia la tarea en segundo plano si el módulo se apaga o recarga."""
        self.mood_decay_loop.cancel()
        if hasattr(self, 'worker_task'): self.worker_task.cancel()

    async def _evolution_worker(self):
        """Worker asíncrono en bucle para encolar los análisis pesados de fondo."""
        while True:
            try:
                await self.mood_queue.get()
                await self.process_mood_analysis()
                self.mood_queue.task_done()
            except asyncio.CancelledError: break
            except Exception as e: print(self.bot.lang.get("sys_ai_evo_work_err").format(e=e))

    def _ensure_files(self):
        """Crea las estructuras JSON por defecto si los archivos de estado no existen."""
        if not os.path.exists(self.state_file):
            ConfigManager.save_json(self.state_file, {"estado_animo": "Neutral: Solo existiendo."}, use_lock=False)
        if not os.path.exists(self.history_file):
            ConfigManager.save_json(self.history_file, [], use_lock=False)

    def _get_config(self):
        """Lee el archivo de configuración para obtener los límites personalizados."""
        return ConfigManager.load_json(self.settings_path, use_lock=True).get("ai_config", {})

    def get_current_mood(self):
        """Lee el archivo JSON para devolver el estado emocional vigente del bot."""
        data = ConfigManager.load_json(self.state_file, use_lock=False)
        return data.get("estado_animo", "Neutral") if isinstance(data, dict) else "Neutral"

    def get_mood_history(self, limit=None):
        """Devuelve los últimos estados de ánimo registrados para dar contexto de transición."""
        if limit is None:
            limit = self._get_config().get("mood_history_limit", 10) # Usa el límite configurable o 10 por defecto
        data = ConfigManager.load_json(self.history_file, use_lock=False)
        if isinstance(data, list):
            return [entry.get("estado_animo") for entry in data[-limit:] if isinstance(entry, dict)]
        return []

    def _load_prompt(self, key):
        """Recupera la plantilla de instrucciones específica para el análisis de evolución."""
        data = ConfigManager.load_json(self.prompts_file, use_lock=False)
        return data.get(key, "") if isinstance(data, dict) else ""

    async def process_mood_analysis(self):
        """
        Corutina principal del subconsciente.
        Toma los últimos mensajes, los junta con la identidad y el estado actual,
        y le pide a la IA que decida cómo debería sentirse el bot ahora.
        """
        if not self.mood_buffer: return # Si el buffer está vacío, aborta
        
        # Snapshot (copia de seguridad) del buffer y limpieza inmediata para seguir recibiendo mensajes
        messages = list(self.mood_buffer)
        self.mood_buffer = []
        
        print(self.bot.lang.get("sys_ai_evo_proc"))
        
        # Recopilación de contexto psicológico
        current_mood = self.get_current_mood() # Cómo nos sentimos ahora
        history = self.get_mood_history() # Cómo nos hemos sentido antes
        identity = identity_manager.get_identity_block() # Quiénes somos
        prompt_template = self._load_prompt("evolucion_analisis") # La orden estricta extraída de prompts.json

        if not prompt_template:
            # Prompt de fallback de emergencia si no existe el archivo json
            prompt_template = """
            Eres el subconsciente de la IA. Analiza la conversación y ajusta el estado de ánimo.
            Identidad: {identidad}
            Estado Actual: {estado_actual}
            Historial Reciente: {historial}
            Conversación: {mensajes}
            
            Responde SOLO un JSON: {{{{"estado_animo": "Nuevo Estado: Justificación"}}}}
            """

        # Rellena los huecos ({variables}) usando replace para evitar colisiones con las llaves {} del JSON
        final_prompt = prompt_template.replace("{identidad}", identity)\
                                      .replace("{estado_actual}", current_mood)\
                                      .replace("{historial}", "\n".join(history))\
                                      .replace("{mensajes}", "\n".join(messages))\
                                      .replace("{estados_posibles}", "(Lee guidelines para tono)")

        # Llama a Gemini usando el tier 'evolution' (Optimizado para análisis inteligente con temperatura controlada)
        response = await ai_manager.generate_content("evolution", final_prompt, temperature=0.5)
        
        if response:
            clean_json = ai_manager.clean_json_response(response) # Limpia etiquetas Markdown (```json) de la respuesta
            try:
                data = json.loads(clean_json) # Convierte el texto de la respuesta a un diccionario de Python
                new_mood = data.get("estado_animo") # Extrae el nuevo estado sugerido
                
                if new_mood:
                    # Sobrescribe el archivo de estado con la nueva emoción
                    ConfigManager.save_json(self.state_file, {"estado_animo": new_mood}, use_lock=False)
                    
                    # Lee el historial completo existente
                    full_hist_raw = ConfigManager.load_json(self.history_file, use_lock=False)
                    full_hist = full_hist_raw if isinstance(full_hist_raw, list) else []
                    
                    # Añade el nuevo estado con su marca de tiempo oficial de Discord
                    full_hist.append({"timestamp": str(discord.utils.utcnow()), "estado_animo": new_mood})
                    
                    # Prevenir que el archivo crezca infinitamente (si está activado)
                    enable_limit = self._get_config().get("enable_history_limit", True)
                    if enable_limit:
                        limit_save = self._get_config().get("history_save_limit", 50)
                        read_limit = self._get_config().get("mood_history_limit", 10)
                        limit_save = max(limit_save, read_limit) # Asegurar que guarda al menos lo que se necesita leer
                        full_hist = full_hist[-limit_save:]
                    
                    # Guarda el historial actualizado
                    ConfigManager.save_json(self.history_file, full_hist, use_lock=False)
                        
                    print(self.bot.lang.get("sys_ai_evo_upd").format(mood=new_mood))
            except Exception as e:
                print(self.bot.lang.get("sys_ai_evo_err_json").format(e=e)) # Captura errores si la IA respondió basura en lugar de JSON

    def add_to_buffer(self, msg_content):
        """
        Recibe mensajes del canal y los apila en la memoria RAM temporal.
        Si el contador llega al límite, dispara el proceso de análisis de forma asíncrona.
        """
        self.last_activity = discord.utils.utcnow() # Resetea el reloj de inactividad al escuchar a alguien
        self.mood_buffer.append(msg_content) # Añade el texto a la lista
        buffer_limit = self._get_config().get("mood_buffer_limit", 15) # Fix: Default 15 (era 5, se enojaba muy rápido)
        if len(self.mood_buffer) >= buffer_limit: # Si alcanzamos los X mensajes...
            self.bot.loop.create_task(self.mood_queue.put(True)) # Despacha a la cola de trabajo segura

    @tasks.loop(minutes=30)
    async def mood_decay_loop(self):
        """
        Se ejecuta cada 30 minutos. Evalúa si han pasado X horas desde el último mensaje.
        Si es así y el bot estaba alterado, lo devuelve a su estado Neutral base.
        """
        now = discord.utils.utcnow()
        decay_hours = self._get_config().get("mood_decay_hours", 2.0)
        decay_seconds = decay_hours * 3600
        
        if (now - self.last_activity).total_seconds() > decay_seconds:
            current_mood = self.get_current_mood()
            if not current_mood.startswith("Neutral"):
                print(self.bot.lang.get("sys_ai_evo_decay").format(hours=decay_hours))
                new_mood = "Neutral: Me he calmado tras un largo rato sin interactuar con nadie."
                
                ConfigManager.save_json(self.state_file, {"estado_animo": new_mood}, use_lock=False)
                
                full_hist_raw = ConfigManager.load_json(self.history_file, use_lock=False)
                full_hist = full_hist_raw if isinstance(full_hist_raw, list) else []
                full_hist.append({"timestamp": str(now), "estado_animo": new_mood})
                
                enable_limit = self._get_config().get("enable_history_limit", True)
                if enable_limit:
                    limit_save = max(self._get_config().get("history_save_limit", 50), self._get_config().get("mood_history_limit", 10))
                    full_hist = full_hist[-limit_save:]
                
                ConfigManager.save_json(self.history_file, full_hist, use_lock=False)

    @mood_decay_loop.before_loop
    async def before_decay_loop(self):
        await self.bot.wait_until_ready() # Espera a que el bot esté conectado antes de iniciar el reloj

# Registro estándar en el Loop del bot
async def setup(bot):
    await bot.add_cog(Evolution(bot))