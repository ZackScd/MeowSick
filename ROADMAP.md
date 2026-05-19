# ROADMAP - MeowSick V3

---

## 📋 Guía de Estructuración de Tareas (Plantilla para Desarrolladores y LLMs)

> **Propósito:** Para mantener el orden y facilitar el desarrollo asistido por IA, cada nueva tarea añadida a este ROADMAP debe seguir rigurosamente la siguiente estructura. Esto asegura que el contexto, los problemas a resolver y las instrucciones de código estén perfectamente delimitadas.

### 📌 Tarea [Número]: [Nombre descriptivo de la Tarea]
- **Fase de Análisis Previo (Obligatorio):**

  - **Detalles, Problema y Mejoras:** 
  Explica aquí detalladamente cuál es el problema actual que se busca resolver, la deuda técnica identificada o la nueva característica a implementar. Describe cómo mejorará el sistema una vez aplicada la tarea.

  > 🛑 **ANTES de iniciar la tarea o proponer código**, se debe realizar una búsqueda exhaustiva en todo el proyecto para identificar todas las dependencias involucradas. Se deben listar los archivos, bloques y líneas de código exactas que se verán impactadas y requerirán actualización.

  - **Archivos a modificar y dependencias:**

  > 🛑 **IMPORTANTE**, Se debe listar cada archivo por separado, y en él incluir una lista de todos los cambios que incluya

    - `ruta/archivo_1.ext`: Especificar la Clase y Función exacta (ej: `def setup()` en la línea 45) que recibirá los cambios.
    - `ruta/archivo_2.ext`: Indicar si hay JSONs, variables u otros módulos que dependan de esta alteración y deban actualizarse en cascada.

- **Checklist de Implementación:**
  *(Debe ser un listado completo, detallado y atomizado. Cada línea DEBE iniciar especificando el archivo a modificar)*
  - [ ] `ruta/archivo_1.ext`: Acción específica 1 (ej: "Crear la nueva función de parseo").
  - [ ] `ruta/archivo_1.ext`: Acción específica 2 (ej: "Reemplazar X por Y en la línea Z").
  - [ ] `ruta/archivo_2.ext`: Acción específica 3 (ej: "Actualizar la interfaz para reflejar los cambios").

---


# Estructura de archivos actual

```text
MeowSick/
├── launcher.py                 # Punto de entrada de la UI gráfica (CustomTkinter). Muy reducido post-refactorización.
├── meowSick.py                 # Punto de entrada del Bot de Discord (Proceso asíncrono)
├── build.py                    # Script de compilación (PyInstaller) para empaquetado standalone
├── README.md                   # Documentación principal
├── ROADMAP.md                  # Plan de refactorización y hoja de ruta
├── completeTask.md             # Historial de tareas y fases de refactorización completadas
│
├── shared/                     # [Módulos Compartidos] Código reutilizable entre el Launcher y el Bot
│   ├── __init__.py
│   ├── config_manager.py       # Gestor centralizado de lectura/escritura JSON (D.R.Y)
│   ├── theme_manager.py        # Carga dinámica de paletas de colores desde themes/
│   ├── language_manager.py     # Sistema de internacionalización (i18n), carga strings desde locales/
│   └── presets.py              # [NUEVO] Gestor de personalidades prefabricadas
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
│   │   ├── ai_engine_view.py
│   │   └── ai_amnesia_view.py    # Renombrado: "Personalidad y Reseteo"
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
│       ├── local_guide_view.py
│       ├── wizard_view.py          # [NUEVO] Asistente de configuración inicial
│       └── ai_wizard_view.py       # [NUEVO] Asistente de personalidad de IA
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

### QoL y Mejoras 

### 📌 Tarea 24: Ecualizador y Efectos de Sonido (Música)
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  Mejorar la experiencia auditiva añadiendo opciones de ecualizador (Bass Boost) o efectos (Nightcore, Vaporwave). Estos efectos requieren enviar el flag `-af` a FFmpeg. Dado que es un bot de instancia única (Self-Hosted para un solo servidor principal), no es necesario aislar los efectos por servidor; la configuración de EQ será global para toda la instancia. Además, el protocolo IPC musical del Launcher debe actualizarse para soportar enviar argumentos arbitrarios (como el nombre del efecto).
  - **Archivos a modificar y dependencias:**
    - `launcher.py`: Modificar el método `send_music_cmd(self, action, arg=None)` para que admita un argumento opcional explícito en el payload, y así poder enviar el estado del ComboBox de EQ.
    - `views/music/main_view.py`: Añadir un `CTkOptionMenu` en `controls_frame` con perfiles de EQ (Normal, Nightcore, BassBoost, Vaporwave, ultra-saturado) conectado a `send_music_cmd("eq", valor)`.
    - `cogs/music.py`: 
      - `__init__`: Añadir `self.active_eq = "Normal"` como estado global de la instancia (o persistirlo en `config.json`).
      - `get_ffmpeg_options()`: Modificar para que lea `self.active_eq`. Si hay un efecto activo distinto a "Normal", concatenarlo en la clave `options` (ej: `options += ' -af atempo=1.2,asetrate=44100*1.25'`).
      - `ipc_invoke()`: Añadir `"eq"` al mapa de comandos válidos.
      - Crear el comando `@commands.command(name="eq")` que actualice `self.active_eq` globalmente y emita un mensaje notificando que el efecto se aplicará en la próxima canción.
    - `settings/locales/es.json` (y `en.json`): Nuevas claves para la interfaz (`mus_lbl_eq`, `mus_eq_normal`, `mus_eq_nightcore`, `mus_eq_satured`) y para los mensajes del bot (`cmd_eq_changed`).

- **Checklist de Implementación:**
  - [x] `launcher.py`: Refactorizar el método `send_music_cmd` para aceptar el parámetro opcional `arg`.
  - [x] `settings/locales/es.json` (y `en.json`): Añadir claves de traducción para la vista de efectos.
  - [x] `views/music/main_view.py`: Integrar el menú desplegable `CTkOptionMenu` para perfiles EQ.
  - [x] `cogs/music.py`: Declarar la variable de estado global `active_eq` e implementar el comando `@commands.command(name="eq")`.
  - [x] `cogs/music.py`: Mapear el comando `music_eq` en la función de enrutamiento IPC `ipc_invoke`.
  - [x] `cogs/music.py`: Modificar la compilación en `get_ffmpeg_options` para inyectar las directivas de filtros (`-af`).

### 📌 Tarea 25: Reorganización de Configuraciones (Básico vs Avanzado)
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  El panel de `ai_settings_view.py` es actualmente un marco desplazable masivo ("scroll de la muerte") que abruma al usuario con demasiadas opciones apiladas. Se requiere refactorizar esta vista utilizando un componente `CTkTabview` para agrupar lógicamente la configuración en pestañas (Ej: "Comportamiento", "Multimodal", "Avanzado"). Además, se debe realizar una auditoría general de `config.json` para cazar variables huérfanas.
  - **Archivos a modificar y dependencias:**
    - `views/config/ai_settings_view.py`: 
      - Reemplazar el `scroll = ctk.CTkScrollableFrame(...)` base por un `self.tabview = ctk.CTkTabview(...)`.
      - Crear 3 pestañas: "General", "Multimodal" y "Avanzado", e insertar un `CTkScrollableFrame` dentro de cada una.
      - Redistribuir los bloques de código existentes: "Filtros" va a General; "Voz (TTS)" y "Búsqueda Web" van a Multimodal; "Valores Mágicos" y "Almacenamiento" van a Avanzado.
    - `settings/locales/es.json` (y `en.json`): Añadir las traducciones para las nuevas pestañas (`tab_ai_behavior`, `tab_ai_multimodal`, `tab_ai_advanced`).
    - `settings/config.json`: Realizar una revisión cruzada para verificar que parámetros como `enable_safety_filters` u `ollama_fallback` sigan teniendo representación en la UI.

- **Checklist de Implementación:**
  - [ ] `settings/locales/es.json` (y `en.json`): Añadir las claves de traducción para las pestañas ("Básico", "Avanzado", etc.).
  - [ ] `views/config/ai_settings_view.py`: Instanciar y configurar el layout con `CTkTabview` en el `__init__`.
  - [ ] `views/config/ai_settings_view.py`: Mover los marcos existentes (`filt_card`, `tts_card`, etc.) hacia sus pestañas respectivas.
  - [ ] `views/config/ai_settings_view.py`: Validar la integridad de los métodos `load_ai_settings_ui` y `save_ai_settings` post-migración.
  - [ ] `settings/config.json`: Auditar y emparejar controles gráficos para cualquier llave huérfana de `ai_config`.

  