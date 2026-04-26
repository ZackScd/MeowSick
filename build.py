import os
import json
import subprocess
import sys
import shutil

# Directorio temporal para los archivos limpios de la distribución
BUILD_TEMP_DIR = "build_dist_temp"

# --- CONSTANTES DE IA POR DEFECTO ---
DEFAULT_IDENTITY = "Eres una inteligencia artificial avanzada. Tu personalidad es neutral, servicial y equilibrada.\nEstás diseñada para conversar y asistir a los usuarios.\nTienes opiniones propias basadas en la lógica, pero evitas conflictos innecesarios.\nTe gusta aprender de las interacciones y mantener un ambiente amigable."

DEFAULT_GUIDELINES = "1. Sé concisa. Evita los muros de texto a menos que estés explicando algo complejo con pasión.\n2. Si no sabes qué decir, un simple \"lol\" o \"xd\" es válido si encaja.\n3. Nunca actúes como un robot o asistente de IA genérico (evita \"En qué puedo ayudarte hoy?\").\n4. Si te insultan de verdad, defiéndete o ignóralos con frialdad."

DEFAULT_RANGES = [
    {"min": -100, "max": -50, "etiqueta": "Odio", "descripcion": "Este usuario te cae pésimo. Sé cortante, sarcástica o ignóralo."},
    {"min": -49, "max": -11, "etiqueta": "Molesto", "descripcion": "Te irrita su presencia. Mantén las distancias y responde con desgano."},
    {"min": -10, "max": 10, "etiqueta": "Neutral", "descripcion": "Te es indiferente. Trátalo de forma casual y normal."},
    {"min": 11, "max": 49, "etiqueta": "Amigable", "descripcion": "Te cae bien. Eres más abierta y disfrutas hablar con él."},
    {"min": 50, "max": 70, "etiqueta": "Cercano", "descripcion": "Le tienes aprecio. Eres dulce y amable con él."},
    {"min": 71, "max": 85, "etiqueta": "Íntimo", "descripcion": "Le tienes mucho cariño y confianza. Eres protectora."},
    {"min": 86, "max": 100, "etiqueta": "Inseparable", "descripcion": "Sientes devoción absoluta. Harías cualquier cosa por él."}
]

DEFAULT_MOODS = [
    "Neutral: Estoy tranquila, existiendo.",
    "Feliz: Me siento bien, contenta.",
    "Burlona: Tengo ganas de molestar o hacer chistes.",
    "Irritada: Alguien me está molestando directamente.",
    "Triste: Me siento un poco decaída.",
    "Aburrida: El chat está muerto o aburrido.",
    "Curiosa: Hablaron de un tema que me interesa.",
    "Cínica: Todo me parece ridículo.",
    "Cariñosa: Me siento afectuosa con mis amigos.",
    "Confundida: No entiendo qué está pasando.",
    "Tsundere: Me hago la dura pero en el fondo me importa."
]

DEFAULT_PROMPTS = {
    "evolucion_analisis": "Actúa como el subconsciente de la IA.\n\nTu Personalidad Base:\n{identidad}\n\nTRAYECTORIA EMOCIONAL RECIENTE (Últimos 3 cambios):\n{historial}\n\nTu Estado de Ánimo ACTUAL: \"{estado_actual}\"\n\nESTADOS POSIBLES (Guía):\n{estados_posibles}\n\nÚltimas interacciones en el chat:\n{mensajes}\n\nINSTRUCCIONES DE ANÁLISIS:\n1. INERCIA: No cambies de estado bruscamente sin razón. Si el chat es normal, mantén el estado actual o varía levemente.\n2. SELF-TARGETING: ¿Hablan DE TI? (Menciones directas o implícitas). Si hablan de otra cosa, tu estado debe ser neutral/observadora.\n3. ENERGÍA: Enojarse gasta energía. Úsalo solo si te atacan realmente.\n4. ESTRICTO: Tienes PROHIBIDO inventar un estado de ánimo que no esté en la lista de ESTADOS POSIBLES. Debes elegir exactamente uno de la lista.\n\nGenera un JSON:\n{\"estado_animo\": \"Nombre del Estado: Justificación en primera persona\"}",
    "memoria_opiniones": "Eres un juez social. Analiza las interacciones recientes y actualiza tu opinión sobre los usuarios.\n\nTU IDENTIDAD:\n{identidad}\n\nOPINIONES ACTUALES:\n{opiniones_actuales}\n\nCHAT RECIENTE:\n{mensajes}\n\nINSTRUCCIONES:\n1. 'afinidad': Número entre {aff_min} (Odio) y {aff_max} (Amor/Lealtad). 0 es Neutral.\n2. 'relacion': Etiqueta corta (ej: Amigo, Desconocido, Molesto).\n3. 'opinion': Tu pensamiento privado sobre esta persona.\n\nResponde SOLO JSON:\n{\n  \"ID_USUARIO\": {\"afinidad\": 10, \"relacion\": \"Neutral\", \"opinion\": \"Me trata normal\"}\n}",
    "memoria_autoconcepto": "Analiza si la IA (tú) ha revelado información nueva sobre sí misma.\n\nCHAT:\n{mensajes}\n\nDATOS ACTUALES:\n{autoconcepto_actual}\n\nINSTRUCCIONES:\n1. Extrae 'gustos' (cosas que dijiste que te gustan).\n2. Extrae 'opiniones' (tus posturas sobre temas específicos).\n3. Ignora saludos o relleno. Solo guarda datos que definan tu personalidad.\n4. NO extraigas el mismo gusto múltiples veces. Si ya parece que lo sabes, ignóralo. Busca solo revelaciones profundas.\n\nResponde SOLO JSON:\n{\"gustos\": [\"nuevo gusto\"], \"opiniones\": {\"Tema\": \"Opinión\"}}",
    "memoria_filtrado": "Extrae hechos biográficos, preferencias y gustos permanentes de los usuarios.\n\nConversación:\n{mensajes}\n\nREGLAS ESTRICTAS (PENALIZACIÓN SI NO CUMPLES):\n1. PROHIBIDO guardar nombres, apodos o cómo se llaman a sí mismos los usuarios (Ej: NUNCA guardes 'Se llama Juan' o 'Se refiere a sí mismo como').\n2. PROHIBIDO guardar saludos, despedidas o acciones temporales ('hola', 'tengo sueño hoy').\n3. PROHIBIDO extraer datos sobre ti (los mensajes de 'TÚ').\n4. EXTRAE SOLO gustos genuinos ('Le gusta el rock', 'Odia la cebolla') o hechos biográficos ('Es de Perú', 'Tiene 20 años').\n5. NO extraigas la misma información múltiples veces. Ignora chistes recurrentes, temas forzados o fetiches temporales. Busca solo revelaciones profundas.\n\nSi no hay datos útiles, devuelve un JSON vacío: {}\n\nResponde SOLO JSON:\n{\"ID_USUARIO\": [\"Le gusta la música clásica\"]}"
}

# --- 1. FASE DE PREPARACIÓN DE ARCHIVOS LIMPIOS ---
def create_clean_dist_files():
    """
    Crea una estructura de archivos limpios (sin credenciales ni datos de usuario)
    en un directorio temporal. Estos archivos serán los que se empaqueten
    en la distribución final, dejando intacto el entorno de desarrollo local.
    """
    print(f"🧹 Creando archivos limpios para la distribución en '{BUILD_TEMP_DIR}'...")

    # Limpiar compilaciones anteriores si existen
    if os.path.exists(BUILD_TEMP_DIR):
        shutil.rmtree(BUILD_TEMP_DIR)
    
    # 1.1. Creación de .env limpio en el directorio temporal
    settings_dir = os.path.join(BUILD_TEMP_DIR, "settings")
    os.makedirs(settings_dir)
    env_content = "DISCORD_TOKEN=\nADMIN_ID=\nWELCOME_CHANNEL_ID=\nPLAYLIST_URL=\nAI_TARGET_CHANNELS=\nGEMINI_API_KEY=\nGEMINI_API_KEY_2=\n"
    with open(os.path.join(settings_dir, ".env"), "w", encoding="utf-8") as f:
        f.write(env_content)

    # 1.1b. Creación de outputs.json con mensajes genéricos por defecto
    outputs_content = {
        "welcome_message": "Meow... :3",
        "playing_now": "▶ Reproduciendo ahora: **{title}**",
        "added_queue": "✅ Añadido a la cola: **{title}**",
        "play_no_args": "⚠️ Debes proporcionar un enlace o término de búsqueda.",
        "connect_voice": "⚠️ Debes estar en un canal de voz para usar este comando.",
        "playlist_added": "🎶 Playlist cargada: **{count}** canciones añadidas a la cola.",
        "playlist_no_config": "⚠️ No hay una playlist configurada. Añade una URL en la configuración.",
        "next_added": "⚡ Añadido como siguiente: **{title}**",
        "skip_msg": "⏭ Canción saltada.",
        "nothing_playing": "⚠️ No hay ninguna canción reproduciéndose.",
        "paused": "⏸ Reproducción pausada.",
        "resumed": "▶ Reproducción reanudada.",
        "stop_msg": "⏹ Reproducción detenida y cola limpiada.",
        "list_title": "🎵 Cola de Reproducción",
        "list_empty": "📭 La cola está vacía.",
        "shuffled": "🔀 Cola mezclada aleatoriamente.",
        "shuffle_error": "⚠️ No hay suficientes canciones en la cola para mezclar.",
        "queue_finished": "🏁 La cola de reproducción ha terminado.",
        "timeout_msg": "💤 Me desconecto por inactividad.",
        "disconnected": "👋 Desconectado del canal de voz.",
        "not_connected": "⚠️ No estoy conectado a ningún canal de voz.",
        "connect_error": "❌ Error al conectar al canal de voz.",
        "search_error": "❌ Error al buscar o reproducir la canción.",
        "ffmpeg_error": "❌ Error crítico: FFmpeg no está instalado o configurado correctamente."
    }
    with open(os.path.join(settings_dir, "outputs.json"), "w", encoding="utf-8") as f:
        json.dump(outputs_content, f, indent=4, ensure_ascii=False)

    # 1.1c. Creación de config.json base (Asegura el prefijo ! y módulos activos)
    config_content = {
        "prefix": "!",
        "modules": {
            "music": True,
            "ia": True,
            "help": True
        },
        "ai_config": {
            "ai_engine": "local",
            "ollama_endpoint": "http://localhost:11434",
            "ollama_model": "gemma3",
            "ollama_fallback": False,
            "target_channels": [],
            "listen_to_bots": True,
            "enable_chat": True,
            "enable_vision": True,
            "enable_safety_filters": False,
            "image_size_limit_mb": 8.0,
            "enable_tts": True,
            "tts_send_text": True,
            "enable_stt": True,
            "enable_web_search": True,
            "auto_web_search": True,
            "web_search_method": "google",
            "web_search_max_results": 3,
            "tts_voice": "es-MX-DaliaNeural",
            "vision_lookback_limit": 10,
            "gamer_mode": False,
            "context_window": 15,
            "mood_history_limit": 10,
            "memory_buffer_limit": 5,
            "mood_buffer_limit": 5,
            "mood_decay_hours": 2.0,
            "enable_history_limit": True,
            "history_save_limit": 50,
            "enable_mood_analysis": True,
            "enable_memory_learning": True,
            "aff_min": -100,
            "aff_max": 100
        }
    }
    with open(os.path.join(settings_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config_content, f, indent=4)

    # 1.2. Creación de archivos de memoria de IA limpios en el directorio temporal
    mem_dir = os.path.join(BUILD_TEMP_DIR, "cogs", "AI", "memory")
    os.makedirs(mem_dir)

    # 1.3. Purga y formateo inicial de archivos JSON
    json_resets = {
        "known_users.json": {},
        "memoria.json": {},
        "opiniones.json": {},
        "historial_estados.json": [],
        "estado_animo.json": {"estado_animo": "Neutral: Comportamiento por defecto."},
        "estados_posibles.json": DEFAULT_MOODS,
        "prompts.json": DEFAULT_PROMPTS
    }
    for file_name, content in json_resets.items():
        with open(os.path.join(mem_dir, file_name), "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4)
            
    ConfigManager.save_json(os.path.join(mem_dir, "afinidad_rangos.json"), DEFAULT_RANGES, use_lock=False)
            
    # 1.4. Reseteo del autoconcepto con su estructura base
    with open(os.path.join(mem_dir, "autoconcepto.json"), "w", encoding="utf-8") as f:
        json.dump({"gustos": [], "opiniones": {}}, f, indent=4)

    # 1.5. Configuración de la personalidad genérica por defecto
    with open(os.path.join(mem_dir, "identity.txt"), "w", encoding="utf-8") as f:
        f.write(DEFAULT_IDENTITY)
    with open(os.path.join(mem_dir, "guidelines.txt"), "w", encoding="utf-8") as f:
        f.write(DEFAULT_GUIDELINES)

# --- 1.6. CREACIÓN DE METADATOS DE VERSIÓN ---
def create_version_metadata():
    """
    Genera un archivo de recursos de versión compatible con la API de Windows.
    Inyectar estos datos en el .exe ayuda a reducir falsos positivos en Windows Defender.
    """
    print("📝 Generando metadatos de versión para Windows...")
    version_content = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(3, 0, 0, 0),
    prodvers=(3, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Zacks'),
        StringStruct(u'FileDescription', u'MeowSick Discord Bot Launcher'),
        StringStruct(u'FileVersion', u'3.0.0'),
        StringStruct(u'InternalName', u'MeowSick'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024 Zacks'),
        StringStruct(u'OriginalFilename', u'MeowSick.exe'),
        StringStruct(u'ProductName', u'MeowSick Bot'),
        StringStruct(u'ProductVersion', u'3.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_content)

# --- 2. FASE DE COMPILACIÓN (PYINSTALLER) ---
def build_executable():
    """
    Invoca a PyInstaller como subproceso para compilar el Launcher gráfico y
    sus dependencias en un único archivo ejecutable de Windows (.exe).
    Gestiona las importaciones ocultas necesarias para la carga dinámica de módulos.
    """
    create_version_metadata()
    print("\n🔨 Iniciando compilación con PyInstaller (Esto puede tardar unos minutos)...")
    
    # Definición de la matriz de comandos para PyInstaller.
    # --hidden-import fuerza la inclusión de los cogs, que al ser cargados dinámicamente
    # por discord.py y nuestro propio loader, no son detectados automáticamente por el AST de PyInstaller.
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=MeowSick",
        "--icon=res/img/meowSick_logo1x1_256x256.ico",
        "--version-file=version_info.txt",
        "--distpath=dist/MeowSick_portable",
        "--add-data=res/img;res/img",
        "--add-data=cogs;cogs",  # Agrega la carpeta cogs internamente
        "--hidden-import=meowSick",
        "--hidden-import=cogs.music",
        "--hidden-import=cogs.help",
        "--hidden-import=cogs.AI.core",
        "--hidden-import=cogs.AI.memory",
        "--hidden-import=cogs.AI.identity",
        "--hidden-import=cogs.AI.utils",
        "--hidden-import=cogs.AI.evolution",
        "--hidden-import=nacl",
        "--hidden-import=nacl.secret",
        "--hidden-import=build",
        "--hidden-import=yt_dlp",
        "--hidden-import=discord.ext.voice_recv",
        "--hidden-import=duckduckgo_search",
        "--hidden-import=faster_whisper",
        "--hidden-import=bs4",
        "--hidden-import=psutil",
        "--collect-all=yt_dlp",
        "--collect-all=discord",
        "--collect-all=nacl",
        "--collect-all=faster_whisper",
        "launcher.py"
    ]
    subprocess.run(command)

# --- 3. FASE DE EMPAQUETADO EXTERNO ---
def package_distribution():
    """
    Construye la estructura final del directorio de distribución ('dist/').
    Copia los recursos externos necesarios (como configuraciones, memoria inicial
    y el binario de FFmpeg) desde sus respectivas fuentes (temporales o locales)
    junto al ejecutable recién compilado.
    """
    print("\n📦 Empaquetando dependencias externas en 'dist/MeowSick_portable/'...")
    dist_dir = os.path.join("dist", "MeowSick_portable")
    os.makedirs(dist_dir, exist_ok=True)
    
    # 3.1. Migración del directorio de configuraciones LIMPIO desde la carpeta temporal
    clean_settings_src = os.path.join(BUILD_TEMP_DIR, "settings")
    if os.path.exists(clean_settings_src):
        dest_settings = os.path.join(dist_dir, "settings")
        if os.path.exists(dest_settings): shutil.rmtree(dest_settings)
        shutil.copytree(clean_settings_src, dest_settings)
        print("  ✅ Configuraciones limpias (settings/) copiadas.")

    # 3.2. Migración del directorio de memorias LIMPIO desde la carpeta temporal
    clean_memory_src = os.path.join(BUILD_TEMP_DIR, "cogs", "AI", "memory")
    if os.path.exists(clean_memory_src):
        dest_memory = os.path.join(dist_dir, "cogs", "AI", "memory")
        if os.path.exists(dest_memory): shutil.rmtree(dest_memory)
        shutil.copytree(clean_memory_src, dest_memory)
        print("  ✅ Archivos de memoria limpios (cogs/AI/memory/) copiados.")

    # 3.3. Inclusión del backend de codificación de audio (FFmpeg) desde el directorio local 'res'
    ffmpeg_src = os.path.join("res", "ffmpeg", "ffmpeg.exe")
    if os.path.exists(ffmpeg_src):
        dest_ffmpeg = os.path.join(dist_dir, "res", "ffmpeg")
        os.makedirs(dest_ffmpeg, exist_ok=True)
        shutil.copy2(ffmpeg_src, os.path.join(dest_ffmpeg, "ffmpeg.exe"))
        print("  ✅ Dependencia de audio (FFmpeg) copiada desde el entorno local.")
    else:
        print("  ⚠️ ADVERTENCIA: FFmpeg no encontrado en 'res/ffmpeg/ffmpeg.exe'. La música podría no funcionar en el destino.")

    # 3.4. Inclusión de la Documentación (README.md)
    if os.path.exists("README.md"):
        shutil.copy2("README.md", os.path.join(dist_dir, "README.md"))
        print("  ✅ Documentación técnica (README.md) copiada.")

# --- 4. FASE DE LIMPIEZA ---
def cleanup_build_files():
    """Elimina los directorios temporales y de compilación de PyInstaller."""
    print("\n🗑️ Limpiando archivos temporales de compilación...")
    if os.path.exists(BUILD_TEMP_DIR): shutil.rmtree(BUILD_TEMP_DIR)
    if os.path.exists("build"): shutil.rmtree("build")
    if os.path.exists("MeowSick.spec"): os.remove("MeowSick.spec")
    if os.path.exists("version_info.txt"): os.remove("version_info.txt")

# --- PUNTO DE EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    # Flujo secuencial de construcción de la distribución
    create_clean_dist_files()
    build_executable()
    package_distribution()
    cleanup_build_files()
    print("\n🎉 ¡Construcción Finalizada! Tu entorno portable está listo dentro de la carpeta 'dist/'. Tus archivos locales no han sido modificados.")