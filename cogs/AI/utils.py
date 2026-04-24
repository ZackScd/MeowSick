import os
import aiohttp # Librería para hacer peticiones web asíncronas sin bloquear el bot
import json
import asyncio
import sys
from shared.config_manager import ConfigManager

class AIManager:
    """
    Gestor de Conexión a la API de Google Gemini.
    Administra la autenticación, la creación de peticiones HTTP (payloads),
    el manejo de errores (como cuotas excedidas) y la rotación automática de llaves.
    """
    def __init__(self):
        # ══════════════════════════════════════════════════════════════════
        # FIX CRÍTICO — Race Condition de Keys
        # ══════════════════════════════════════════════════════════════════
        # Las API Keys NO se leen aquí. AIManager se instancia al IMPORTAR
        # el módulo (línea final: ai_manager = AIManager()), lo cual ocurre
        # ANTES de que meowSick.py ejecute load_dotenv(). Si se leen aquí,
        # os.getenv() siempre devuelve None y Google rechaza con 400.
        # La solución: 'api_keys' es ahora una @property que lee el entorno
        # en el momento exacto de cada petición, siempre con el valor real.
        # ══════════════════════════════════════════════════════════════════
        self._api_keys_cache = None  # Cache interno; None = "todavía no leído"
        self.current_key_index = 0   # Puntero de rotación Round-Robin

        # Jerarquía de Modelos (Cascada de Inteligencia)
        # Nombres corregidos — los originales (gemini-3-flash-preview, gemini-flash-latest)
        # no existen en la API de Google y causaban 400/404 instantáneos.
        self.CHAT_HIERARCHY = [
            "gemini-2.5-flash-preview-04-17", # Tier 1: Gemini 2.5 Flash (Google AI Studio, 2025).
            "gemini-2.0-flash",               # Tier 2: Gemini 2.0 Flash, modelo estable.
            "gemini-1.5-flash"                # Tier 3: Salvavidas, siempre disponible en free tier.
        ]

        # Modelos de subprocesos: Gemma en Google AI Studio (nube), NO locales de Ollama.
        # Si el engine está en "local", estos modelos solo se usan si hay API Key configurada.
        self.MODELS = {
            "evolution": "gemma-3-27b-it",  # 27B: Razonamiento emocional profundo.
            "memory":    "gemma-3-12b-it"   # 12B: Extracción de datos, más ligero.
        }

        self.local_tools_supported = True  # Bandera: False si Ollama reportó que el modelo no soporta tools

    @property
    def api_keys(self):
        """
        Propiedad lazy — lee las keys en el momento de usarlas, nunca al instanciar.
        Así funciona correctamente aunque los cogs se importen antes que load_dotenv().
        También recarga automáticamente si el Launcher envía CMD_RELOAD.
        """
        raw_keys = [os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_API_KEY_2")]
        keys = [
            k.strip() for k in raw_keys
            if k and k.strip() and "pega_tu_clave" not in k
        ]
        if self._api_keys_cache != keys:  # Solo loguear si las keys cambiaron
            self._api_keys_cache = keys
            self.current_key_index = 0
            if keys:
                masked = keys[0][:5] + "..." + keys[0][-4:] if len(keys[0]) > 10 else "CORTA"
                print(f"🧠 🔑 [AI UTILS] {len(keys)} key(s) cargada(s). Activa: {masked}")
            else:
                print("🧠 ❌ [AI UTILS] No se encontró GEMINI_API_KEY. Verifica tu archivo .env")
        return self._api_keys_cache

    def get_current_key(self):
        """Devuelve la llave API activa. Retorna None si el usuario no configuró ninguna."""
        keys = self.api_keys  # Usa la property lazy
        if not keys: return None
        # Ajustar índice por si las keys cambiaron y ahora hay menos
        if self.current_key_index >= len(keys):
            self.current_key_index = 0
        return keys[self.current_key_index]

    def rotate_key(self):
        """Cambia a la siguiente llave API disponible (Round-Robin) cuando la actual alcanza el límite."""
        keys = self.api_keys
        if len(keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(keys)
            print(f"🧠 🔄 [AI UTILS] Rotando a API Key #{self.current_key_index}")
            return True
        return False  # Solo hay 1 llave, no se puede rotar

    def _get_config(self):
        """Lee el archivo de configuración general para la IA."""
        if getattr(sys, 'frozen', False):
            config_path = os.path.join(os.path.dirname(sys.executable), "settings", "config.json")
        else:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "settings", "config.json")
            
        return ConfigManager.load_json(config_path, use_lock=True).get("ai_config", {})

    def _get_safety_settings(self):
        """Consulta localmente si los filtros de seguridad deben estar activados o desactivados."""
        cfg = self._get_config()
        # Si el usuario NO habilitó la censura, apagamos los filtros de Google (BLOCK_NONE)
        if not cfg.get("enable_safety_filters", False):
            return [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        return None # Retorna None para que Google aplique su censura por defecto

    async def _perform_web_search(self, query):
        """Herramienta de Búsqueda Web Autónoma (Cascada: DDGS -> BeautifulSoup)"""
        results_str = ""
        try:
            from duckduckgo_search import DDGS
            def sync_search():
                return list(DDGS().text(query, max_results=3))
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, sync_search)
            if results:
                results_str = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')}" for r in results])
        except Exception as e:
            print(f"🧠 ⚠️ [WEB TOOL] Error DDG: {e}. Iniciando Scraping de Resiliencia...")
            try:
                from bs4 import BeautifulSoup
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://html.duckduckgo.com/html/?q={query}", headers={"User-Agent": "Mozilla/5.0"}) as resp:
                        if resp.status == 200:
                            soup = BeautifulSoup(await resp.text(), "html.parser")
                            results = []
                            for a in soup.find_all('a', class_='result__snippet')[:3]:
                                results.append(f"- {a.parent.text}")
                            results_str = "\n".join(results)
            except Exception as e2:
                print(f"🧠 ❌ [WEB TOOL] Scraping también falló: {e2}")
                
        if results_str:
            return f"[RESULTADOS DE BÚSQUEDA WEB PARA '{query}']\n{results_str}\n\nUtiliza estos datos para responder al usuario de forma natural."
        return f"[RESULTADOS DE BÚSQUEDA WEB PARA '{query}']\nLa búsqueda falló o no devolvió resultados."

    async def _route_to_ollama(self, prompt, temperature, max_tokens, system_instruction, media_data, config, use_grounding=False):
        """Traduce la petición al formato nativo de Ollama (API /chat) y la envía al servidor local."""
        endpoint = config.get("ollama_endpoint", "http://localhost:11434")
        model = config.get("ollama_model", "gemma3") # Único modelo todoterreno
        
        # Fix: Advertir si se envía imagen y el modelo configurado no es multimodal
        if media_data:
            vision_models = ["llava", "llava-llama3", "moondream", "bakllava", "minicpm-v", "gemma3"]
            is_vision_model = any(v in model.lower() for v in vision_models)
            if not is_vision_model:
                print(f"🧠 ⚠️ [OLLAMA VISION] El modelo '{model}' probablemente NO soporta imágenes. Considera usar 'llava' o 'gemma3' en la config.")
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
            
        user_msg = {"role": "user", "content": prompt}
        if media_data:
            mime_type, b64_data = media_data
            user_msg["images"] = [b64_data] # Ollama requiere el base64 limpio de la imagen
            
        messages.append(user_msg)
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "repeat_penalty": 1.1,
                "stop": ["\n[NUEVO MENSAJE", "\nTÚ (", "\n[HISTORIAL", "[TU RESPUESTA]"]
            }
        }

        if use_grounding and self.local_tools_supported:
            payload["tools"] = [{
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Busca en internet información actualizada, noticias, clima o datos que desconozcas.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Término exacto a buscar."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }]
        
        try:
            # Timeout alto (180s) para evitar cortes mientras la GPU local procesa modelos pesados
            timeout = aiohttp.ClientTimeout(total=180)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{endpoint}/api/chat", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        msg_resp = data.get("message", {})
                        
                        # --- VERIFICAR FUNCTION CALLING ---
                        if msg_resp.get("tool_calls"):
                            tool_call = msg_resp["tool_calls"][0]
                            if tool_call["function"]["name"] == "search_web":
                                query = tool_call["function"]["arguments"].get("query", "")
                                print(f"🧠 🌐 [OLLAMA TOOLS] Gemma decidió buscar en internet: '{query}'")
                                
                                search_results = await self._perform_web_search(query)
                                
                                # Inyectar resultados y realizar la segunda llamada
                                messages.append(msg_resp)
                                messages.append({"role": "tool", "content": search_results, "name": "search_web"})
                                
                                if "tools" in payload: del payload["tools"] # Evitar bucles infinitos
                                
                                async with session.post(f"{endpoint}/api/chat", json=payload) as response2:
                                    if response2.status == 200:
                                        return (await response2.json()).get("message", {}).get("content")
                                    else: return None
                                        
                        return msg_resp.get("content")
                    else:
                        err = await response.text()
                        if response.status == 400 and "does not support tools" in err:
                            if self.local_tools_supported:
                                print(f"🧠 ⚠️ [OLLAMA] El modelo '{model}' no soporta herramientas. Desactivando búsqueda autónoma local...")
                                self.local_tools_supported = False
                            if "tools" in payload:
                                del payload["tools"]
                            async with session.post(f"{endpoint}/api/chat", json=payload) as response_fallback:
                                if response_fallback.status == 200:
                                    data_fallback = await response_fallback.json()
                                    return data_fallback.get("message", {}).get("content")
                                else:
                                    err_fb = await response_fallback.text()
                                    print(f"🧠 ⚠️ [OLLAMA] Error {response_fallback.status} en reintento: {err_fb[:100]}")
                                    return None
                        print(f"🧠 ⚠️ [OLLAMA] Error {response.status}: {err[:100]}")
                        return None
        except Exception as e:
            print(f"🧠 ❌ [OLLAMA] Servidor local inalcanzable. ¿Ollama está abierto? Error: {e}")
            return None

    async def generate_content(self, model_type, prompt, temperature=0.7, max_tokens=1000, system_instruction=None, media_data=None, use_grounding=False):
        """
        Genera contenido usando el Enrutador Bilingüe.
        Recibe el tipo de tarea ('chat', 'evolution', 'memory'), el texto (prompt), la creatividad (temperature) y directrices.
        Ahora también acepta 'media_data' (tupla de mime_type y base64) para contenido multimodal (Fotos y Audio).
        """
        config = self._get_config()
        engine = config.get("ai_engine", "local") # Por defecto priorizamos Local
        
        # --- 1. RUTA LOCAL (OLLAMA / GEMMA 3) ---
        if engine == "local":
            # Fix: Si se pide grounding en local, hacer la búsqueda web manualmente
            # ANTES de enviar a Ollama, porque Ollama no siempre soporta tool_calls.
            if use_grounding and not media_data:
                # Extraer el término de búsqueda del prompt (última línea del usuario)
                search_query = prompt.split("[NUEVO MENSAJE")[-1].replace("[TU RESPUESTA]:", "").strip()
                if not search_query or len(search_query) < 3:
                    search_query = prompt[-200:].strip() # Fallback: usar el final del prompt
                print(f"🧠 🌐 [LOCAL-WEB] Inyectando búsqueda preventiva: '{search_query[:60]}'")
                web_context = await self._perform_web_search(search_query)
                prompt = f"{web_context}\n\n---\n\n{prompt}"
                use_grounding = False # Ya está inyectado, no enviar tools a Ollama

            local_resp = await self._route_to_ollama(prompt, temperature, max_tokens, system_instruction, media_data, config, use_grounding)
            if local_resp:
                return local_resp
            if not config.get("ollama_fallback", False):
                print("🧠 ❌ [ROUTER] Falló la IA Local y el Fallback a la Nube está desactivado.")
                return None
            print("🧠 ⚠️ [ROUTER] Falló la IA Local. Aplicando Fallback de emergencia a Nube (Google Gemini)...")

        # --- 2. RUTA NUBE (GOOGLE GEMINI) ---
        parts = [{"text": prompt}] # El texto principal de la petición
        
        if media_data:
            mime_type, b64_data = media_data
            parts.append({
                "inlineData": {
                    "mimeType": mime_type,
                    "data": b64_data
                }
            })

        # Construcción del 'Payload' (El paquete de datos JSON que Google exige para procesar peticiones)
        payload = {
            "contents": [{"parts": parts}], # El contenido ensamblado (Texto + Imagen)
            "generationConfig": {
                "maxOutputTokens": max_tokens, # Límite máximo de palabras a responder para no gastar cuota en respuestas infinitas
                "temperature": temperature # Nivel de alucinación/creatividad (0.0 = Robótico, 1.0 = Muy creativo/impredecible)
            }
        }
        
        if use_grounding:
            payload["tools"] = [{"googleSearch": {}}] # Inyecta la herramienta nativa de Google Search a la petición
        
        # Aplica o retira la censura dependiendo de la configuración
        safety = self._get_safety_settings()
        if safety:
            payload["safetySettings"] = safety
        
        if system_instruction: # Si hay personalidad o directrices maestras (core.py las usa)...
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]} # Las inyecta en el bloque especial del sistema

        # --- ESTRATEGIA DE ENRUTAMIENTO DE MODELOS ---
        if model_type == "chat": # Si la tarea es hablar con un humano...
            intentos_modelos = list(self.CHAT_HIERARCHY) # Copiamos la lista de Tiers de chat (para poder iterarla y modificarla si es necesario)
        else:
            # Para tareas de fondo, intentamos primero el modelo especializado (Gemma).
            # Si Gemma está saturado (503), usamos la jerarquía de chat como respaldo para no perder el recuerdo/emoción.
            fallback_model = self.CHAT_HIERARCHY[1] if len(self.CHAT_HIERARCHY) > 1 else (self.CHAT_HIERARCHY[0] if self.CHAT_HIERARCHY else "gemini-2.5-flash")
            modelo_principal = self.MODELS.get(model_type, fallback_model)
            respaldos = [m for m in self.CHAT_HIERARCHY if m != modelo_principal]
            intentos_modelos = [modelo_principal] + respaldos

        async with aiohttp.ClientSession() as session: # Abre una sesión HTTP asíncrona permanente para esta petición
            keys_snapshot = self.api_keys  # Captura la lista una vez para este ciclo
            for modelo_actual in intentos_modelos: # Bucle 1: Prueba los modelos uno por uno (Tier 1 -> Tier 2 -> Tier 3)
                modelo_exitoso = False # Bandera de estado
                
                # Bucle 2: Intenta enviar la petición tantas veces como llaves haya disponibles
                for _ in range(len(keys_snapshot) or 1): 
                    current_key = self.get_current_key() # Saca la llave activa
                    if not current_key: return None # Freno total si no hay llave

                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_actual}:generateContent?key={current_key}" # Arma el enlace hacia los servidores de Google
                    
                    try:
                        async with session.post(url, json=payload) as response: # Ejecuta el POST
                            if response.status == 200: # Código HTTP 200 = Éxito total
                                data = await response.json() # Traduce la respuesta a diccionario
                                try:
                                    # Navega por el árbol profundo de JSON de Google para extraer puramente el texto de respuesta
                                    texto = data['candidates'][0]['content']['parts'][0]['text'] 
                                    modelo_exitoso = True # Marca la victoria
                                    return texto # Devuelve el texto y rompe todos los bucles
                                except (KeyError, IndexError, TypeError): # Si el árbol JSON vino deforme...
                                    print(f"🧠 ⚠️ [AI] Respuesta vacía o bloqueada por seguridad. Detalles: {data}") # Log de la estructura rota
                                    return None # Aborta
                            
                            elif response.status == 429: # Código HTTP 429 = "Too Many Requests" (Agotaste tus mensajes por minuto)
                                print(f"🧠 ⚠️ [AI] Cuota excedida (429) en {modelo_actual}.") # Log
                                self.rotate_key() # Invoca el cambio de llave (Saca la API_KEY_2)
                                print(f"🧠 🔁 [AI] Reintentando el modelo {modelo_actual} con la nueva llave API...")
                                continue # Reinicia el "Bucle 2" forzando el reintento del mismo modelo pero con la nueva llave
                            
                            elif response.status == 503: # Código HTTP 503 = Servidores de Google colapsados
                                print(f"🧠 ⚠️ [AI] El modelo {modelo_actual} está saturado en Google (503). Intentando con otro modelo...")
                                break # Rompe el Bucle de Llaves (cambiar llave no sirve) y pasa al siguiente modelo (Bucle 1).
                            
                            else: # Cualquier otro error HTTP (500 Server Error, 404 Not Found, 400 Bad Request)
                                err = await response.text() # Lee el error crudo enviado por Google
                                # Diagnóstico específico: Si el usuario puso mal la llave en el Launcher
                                if response.status == 400 and "API key not valid" in err: 
                                    masked = current_key[:5] + "..." + current_key[-4:] if len(current_key) > 10 else "INVALID" # Censura la llave por privacidad
                                    print(f"🧠 ❌ [AI] LLAVE INVÁLIDA (400): La llave '{masked}' fue rechazada.") # Alerta humana
                                else:
                                    print(f"🧠 ⚠️ [AI] Error API {response.status}: {err[:100]}") # Alerta técnica truncada
                                break # Error fatal e irrecuperable de este modelo. Rompe el Bucle de Llaves y pasa al siguiente modelo (Bucle 1).
                                
                    except Exception as e: # Si no hay internet o el servidor de Google está completamente caído
                        print(f"🧠 ❌ [AI] Error de conexión: {e}") 
                        break # Salta al siguiente modelo
                
                # --- PENALIZACIÓN DE MODELOS ---
                # Si recorrimos todas las llaves y el modelo actual nunca pudo responder (por colapso total de cuotas)...
                if not modelo_exitoso and model_type == "chat" and modelo_actual in self.CHAT_HIERARCHY: 
                    print(f"🧠 📉 [AI] El modelo {modelo_actual} se agotó. Se ignorará temporalmente para agilizar respuestas.") # Log
                    self.CHAT_HIERARCHY.remove(modelo_actual) # ¡Lo borramos de la lista! Así, el siguiente mensaje en Discord pasará directo al Tier 2 sin perder 3 segundos esperando al Tier 1 roto.
                    
        return None # Si todos los modelos y todas las llaves fallaron, la IA queda en silencio y retorna Nada.

    def clean_json_response(self, text):
        """
        Herramienta de limpieza.
        Gemini frecuentemente devuelve los datos encerrados en bloques de código Markdown (ej: ```json {...} ```).
        Esta función los destruye para que `json.loads` de Python no colapse con un error de sintaxis.
        """
        if not text: return "{}"
        # Extracción quirúrgica: Busca únicamente lo que esté entre llaves {}
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end >= start:
            return text[start:end+1]
        return "{}"

# Instancia global: Patrón Singleton para mantener el seguimiento unificado de las rotaciones de llaves en toda la sesión
ai_manager = AIManager()