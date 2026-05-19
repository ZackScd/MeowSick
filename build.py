import os
import json
import subprocess
import sys
import shutil

from shared.presets import AI_PRESETS

# Directorio temporal para los archivos limpios de la distribución
BUILD_TEMP_DIR = "build_dist_temp"

# --- CONSTANTES DE SALIDA (MENSAJES) POR DEFECTO ---
DEFAULT_OUTPUTS_ES = {
    "welcome_message": "¡Hola! He despertado y estoy listo.",
    "playing_now": "🎵 Reproduciendo ahora: **{title}**",
    "added_queue": "✅ Añadido a la cola: **{title}**",
    "play_no_args": "⚠️ Dime qué quieres que busque.",
    "connect_voice": "⚠️ Necesitas estar en un canal de voz.",
    "playlist_added": "✅ Playlist cargada. {count} canciones añadidas.",
    "playlist_no_config": "⚠️ No has configurado una Playlist Especial en el Launcher.",
    "next_added": "⚡ Se reproducirá a continuación: **{title}**",
    "skip_msg": "⏭️ Canción saltada.",
    "nothing_playing": "⚠️ No hay nada sonando ahora mismo.",
    "paused": "⏸️ Música pausada.",
    "resumed": "▶️ Música reanudada.",
    "stop_msg": "⏹️ Música detenida y cola vaciada.",
    "list_title": "🎵 Cola de Reproducción",
    "list_empty": "La cola está vacía.",
    "list_footer": "Página {page}/{total} | Total: {len}",
    "shuffled": "🔀 Cola mezclada aleatoriamente.",
    "shuffle_error": "⚠️ No hay suficientes canciones para mezclar.",
    "queue_finished": "✅ No hay más canciones en la cola.",
    "timeout_msg": "💤 Me desconecto por inactividad.",
    "disconnected": "🚪 Me he desconectado del canal de voz.",
    "not_connected": "⚠️ No estoy conectado a ningún canal.",
    "connect_error": "❌ Error al conectar al canal de voz.",
    "search_error": "❌ No pude encontrar resultados o hubo un error.",
    "ffmpeg_error": "❌ Error crítico: No se encontró FFmpeg en el sistema."
}

DEFAULT_OUTPUTS_EN = {
    "welcome_message": "Hello! I am online and ready.",
    "playing_now": "🎵 Now playing: **{title}**",
    "added_queue": "✅ Added to queue: **{title}**",
    "play_no_args": "⚠️ Tell me what to search for.",
    "connect_voice": "⚠️ You need to be in a voice channel.",
    "playlist_added": "✅ Playlist loaded. {count} songs added.",
    "playlist_no_config": "⚠️ You haven't configured a Special Playlist in the Launcher.",
    "next_added": "⚡ Playing next: **{title}**",
    "skip_msg": "⏭️ Track skipped.",
    "nothing_playing": "⚠️ Nothing is playing right now.",
    "paused": "⏸️ Music paused.",
    "resumed": "▶️ Music resumed.",
    "stop_msg": "⏹️ Music stopped and queue cleared.",
    "list_title": "🎵 Music Queue",
    "list_empty": "The queue is empty.",
    "list_footer": "Page {page}/{total} | Total: {len}",
    "shuffled": "🔀 Queue shuffled randomly.",
    "shuffle_error": "⚠️ Not enough songs to shuffle.",
    "queue_finished": "✅ No more songs in the queue.",
    "timeout_msg": "💤 Disconnected due to inactivity.",
    "disconnected": "🚪 Disconnected from the voice channel.",
    "not_connected": "⚠️ I am not connected to any channel.",
    "connect_error": "❌ Error connecting to voice channel.",
    "search_error": "❌ Could not find results or an error occurred.",
    "ffmpeg_error": "❌ Critical error: FFmpeg not found in the system."
}

# --- CONSTANTES DE IA POR DEFECTO ---
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
    env_content = "DISCORD_TOKEN=\nADMIN_ID=\nWELCOME_CHANNEL_ID=\nMUSIC_CHANNEL_ID=\nPLAYLIST_URL=\nAI_TARGET_CHANNELS=\nGEMINI_API_KEY=\nGEMINI_API_KEY_2=\n"
    with open(os.path.join(settings_dir, ".env"), "w", encoding="utf-8") as f:
        f.write(env_content)

    # 1.1a. Copiar archivos de idiomas y temas visuales
    if os.path.exists(os.path.join("settings", "locales")):
        shutil.copytree(os.path.join("settings", "locales"), os.path.join(settings_dir, "locales"))
        
        # Sanitizar mensajes privados del bot (Evita fuga de textos personalizados del desarrollador)
        with open(os.path.join(settings_dir, "locales", "outputs_es.json"), "w", encoding="utf-8") as f:
            json.dump(DEFAULT_OUTPUTS_ES, f, indent=4)
        with open(os.path.join(settings_dir, "locales", "outputs_en.json"), "w", encoding="utf-8") as f:
            json.dump(DEFAULT_OUTPUTS_EN, f, indent=4)
        
    if os.path.exists("themes"):
        shutil.copytree("themes", os.path.join(BUILD_TEMP_DIR, "themes"))
        
    os.makedirs(os.path.join(BUILD_TEMP_DIR, "logs"), exist_ok=True)

    # 1.1b. Configuración Base 100% Limpia
    # Generada completamente desde cero para evitar que CUALQUIER ajuste local del desarrollador
    # (como API keys sueltas en config, canales, límites de ventana, etc) se filtre a los usuarios finales.
    config_content = {
        "language": "es",
        "theme": "dark",
        "prefix": "!",
        "owner_id": 0,
        "queue_page_limit": 10,
        "modules": {
            "music": True, 
            "ia": True, 
            "help": True
        },
        "music_config": {
            "inactivity_sleep": 60,
            "max_retries": 3,
            "view_timeout": 60,
            "ytdl_options": {},
            "ffmpeg_options": {}
        },
        "ai_config": {
            "ai_engine": "local",
            "ollama_endpoint": "http://localhost:11434",
            "ollama_model": "gemma3",
            "fallback_to_cloud": False,
            "target_channels": [],
            "listen_to_bots": False,
            "enable_chat": True,
            "enable_vision": True,
            "enable_tts": True,
            "tts_engine": "edge-tts",
            "tts_voice": "",
            "enable_rvc": False,
            "tts_send_text": True,
            "enable_stt": True,
            "enable_web_search": True,
            "auto_web_search": True,
            "web_search_method": "google",
            "web_search_max_results": 3,
            "gamer_mode": False,
            "gamer_limit": 5,
            "ai_first_run": True,
            "context_window": 15,
            "mood_eval_buffer": 5,
            "mood_history_limit": 10,
            "memory_buffer_limit": 5,
            "image_size_limit_mb": 8.0,
            "vision_lookback_limit": 10,
            "decay_hours": 2.0,
            "disk_history_limit": 50,
            "spontaneous_prob": 0.05,
            "cooldown": 3.0,
            "repetition_penalty": 1.1,
            "ai_timeout": 180,
            "enable_safety_filters": True
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
        "estados_posibles.json": AI_PRESETS["neutral"]["estados_posibles"],
        "prompts.json": DEFAULT_PROMPTS,
        "afinidad_rangos.json": AI_PRESETS["neutral"]["afinidad_rangos"]
    }
    for file_name, content in json_resets.items():
        with open(os.path.join(mem_dir, file_name), "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4)
            
    # 1.4. Reseteo del autoconcepto con su estructura base
    with open(os.path.join(mem_dir, "autoconcepto.json"), "w", encoding="utf-8") as f:
        json.dump(AI_PRESETS["neutral"]["autoconcepto"], f, indent=4)

    # 1.5. Configuración de la personalidad genérica por defecto
    with open(os.path.join(mem_dir, "identity.txt"), "w", encoding="utf-8") as f:
        f.write(AI_PRESETS["neutral"]["identity"])
    with open(os.path.join(mem_dir, "guidelines.txt"), "w", encoding="utf-8") as f:
        f.write(AI_PRESETS["neutral"]["guidelines"])

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
        "--hidden-import=cogs.AI.tts_manager",
        "--hidden-import=cogs.AI.stt_manager",
        "--hidden-import=nacl",
        "--hidden-import=nacl.secret",
        "--hidden-import=filelock",
        "--hidden-import=build",
        "--hidden-import=yt_dlp",
        "--hidden-import=discord.ext.voice_recv",
        "--hidden-import=duckduckgo_search",
        "--hidden-import=faster_whisper",
        "--hidden-import=bs4",
        "--hidden-import=psutil",
        "--hidden-import=shared",
        "--hidden-import=views",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=edge_tts",
        "--hidden-import=dotenv",
        "--hidden-import=aiohttp",
        "--collect-all=yt_dlp",
        "--collect-all=discord",
        "--collect-all=nacl",
        "--collect-all=filelock",
        "--collect-all=faster_whisper",
        "--collect-all=shared",
        "--collect-all=views",
        "--collect-all=themes",
        "--collect-all=customtkinter",
        "--collect-all=edge_tts",
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

    # 3.1b. Migración de Temas y creación de Logs en la Distribución
    clean_themes_src = os.path.join(BUILD_TEMP_DIR, "themes")
    if os.path.exists(clean_themes_src):
        dest_themes = os.path.join(dist_dir, "themes")
        if os.path.exists(dest_themes): shutil.rmtree(dest_themes)
        shutil.copytree(clean_themes_src, dest_themes)
        print("  ✅ Temas visuales (themes/) copiados.")
        
    os.makedirs(os.path.join(dist_dir, "logs"), exist_ok=True)
    print("  ✅ Directorio de registros (logs/) creado.")

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