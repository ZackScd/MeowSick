# ROADMAP - MeowSick V3

# Estructura de archivos actual

```text
MeowSick/
├── launcher.py                 # Punto de entrada de la UI gráfica (CustomTkinter). Muy reducido post-refactorización.
├── meowSick.py                 # Punto de entrada del Bot de Discord (Proceso asíncrono)
├── build.py                    # Script de compilación (PyInstaller) para empaquetado standalone
├── README.md                   # Documentación principal
├── ROADMAP.md                  # Plan de refactorización y hoja de ruta
├── CHANGELOG.md                # Registro de cambios y versiones
│
├── shared/                     # [Módulos Compartidos] Código reutilizable entre el Launcher y el Bot
│   ├── __init__.py
│   ├── config_manager.py       # Gestor centralizado de lectura/escritura JSON (D.R.Y)
│   ├── theme_manager.py        # Carga dinámica de paletas de colores desde themes/
│   └── language_manager.py     # Sistema de internacionalización (i18n), carga strings desde locales/
│
├── views/                      # [Vistas UI] Archivos modulares de la interfaz gráfica (Lazy Loading)
│   ├── __init__.py
│   ├── dashboard_view.py       # Clase DashboardFrame
│   ├── modules_view.py         # Clase ModulesFrame
│   ├── music/                  # Vistas específicas del reproductor
│   │   ├── __init__.py
│   │   └── main_view.py        # Clase MusicFrame (Panel principal de música)
│   ├── config/                 # Vistas de configuración y ajustes
│   │   ├── __init__.py
│   │   ├── general_view.py
│   │   ├── music_view.py
│   │   ├── ai_general_view.py
│   │   ├── ai_settings_view.py
│   │   ├── ai_engine_view.py   # Renombrado: "Núcleo Cognitivo (Motor)"
│   │   └── ai_presets_view.py  # Nueva: "Personalidades Prefabricadas"
│   ├── ai/                     # Editores visuales de Memoria y Personalidad
│   │   ├── __init__.py
│   │   ├── identity_editor.py
│   │   ├── moods_editor.py
│   │   ├── moods_history_editor.py
│   │   ├── users_editor.py
│   │   ├── memory_editor.py
│   │   ├── opinions_editor.py
│   │   ├── ranges_editor.py
│   │   ├── self_editor.py
│   │   └── prompts_editor.py
│   └── guides/                 # Interfaces de las guías de ayuda integradas
│       ├── __init__.py
│       ├── discord_guide_view.py
│       ├── google_guide_view.py
│       ├── id_guide_view.py
│       ├── privacy_guide_view.py
│       └── local_guide_view.py
│
├── themes/                     # [Temas Visuales] Paletas de colores en JSON
│   └── dark.json               # Tema oscuro por defecto (migrado desde el dict COLORS de launcher.py)
│
├── settings/                   # [Datos de Usuario] Configuraciones locales
│   ├── config.json             # Ajustes globales, estados de toggles, límites, language y theme
│   ├── outputs.json            # Textos personalizables de los mensajes del bot
│   ├── .env                    # Tokens y API Keys (Discord, Google AI, etc.)
│   └── locales/                # Sistema de internacionalización
│       ├── es.json             # Strings en Español
│       └── en.json             # Strings en Inglés
│
├── cogs/                       # [Backend] Módulos operacionales del Bot
│   ├── help.py                 # Comando de ayuda nativo
│   ├── music.py                # Motor asíncrono de audio, colas y descargas (yt-dlp)
│   └── AI/                     # [Ecosistema Cognitivo de IA]
│       ├── core.py             # Lóbulo Frontal (Chat, Visión, Búsqueda web)
│       ├── memory.py           # Hipocampo (Extracción de hechos, juicios sociales, autoconcepto)
│       ├── evolution.py        # Sistema Límbico (Análisis de humor pasivo y decaimiento)
│       ├── identity.py         # Gestor dinámico de personalidad e inyección de contexto
│       ├── utils.py            # Módem de red y llamadas a API (Gemini / Ollama) + AIManager
│       ├── tts_manager.py      # [Nuevo] Abstracción del motor TTS (Edge-TTS, Piper, etc.)
│       ├── stt_manager.py      # [Nuevo] Abstracción del motor STT (Whisper, Gemini Audio, etc.)
│       └── memory/             # [Base de Datos RAG Local] Archivos dinámicos de la IA
│           ├── identity.txt
│           ├── guidelines.txt
│           ├── known_users.json
│           ├── memoria.json
│           ├── opiniones.json
│           ├── afinidad_rangos.json
│           ├── autoconcepto.json
│           ├── estado_animo.json
│           ├── historial_estados.json
│           ├── estados_posibles.json
│           └── prompts.json
│
├── logs/                       # [Sistema de Logging] Registros de eventos y errores
│   └── system.log              # Log con rotación automática (generado en runtime)
│
└── res/                        # [Recursos Estáticos]
    ├── img/                    # Íconos, avatares y logos (.ico, .png)
    └── ffmpeg/                 # Binarios de codificación de audio (ffmpeg.exe)
```


### Fase 6: QoL y Mejoras Futuras (Post-Refactorización)

#### Checklist de Progreso - Fase 6

- [ ] **Tarea 19: Asistente de Configuración Inicial (Wizard)**
  - [ ] Crear pantalla de bienvenida bloqueante para el primer arranque.
  - [ ] Forzar configuración de Idioma, Token, Admin ID y canales básicos.

- [ ] **Tarea 20: Comando `!config` vía Discord**
  - [ ] Crear comando restringido a `ADMIN_ID` para configuraciones remotas.
  - [ ] Extraer y separar variables de canal compartidas (crear `MUSIC_CHANNEL_ID` en lugar de reusar `WELCOME_CHANNEL_ID`).