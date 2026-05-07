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


### QoL y Mejoras 

### 📌 Tarea 19: Selector de Idioma Dinámico en Interfaz
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  Actualmente el sistema soporta i18n y lee `"language": "es"` desde el `config.json`, pero no existe ningún control visual para cambiarlo. Se debe añadir esta opción en el panel para evitar ediciones manuales del JSON. Dado que varias vistas de configuración leen el archivo `outputs_{lang}.json` basado en el idioma cargado en memoria al arrancar, cambiar el idioma en caliente sin reiniciar podría causar escrituras cruzadas de diccionarios. Se requiere exigir un reinicio de la aplicación tras el cambio.
  - **Archivos a modificar y dependencias:**
    - `settings/locales/es.json` (y `en.json`): Añadir las traducciones (`cfg_gen_language`, `cfg_gen_help_language`, `msg_restart_title`, `msg_restart_required`).
    - `views/config/general_view.py`: 
      - Dependencias: Importar `from tkinter import messagebox`.
      - Clase `GeneralConfigFrame`: Crear el helper `add_option_row(label, key, source, options, help_txt)` que implemente un `CTkComboBox` con los valores disponibles. Inyectar la fila de idioma justo antes de "Token de Discord".
      - Método `save_general_config`: Recuperar el nuevo idioma desde el widget. Antes de finalizar, comparar el nuevo idioma guardado con `self.controller.lang_code`. Si difieren, lanzar `messagebox.showinfo` bloqueante pidiendo un reinicio manual de la UI.

- **Checklist de Implementación:**
  - [x] `settings/locales/es.json` (y `en.json`): Añadir las nuevas claves de texto.
  - [x] `views/config/general_view.py`: Importar `from tkinter import messagebox`.
  - [x] `views/config/general_view.py`: Crear la función auxiliar `add_option_row` dentro de `__init__`.
  - [x] `views/config/general_view.py`: Añadir la fila de configuración para `language` usando `add_option_row`.
  - [x] `views/config/general_view.py`: Modificar `save_general_config` para capturar y guardar el idioma en `config.json`.
  - [x] `views/config/general_view.py`: Añadir condicional en `save_general_config` para disparar el popup de reinicio si el idioma cambió.

### 📌 Tarea 20: Asistente de Configuración Inicial (Wizard)
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  Actualmente, un usuario nuevo puede sentirse perdido al abrir la aplicación si no sabe que debe ir primero a "Configuración General" a poner su Token. Se requiere implementar un "Wizard" (Asistente paso a paso) de bienvenida que bloquee el acceso al Dashboard principal hasta que las variables críticas (`DISCORD_TOKEN`, Idioma y Tema) estén configuradas (estableciendo "dark" por defecto para el tema).
  - **Archivos a modificar y dependencias:**
    - `launcher.py`: 
      - Método `__init__`: Añadir lógica para leer `dotenv_values(ENV_PATH).get("DISCORD_TOKEN")`. Si está vacío o es nulo, invocar `self.show_frame(WizardView)` en lugar de `DashboardFrame`.
      - Método `__init__`: Ocultar la barra lateral (`self.sidebar_frame.grid_remove()`) si el Wizard está activo para evitar fugas de navegación.
      - Nuevo Método `finish_wizard()`: Restaurar la barra lateral (`grid()`), recargar la instancia de `LanguageManager` por si el usuario cambió el idioma, y redirigir al `DashboardFrame`.
    - `views/guides/wizard_view.py`: 
      - (Archivo Nuevo) Crear la clase `WizardView(ctk.CTkFrame)` con un diseño secuencial (paso 1: Idioma y Tema Visual, paso 2: Token de Discord y Admin ID).
      - Importar y usar `dotenv.set_key` para guardar las credenciales ingresadas directamente a disco.
    - `settings/locales/es.json` (y `en.json`): 
      - Inyectar las nuevas claves de traducción necesarias para la UI del Wizard (ej: `wizard_title`, `wizard_step_1`, `wizard_theme`, `wizard_btn_next`, `wizard_finish`).

- **Checklist de Implementación:**
  - [x] `settings/locales/es.json` (y `en.json`): Añadir las claves de texto del Wizard.
  - [x] `views/guides/wizard_view.py`: Crear el archivo y desarrollar la lógica de UI por pasos, integrando el selector de temas.
  - [x] `launcher.py`: Importar `WizardView` de forma compatible con carga perezosa.
  - [x] `launcher.py`: Modificar el `__init__` para evaluar el `DISCORD_TOKEN` ocultando `sidebar_frame` si no existe.
  - [x] `launcher.py`: Implementar `finish_wizard()` para reactivar la barra lateral y recargar el controlador de idioma.
  - [x] `settings/.env`: Eliminar el token manualmente en el entorno de desarrollo para comprobar el bloqueo de la UI.

### 📌 Tarea 21: Restricción de Canal para Módulo de Música
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  Actualmente, los comandos de música pueden ser invocados en cualquier canal de texto, lo que genera spam de respuestas (Now playing, Queued, etc.) y ensucia las conversaciones generales. Se requiere independizar la variable `MUSIC_CHANNEL_ID` para que el bot bloquee los comandos musicales si no se ejecutan en su canal designado.
  - **Archivos a modificar y dependencias:**
    - `build.py`: 
      - `create_clean_dist_files()`: Inyectar `MUSIC_CHANNEL_ID=\n` en la constante `.env` virgen.
    - `views/config/general_view.py`: En `GeneralConfigFrame.__init__`, añadir el widget `add_gen_row` para el nuevo canal de música.
    - `cogs/music.py`: Añadir un `cog_check(self, ctx)` global en la clase `Music` que cancele la ejecución si `os.getenv("MUSIC_CHANNEL_ID")` está configurado y el canal del comando no coincide.
    - `settings/locales/es.json` (y `en.json`): Añadir los textos de interfaz (`cfg_gen_music_id`, `cfg_gen_help_music_id`) y el mensaje de error del bot (`cmd_music_wrong_channel`).

- **Checklist de Implementación:**
  - [x] `build.py`: Añadir inyección de `MUSIC_CHANNEL_ID` en `env_content`.
  - [x] `settings/locales/es.json` (y `en.json`): Agregar las claves de idiomas correspondientes.
  - [x] `views/config/general_view.py`: Añadir el widget visual para `MUSIC_CHANNEL_ID`.
  - [x] `cogs/music.py`: Agregar comprobación global (`cog_check`) para bloquear la invocación de comandos musicales en canales ajenos.

### 📌 Tarea 22: Ampliación de Personalidades Prefabricadas
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  La IA solo trae una personalidad "Neutral" por defecto. Se requiere implementar un nuevo Wizard de Primer Arranque exclusivo para el módulo de IA que permita elegir una personalidad prefabricada viendo un resumen y sus detalles. Es crucial que cada personalidad prefabricada defina **sus propios estados de ánimo y sus propios rangos de afinidad**, ya que la forma en que la IA demuestra "odio" o "amor" debe ir estrictamente ligada a su identidad (ej. una Tsundere no expresa afecto igual que un Asistente Formal). Además, la vista actual de `ai_amnesia_view.py` se debe refactorizar para separar claramente "Cambiar Personalidad" (con casillas modulares) de "Limpiar Memoria" (borrado de usuarios, hechos). Todo alimentado desde un nuevo gestor unificado `shared/presets.py`.
  - **Archivos a modificar y dependencias:**
    - `shared/presets.py`: (Archivo Nuevo) Contendrá los perfiles (Neutral, Tsundere, Gamer). Cada perfil incluirá `summary`, `identity`, `guidelines`, `estados_posibles`, `autoconcepto` (gustos por defecto) y `afinidad_rangos`.
    - `settings/config.json`: Añadir y gestionar la bandera `"ai_first_run": true`.
    - `views/guides/ai_wizard_view.py`: (Archivo Nuevo) Wizard que obligue a elegir un preset al entrar a la configuración de IA por primera vez.
    - `launcher.py`: En `render_main_sidebar` o en `open_ai_menu`, interceptar la navegación si `ai_first_run` es verdadero, mostrando `AIWizardView`.
    - `build.py`: Limpiar constantes, importar desde `shared/presets.py` e inyectar `"ai_first_run": true` en el entorno virgen.
    - `views/config/ai_amnesia_view.py`: Dividir en dos secciones visuales: 1) Cambiar Personalidad (Selector de preset, visualización de resumen y checkboxes modulares para aplicar solo lo deseado). 2) Limpiar Memoria (Borrado de usuarios, opiniones, hechos y reseteo de prompts).
    - `settings/locales/es.json` (y `en.json`): Agregar traducciones del nuevo Wizard de IA y de la vista dividida de amnesia.

- **Checklist de Implementación:**
  - [x] `shared/presets.py`: Crear el archivo extrayendo la personalidad Neutral base como prueba estructural.
  - [x] `build.py`: Consumir `presets.py` para construir archivos vírgenes e inyectar `"ai_first_run": true` en `config.json`.
  - [x] `settings/locales/es.json` (y `en.json`): Añadir los textos de interfaz para el AI Wizard.
  - [x] `views/guides/ai_wizard_view.py`: Programar el nuevo asistente con previsualización detallada de la personalidad elegida.
  - [x] `launcher.py`: Implementar el bloqueo/redirección hacia el AI Wizard la primera vez que se hace clic en la sección de IA.
  - [x] `views/config/ai_amnesia_view.py`: Refactorizar la UI para tener "Cambiar Personalidad" (modular) y "Limpiar Memoria/Sistema" (borrado).
  - [x] `views/config/ai_amnesia_view.py`: Implementar la lógica de "Aplicar Personalidad" para que sobreescriba solo las casillas marcadas e invoque el IPC.

### 📌 Tarea 23: Expansión de Temas Visuales y Colores Custom
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  El ThemeManager actual está parcialmente hardcodeado en `launcher.py` para cargar siempre `"dark"`. Añadir más temas base y una herramienta de personalización de colores HEX permite adaptar la interfaz a los gustos específicos de cada servidor. El Asistente de Configuración Inicial (Tarea 20) permitirá elegir el tema durante el primer arranque, estableciendo `"dark"` por defecto. Para cambios posteriores en el panel de configuración, la estrategia más robusta será guardar el nuevo tema y exigir un reinicio de la aplicación.
  - **Archivos a modificar y dependencias:**
    - `launcher.py`: Modificar el método `__init__` para que lea `config.json` *antes* de instanciar `ThemeManager`, inyectando `config_data.get("theme", "dark")` en lugar del `"dark"` estático.
    - `shared/theme_manager.py`: Añadir método `get_available_themes()` para escanear la carpeta `themes/` dinámicamente (excluyendo el archivo base para la UI), y `save_custom_theme()` para escribir `themes/custom.json`.
    - `themes/`: Crear físicamente los archivos prefabricados `light.json` y `midnight.json`.
    - `views/config/general_view.py`: Implementar un `CTkOptionMenu` alimentado por `ThemeManager.get_available_themes()`. Añadir una sección "Editor Custom" que itere las 10 claves de colores requiriendo valores HEX. Todo campo debe validarse con Regex (ej: `^#(?:[0-9a-fA-F]{3}){1,2}$`) para evitar crasheos fatales en Tkinter.
    - `settings/locales/es.json` (y `en.json`): Nuevas claves para la UI (`cfg_gen_theme`, `cfg_gen_theme_editor`, `msg_restart_theme`, `err_invalid_hex`).

- **Checklist de Implementación:**
  - [ ] `themes/`: Crear físicamente los archivos base `light.json` y `midnight.json`.
  - [ ] `launcher.py`: Modificar el `__init__` para inyectar el tema desde `config.json` en lugar del `"dark"` estático.
  - [ ] `shared/theme_manager.py`: Añadir métodos de lectura dinámica de directorio y guardado custom.
  - [ ] `settings/locales/es.json` (y `en.json`): Añadir claves de texto para la nueva interfaz.
  - [ ] `views/config/general_view.py`: Integrar `CTkOptionMenu` que guarde la variable temática.
  - [ ] `views/config/general_view.py`: Añadir la interfaz de edición HEX validando datos con Regex.
  - [ ] `views/config/general_view.py`: Implementar el popup de aviso de reinicio al cambiar de colores visuales.

### 📌 Tarea 24: Ecualizador y Efectos de Sonido (Música)
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  Mejorar la experiencia auditiva añadiendo opciones de ecualizador (Bass Boost) o efectos (Nightcore, Vaporwave). Estos efectos requieren enviar el flag `-af` a FFmpeg. Dado que es un bot de instancia única (Self-Hosted para un solo servidor principal), no es necesario aislar los efectos por servidor; la configuración de EQ será global para toda la instancia. Además, el protocolo IPC musical del Launcher debe actualizarse para soportar enviar argumentos arbitrarios (como el nombre del efecto).
  - **Archivos a modificar y dependencias:**
    - `launcher.py`: Modificar el método `send_music_cmd(self, action, arg=None)` para que admita un argumento opcional explícito en el payload, y así poder enviar el estado del ComboBox de EQ.
    - `views/music/main_view.py`: Añadir un `CTkOptionMenu` en `controls_frame` con perfiles de EQ (Normal, Nightcore, BassBoost, Vaporwave) conectado a `send_music_cmd("eq", valor)`.
    - `cogs/music.py`: 
      - `__init__`: Añadir `self.active_eq = "Normal"` como estado global de la instancia (o persistirlo en `config.json`).
      - `get_ffmpeg_options()`: Modificar para que lea `self.active_eq`. Si hay un efecto activo distinto a "Normal", concatenarlo en la clave `options` (ej: `options += ' -af atempo=1.2,asetrate=44100*1.25'`).
      - `ipc_invoke()`: Añadir `"eq"` al mapa de comandos válidos.
      - Crear el comando `@commands.command(name="eq")` que actualice `self.active_eq` globalmente y emita un mensaje notificando que el efecto se aplicará en la próxima canción.
    - `settings/locales/es.json` (y `en.json`): Nuevas claves para la interfaz (`mus_lbl_eq`, `mus_eq_normal`, `mus_eq_nightcore`) y para los mensajes del bot (`cmd_eq_changed`).

- **Checklist de Implementación:**
  - [ ] `launcher.py`: Refactorizar el método `send_music_cmd` para aceptar el parámetro opcional `arg`.
  - [ ] `settings/locales/es.json` (y `en.json`): Añadir claves de traducción para la vista de efectos.
  - [ ] `views/music/main_view.py`: Integrar el menú desplegable `CTkOptionMenu` para perfiles EQ.
  - [ ] `cogs/music.py`: Declarar la variable de estado global `active_eq` e implementar el comando `@commands.command(name="eq")`.
  - [ ] `cogs/music.py`: Mapear el comando `music_eq` en la función de enrutamiento IPC `ipc_invoke`.
  - [ ] `cogs/music.py`: Modificar la compilación en `get_ffmpeg_options` para inyectar las directivas de filtros (`-af`).

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

  