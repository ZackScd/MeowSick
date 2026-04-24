import discord
from discord.ext import commands
import json
import os
import sys
import asyncio
from .utils import ai_manager
from .identity import identity_manager
from shared.config_manager import ConfigManager

class Memory(commands.Cog):
    """
    Submódulo de Memoria a Largo Plazo (Subconsciente).
    Analiza pasivamente el buffer de conversaciones para extraer y persistir
    información clave sobre los usuarios, las relaciones y el propio autoconcepto de la IA.
    """
    def __init__(self, bot):
        self.bot = bot # Instancia principal del bot.
        # Resolución de rutas de memoria, adaptándose a entorno de desarrollo (.py) o producción (.exe).
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.join(os.path.dirname(sys.executable), "cogs", "AI", "memory")
            self.settings_path = os.path.join(os.path.dirname(sys.executable), "settings", "config.json")
        else:
            self.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory")
            self.settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "settings", "config.json")
            
        self.memoria_file = os.path.join(self.base_path, "memoria.json") # Hechos biográficos de usuarios.
        self.opiniones_file = os.path.join(self.base_path, "opiniones.json") # Afinidad y juicio sobre usuarios.
        self.autoconcepto_file = os.path.join(self.base_path, "autoconcepto.json") # Gustos y creencias propias.
        self.prompts_file = os.path.join(self.base_path, "prompts.json") # Plantillas de instrucciones para la IA.
        
        self.memory_buffer = [] # Buffer en RAM para acumular mensajes.
        
        os.makedirs(self.base_path, exist_ok=True) # Crea la carpeta /memory/ si no existe.
        self._ensure_files() # Valida y crea los archivos JSON base si es necesario.
        
        # Arquitectura Anti-Event Storms
        self.memory_queue = asyncio.Queue()
        self.worker_task = self.bot.loop.create_task(self._memory_worker())
        
    def cog_unload(self):
        """Limpieza del worker al apagar el módulo."""
        if hasattr(self, 'worker_task'): self.worker_task.cancel()

    async def _memory_worker(self):
        """Worker asíncrono en bucle para proteger el thread de Discord y el FileSystem."""
        while True:
            try:
                await self.memory_queue.get()
                await self.process_memory_tasks()
                self.memory_queue.task_done()
            except asyncio.CancelledError: break
            except Exception as e: print(self.bot.lang.get("sys_ai_mem_work_err").format(e=e))

    def _ensure_files(self):
        """Garantiza la existencia de los archivos JSON de memoria, creándolos con una estructura vacía si no se encuentran."""
        defaults = {
            self.memoria_file: {}, # Un diccionario vacío.
            self.opiniones_file: {}, # Un diccionario vacío.
            self.autoconcepto_file: {"gustos": [], "opiniones": {}} # Estructura con lista y diccionario.
        }
        for path, default_data in defaults.items():
            if not os.path.exists(path): # Si el archivo no existe en la ruta...
                ConfigManager.save_json(path, default_data, use_lock=False) # ...lo crea con su contenido por defecto.

    def _get_config(self):
        """Lee el archivo de configuración para obtener los límites personalizados."""
        return ConfigManager.load_json(self.settings_path, use_lock=True).get("ai_config", {})
        
    def _get_language_directive(self):
        full_cfg = ConfigManager.load_json(self.settings_path, use_lock=True) or {}
        lang_code = full_cfg.get("language", "es")
        lang_name = "ESPAÑOL (Spanish)" if lang_code == "es" else "ENGLISH"
        return f"[SYSTEM DIRECTIVE: You must analyze and generate the JSON response exclusively in {lang_name}]\n"

    def load_data(self, filename):
        """Utilidad genérica para cargar un archivo JSON de forma segura."""
        return ConfigManager.load_json(filename, use_lock=False)

    def save_data(self, filename, data):
        """Utilidad genérica para guardar datos en un archivo JSON con formato legible."""
        ConfigManager.save_json(filename, data, use_lock=False)

    def get_opinions_data(self):
        """Método público para que otros módulos (como core.py) puedan leer las opiniones actuales."""
        return self.load_data(self.opiniones_file) # Carga y devuelve el contenido de opiniones.json.
        
    def get_autoconcepto_data(self):
        """Método público para que otros módulos puedan leer el autoconcepto actual de la IA."""
        return self.load_data(self.autoconcepto_file) # Carga y devuelve el contenido de autoconcepto.json.

    def get_user_memories(self, user_id):
        """Método público para obtener la lista de hechos recordados sobre un usuario específico."""
        data = self.load_data(self.memoria_file) # Carga toda la base de datos de hechos.
        return data.get(str(user_id), []) # Devuelve la lista para ese ID de usuario, o una lista vacía si no hay nada.

    def _load_prompt(self, key):
        """Carga una plantilla de prompt específica desde el archivo prompts.json."""
        return ConfigManager.load_json(self.prompts_file, use_lock=False).get(key, "")

    async def process_memory_tasks(self):
        """
        Orquestador principal de las tareas de memoria. Se ejecuta cuando el buffer está lleno.
        Dispara en secuencia los diferentes análisis de la IA.
        """
        if not self.memory_buffer: return # Si no hay mensajes en el buffer, no hace nada.
        
        msgs = list(self.memory_buffer) # Crea una copia de los mensajes acumulados.
        self.memory_buffer = [] # Limpia el buffer inmediatamente para seguir acumulando nuevos mensajes.
        
        print(self.bot.lang.get("sys_ai_mem_proc"))
        
        # Ejecuta cada tarea de análisis en orden.
        await self._task_update_opinions(msgs)
        await self._task_update_self(msgs)
        await self._task_extract_facts(msgs)

    async def _task_update_opinions(self, msgs):
        """Tarea específica para analizar y actualizar la afinidad y opinión sobre los usuarios."""
        current_ops = self.load_data(self.opiniones_file) # Carga las opiniones actuales.
        prompt = self._load_prompt("memoria_opiniones") # Carga la plantilla de prompt para esta tarea.
        if not prompt: return # Si no hay prompt, no se puede continuar.

        # Busca el archivo de configuración principal para obtener los límites de afinidad.
        config_path = os.path.abspath(os.path.join(self.base_path, "..", "..", "..", "settings", "config.json"))
        cfg = ConfigManager.load_json(config_path, use_lock=True)
        aff_min = cfg.get("ai_config", {}).get("aff_min", -100) # Límite mínimo de afinidad.
        aff_max = cfg.get("ai_config", {}).get("aff_max", 100) # Límite máximo de afinidad.

        # Rellena la plantilla del prompt con los datos actuales, usando replace para evitar fallos con los JSON.
        final_prompt = prompt.replace("{identidad}", identity_manager.get_identity_block())\
                             .replace("{opiniones_actuales}", json.dumps(current_ops, ensure_ascii=False))\
                             .replace("{mensajes}", "\n".join(msgs))\
                             .replace("{aff_min}", str(aff_min))\
                             .replace("{aff_max}", str(aff_max))

        final_prompt = self._get_language_directive() + final_prompt
        resp = await ai_manager.generate_content("memory", final_prompt) # Llama a la IA con el modelo "memory".
        if resp: # Si la IA devolvió una respuesta...
            try:
                data = json.loads(ai_manager.clean_json_response(resp)) # Limpia y decodifica la respuesta JSON.
                # Fusión inteligente: Actualiza la información de cada usuario.
                bot_id = str(self.bot.user.id)
                for uid, info in data.items():
                    if uid == bot_id: continue # Impide que la IA genere una opinión sobre sí misma
                    if "afinidad" in info: # Asegura que la respuesta contiene la clave necesaria.
                        current_ops[uid] = info # Sobrescribe la opinión del usuario con la nueva.
                self.save_data(self.opiniones_file, current_ops) # Guarda el archivo actualizado.
            except: pass # Ignora errores de parseo si la IA responde mal.

    async def _task_update_self(self, msgs):
        """Tarea para que la IA reflexione sobre sí misma y actualice sus gustos y creencias."""
        current_self = self.load_data(self.autoconcepto_file) # Carga el autoconcepto actual.
        prompt = self._load_prompt("memoria_autoconcepto") # Carga la plantilla para esta tarea.
        if not prompt: return # Aborta si no hay prompt.

        # Rellena la plantilla con los datos, usando replace por seguridad de formato
        final_prompt = prompt.replace("{autoconcepto_actual}", json.dumps(current_self, ensure_ascii=False))\
                             .replace("{mensajes}", "\n".join(msgs))

        final_prompt = self._get_language_directive() + final_prompt
        resp = await ai_manager.generate_content("memory", final_prompt) # Llama a la IA.
        if resp: # Si hay respuesta...
            try:
                data = json.loads(ai_manager.clean_json_response(resp)) # Limpia y decodifica.
                # Fusión de datos:
                new_gustos = data.get("gustos", []) # Extrae la lista de nuevos gustos.
                # Combina la lista vieja con la nueva y usa 'set' para eliminar duplicados.
                current_self["gustos"] = list(set(current_self.get("gustos", []) + new_gustos)) 
                
                new_ops = data.get("opiniones", {}) # Extrae el diccionario de nuevas opiniones.
                current_self["opiniones"].update(new_ops) # Actualiza el diccionario existente con las nuevas.
                
                self.save_data(self.autoconcepto_file, current_self) # Guarda el archivo actualizado.
            except: pass # Ignora errores.

    async def _task_extract_facts(self, msgs):
        """Tarea para extraer hechos biográficos y atemporales sobre los usuarios."""
        current_mem = self.load_data(self.memoria_file) # Carga la memoria de hechos actual.
        prompt = self._load_prompt("memoria_filtrado") # Carga la plantilla de extracción.
        if not prompt: return # Aborta si no hay prompt.

        final_prompt = prompt.replace("{mensajes}", "\n".join(msgs)) # Rellena la plantilla con la conversación.
        
        final_prompt = self._get_language_directive() + final_prompt
        resp = await ai_manager.generate_content("memory", final_prompt) # Llama a la IA.
        if resp: # Si hay respuesta...
            try:
                data = json.loads(ai_manager.clean_json_response(resp)) # Limpia y decodifica.
                cambios = False # Bandera para saber si hubo alguna actualización.
                bot_id = str(self.bot.user.id)
                for uid, facts in data.items():
                    if uid == bot_id: continue # Impide categóricamente que la IA guarde hechos de sí misma aquí
                    if not isinstance(facts, list) or not facts: continue # Si la lista de hechos para un usuario está vacía o es inválida, la ignora.
                    if uid not in current_mem: current_mem[uid] = [] # Si es un usuario nuevo, crea su lista.
                    
                    for fact in facts:
                        if fact not in current_mem[uid]: # Solo añade el hecho si no está ya en la memoria.
                            current_mem[uid].append(fact) # Añade el nuevo hecho.
                            cambios = True # Marca que hubo un cambio.
                
                if cambios: # Si se añadió al menos un hecho nuevo...
                    self.save_data(self.memoria_file, current_mem) # ...guarda el archivo.
                    print(self.bot.lang.get("sys_ai_mem_upd")) # Y lo notifica en consola.
            except: pass # Ignora errores.

    def add_to_buffer(self, msg_formatted):
        """
        Método público llamado por `core.py` para alimentar el buffer de memoria.
        Si el buffer alcanza su límite, dispara el proceso de análisis en segundo plano.
        """
        self.memory_buffer.append(msg_formatted) # Añade el mensaje a la lista en RAM.
        buffer_limit = self._get_config().get("memory_buffer_limit", 5) # Lee el límite establecido en el Launcher
        if len(self.memory_buffer) >= buffer_limit: # Si hemos acumulado suficientes mensajes...
            self.bot.loop.create_task(self.memory_queue.put(True)) # Delega la carga al Worker dedicado.

async def setup(bot):
    """Función estándar de discord.py para registrar el Cog en el bot."""
    await bot.add_cog(Memory(bot)) # Conecta este módulo al bot principal.