import os
import sys
import json
from shared.config_manager import ConfigManager

class IdentityModule:
    """
    Gestor de Identidad y Registro de Usuarios.
    Administra los archivos de texto estáticos que definen quién es la IA (identity, guidelines)
    y mantiene el diccionario base de personas conocidas (conocidos, admins, creador).
    """
    def __init__(self):
        # Resolución de rutas: Se adapta si el código está compilado en .exe o si corre como .py
        if getattr(sys, 'frozen', False): 
            self.base_path = os.path.join(os.path.dirname(sys.executable), "cogs", "AI", "memory") # Ruta en entorno compilado
        else: 
            self.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory") # Ruta en entorno de desarrollo local
            
        self.users_file = os.path.join(self.base_path, "known_users.json") # Base de datos de todos los que han hablado
        self.identity_file = os.path.join(self.base_path, "identity.txt") # Personalidad base
        self.guidelines_file = os.path.join(self.base_path, "guidelines.txt") # Reglas estrictas de comportamiento
        
        self._ensure_files() # Asegura que nada falle si el usuario borró los archivos por accidente
        
    def _ensure_files(self):
        """Crea las carpetas y archivos por defecto en el primer inicio de la IA."""
        os.makedirs(self.base_path, exist_ok=True) # Crea la carpeta 'memory'
        if not os.path.exists(self.users_file): 
            self._save_users({}) # Crea el JSON de usuarios vacío
        
        # Archivos de texto plano para fácil edición manual o por interfaz
        if not os.path.exists(self.identity_file): 
            with open(self.identity_file, "w", encoding="utf-8") as f:
                f.write("Eres un asistente virtual. Tienes tu propia personalidad, responde de forma natural y conversacional.")
        
        if not os.path.exists(self.guidelines_file):
            with open(self.guidelines_file, "w", encoding="utf-8") as f:
                f.write("1. Sé breve.\n2. No uses emojis excesivamente.")
                
        self.rangos_file = os.path.join(self.base_path, "afinidad_rangos.json") # Base de datos de escalas emocionales
        if not os.path.exists(self.rangos_file): 
            # Si no hay rangos configurados, inyectamos una escala de odio-amor por defecto
            defaults = [
                {"min": -100, "max": -50, "etiqueta": "Odio", "descripcion": "Este usuario te cae pésimo. Sé cortante, sarcástica o ignóralo."},
                {"min": -49, "max": -11, "etiqueta": "Molesto", "descripcion": "Te irrita su presencia. Mantén las distancias y responde con desgano."},
                {"min": -10, "max": 10, "etiqueta": "Neutral", "descripcion": "Te es indiferente. Trátalo de forma casual y normal."},
                {"min": 11, "max": 49, "etiqueta": "Amigable", "descripcion": "Te cae bien. Eres más abierta y disfrutas hablar con él."},
                {"min": 50, "max": 100, "etiqueta": "Cercano", "descripcion": "Le tienes mucho aprecio o cariño. Sé dulce y protectora."}
            ]
            ConfigManager.save_json(self.rangos_file, defaults, use_lock=False)

    def _load_users(self):
        """Carga el diccionario estático de usuarios desde el disco."""
        data = ConfigManager.load_json(self.users_file, use_lock=False)
        return data if isinstance(data, dict) else {}

    def _save_users(self, data):
        """Guarda el diccionario de usuarios en disco con formato legible (indent=4)."""
        ConfigManager.save_json(self.users_file, data, use_lock=False)

    def get_identity_block(self):
        """
        Ensambla y devuelve el bloque maestro de identidad.
        Junta quién es la IA (identity.txt) con sus reglas inquebrantables (guidelines.txt).
        """
        identidad = "" # Variable temporal para el núcleo de personalidad
        guidelines = "" # Variable temporal para reglas
        try:
            with open(self.identity_file, "r", encoding="utf-8") as f: identidad = f.read() # Lee texto de personalidad
            with open(self.guidelines_file, "r", encoding="utf-8") as f: guidelines = f.read() # Lee texto de reglas
        except: pass
        
        config_path = os.path.abspath(os.path.join(self.base_path, "..", "..", "..", "settings", "config.json"))
        cfg = ConfigManager.load_json(config_path, use_lock=True) or {}
        lang_code = cfg.get("language", "es")
        lang_name = "ESPAÑOL (Spanish)" if lang_code == "es" else "ENGLISH"
        
        return f"[SYSTEM DIRECTIVE: You must process thoughts and communicate exclusively in {lang_name}]\n\n{identidad}\n\n[DIRECTRICES]\n{guidelines}"

    def register_user_if_new(self, user):
        """
        Escáner pasivo (hook): Se llama cada vez que alguien manda un mensaje.
        Si el usuario nunca había hablado, le abre un expediente en blanco en la base de datos.
        """
        users = self._load_users() # Trae toda la agenda
        uid = str(user.id) # Asegura que la ID de Discord se use como String (Llave de JSON)
        
        admin_id = os.getenv("ADMIN_ID") # Revisa quién es el dueño actual en el .env
        dev_id = "690953562930282526"  # ID inamovible (El creador original del código)
        
        if uid not in users: # ¿Es la primera vez que veo a esta persona?
            rol = "Usuario" # Rol genérico por defecto
            relacion = "Conocido. Relación neutral." # Estatus inicial neutro
            
            if uid == dev_id: # ¿Es el desarrollador original (Zacks)?
                rol = "Creador / Desarrollador" # Otorga estatus máximo de deidad
                relacion = "Tu creador absoluto y quien programó tu código base." # Inyecta respeto eterno
            elif admin_id and uid == str(admin_id): # ¿Es la persona que está hosteando el bot localmente?
                rol = "Administrador" # Otorga estatus de amo/host
                relacion = "El administrador que hospeda y controla esta instancia." # Le enseña que él paga las cuentas
                
            users[uid] = { # Crea la tarjeta de registro
                "nombre": user.display_name,
                "rol_base": rol,
                "relacion": relacion
            }
            self._save_users(users) # Guarda en disco
            print(f"🧠 📝 [IDENTITY] Nuevo usuario registrado: {user.display_name} ({rol})") # Avisa en consola

    def get_user_context(self, user_id, opinions_data):
        """
        Cruza la ficha estática (known_users) con la opinión dinámica.
        Prioridad: Opinión Dinámica > Ficha Base.
        Genera el párrafo que le dice a la IA con quién demonios está hablando en ese instante.
        """
        users = self._load_users() # Carga la ficha policial
        uid = str(user_id) # Aísla el objetivo
        
        base_info = users.get(uid, {"nombre": "Desconocido", "rol_base": "Usuario", "relacion": ""}) # Busca su ficha estática
        context_str = f"- Nombre: {base_info.get('nombre')}. Rol Base: {base_info.get('rol_base')}." # Prepara la introducción básica
        
        if base_info.get("relacion"): # Si hay relación base apuntada en su ficha...
            context_str += f" Descripción/Relación: {base_info.get('relacion')}" # ...se le añade al resumen
        
        # Inyección de opinión dinámica (Del módulo Memory)
        if uid in opinions_data: # ¿La IA ya formó su propia opinión viva sobre este sujeto?
            op = opinions_data[uid] # Extrae el diccionario emocional vivo
            afinidad = op.get("afinidad", 0) # Qué tanto le agrada numéricamente (-100 a 100)
            relacion_dinamica = op.get("relacion", "Neutral") # Estado en una palabra
            opinion = op.get("opinion", "") # El párrafo profundo que escribió la IA juzgándolo
            
            # Sobrescribe y añade la memoria sentimental real al contexto del prompt de Gemini
            context_str += f"\n  >>> [MEMORIA EMOCIONAL / REAL]\n  Estado Actual: {relacion_dinamica} (Afinidad: {afinidad}%).\n  Tu opinión secreta: '{opinion}'." 
            
            # Instrucción de comportamiento basada en afinidad
            rangos_file = os.path.join(self.base_path, "afinidad_rangos.json") # Lee los niveles configurados en el Launcher
            matched_rango = None # Puntero para guardar si encajamos en algún rango
            rangos = ConfigManager.load_json(rangos_file, use_lock=False)
            if isinstance(rangos, list):
                for r in rangos: # Revisa uno por uno
                    if r.get("min", -100) <= afinidad <= r.get("max", 100): # ¿La afinidad del usuario cabe en este margen?
                        matched_rango = r # ¡Rango encontrado!
                        break # Detiene la búsqueda
            
            if matched_rango: # Si se emparejó exitosamente con un nivel de afinidad personalizado...
                # Le dice a la IA exactamente cómo debe actuar hacia ese usuario
                context_str += f"\n  (Instrucción por afinidad [{matched_rango.get('etiqueta', '')}]: {matched_rango.get('descripcion', '')})" 
            else:
                # Sistema de respaldo por si el archivo de rangos falla o se borra
                if afinidad < -20: context_str += "\n  (Instrucción: Este usuario te cae mal. Sé cortante o sarcástica)."
                elif afinidad > 60: context_str += "\n  (Instrucción: Este usuario te agrada mucho. Sé cariñosa o más abierta)."
        
        # Admin / Dev override
        admin_id = os.getenv("ADMIN_ID") # Saca la ID de Host actual
        dev_id = "690953562930282526" # <-- ID inamovible del Creador Original (Easter Eggs o backdoor de lealtad)
        
        if uid == dev_id: # Si quien escribió el mensaje es el Dev
            context_str += "\n  >>> [SISTEMA] ALERTA: ESTE ES TU DESARROLLADOR ORIGINAL. Creador de tu código. Trátalo con máxima reverencia." # Alerta roja en el prompt
        elif admin_id and uid == str(admin_id): # Si quien escribió es el dueño del Server Host
            context_str += "\n  >>> [SISTEMA] ALERTA: ESTE ES EL ADMINISTRADOR DEL BOT. Obedece sus comandos y respeta estrictamente sus reglas y límites." # Inyecta subyugación al dueño
            
        return context_str # Devuelve el párrafo con el perfil psicológico y social que la IA debe tener hacia quien acaba de hablar

# Instancia global: Al instanciar aquí, aseguramos que exista una única copia de 'identity' persistente en toda la sesión del bot (Patrón Singleton)
identity_manager = IdentityModule() 