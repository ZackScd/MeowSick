# ROADMAP de Refactorización - MeowSick V3

Este documento describe el plan de acción para refactorizar el archivo `launcher.py`, que ha crecido a más de 3000 líneas y presenta problemas de rendimiento y mantenibilidad.

> **📝 Recordatorio:** Todos los cambios, refactorizaciones y nuevas implementaciones realizadas durante este proceso deben ser registrados detalladamente en el archivo **`CHANGELOG.md`**.

---

## 1. Problema Actual

- **"God Object"**: El archivo `launcher.py` contiene toda la lógica de la interfaz gráfica, convirtiéndose en un "objeto dios" difícil de navegar y modificar.
- **Rendimiento de la UI**: La aplicación crea **todos** los widgets de **todas** las ventanas al iniciarse. Esto causa:
  - Un tiempo de arranque más lento.
  - Tirones o parpadeos ("flickering") al cambiar entre pestañas, ya que Tkinter debe recalcular la geometría de cientos de elementos.
- **Escalabilidad**: Añadir nuevas ventanas o modificar las existentes es propenso a errores y complica el código innecesariamente.
- **Textos Hardcodeados**: Los textos de la interfaz (títulos, botones, mensajes, descripciones) están incrustados directamente en el código de la UI. Esto ensucia la lógica, dificulta las modificaciones y hace imposible cambiar el idioma de la aplicación.
- **Deuda Técnica de JSON**: Las funciones `_get_config()` y `_load_json()` están duplicadas en **seis archivos** (`launcher.py`, `meowSick.py`, `music.py`, `memory.py`, `evolution.py`, `utils.py`). Cualquier cambio en la lógica de lectura/escritura debe replicarse manualmente en cada uno.
- **Variables de Entorno Frágiles**: Las credenciales (tokens, API keys) se leen y escriben mediante funciones manuales (`load_env_dict`, `update_env_key`) que parsean el `.env` a mano, lo cual es destructivo y propenso a corrupción del archivo.
- **IPC Frágil**: La comunicación entre el Launcher y el Bot se basa en el parseo de strings con prefijos (`IPC_PROGRESS:`, `CMD_MUSIC:`). Un `print` accidental en cualquier punto del bot puede romper silenciosamente la interfaz gráfica.

---

## 2. Objetivo de la Refactorización

- **Modularización**: Dividir la interfaz en componentes lógicos (vistas/páginas), donde cada uno reside en su propio archivo.
- **Rendimiento**: Implementar **"Carga Perezosa" (Lazy Loading)**. Las vistas solo se crearán en memoria la primera vez que el usuario haga clic en su respectivo botón, mejorando drásticamente el tiempo de arranque y la fluidez.
- **Mantenibilidad**: Simplificar `launcher.py` para que actúe solo como un controlador principal, facilitando la depuración y la adición de nuevas características.
- **Internacionalización (i18n)**: Extraer todos los strings y textos de la interfaz hacia diccionarios externos (`.json`). Esto separará la vista de los datos y dejará la aplicación preparada para el soporte multi-idioma.
- **Eliminación de Deuda Técnica**: Centralizar la lectura/escritura de JSON, la gestión de variables de entorno y el protocolo IPC en módulos únicos y reutilizables.

---

## 3. Estructura de Archivos Final (Post-Refactorización)

La arquitectura resultante separará estrictamente la interfaz gráfica (MVC), el backend del bot (Cogs), los datos persistentes del usuario y los módulos compartidos entre procesos.

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
│   ├── config/                 # Vistas de configuración
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
│   └── guides/                 # Interfaces de las guías de ayuda
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

---

## 4. Plan de Acción (Paso a Paso)

> **⚠️ Importante**: El orden de ejecución es vital. Primero construiremos los cimientos centrales (Gestores de Configuración, Tema e Idioma). De esta forma, al momento de extraer las vistas a nuevos archivos, ya insertaremos el código limpio usando estos gestores, evitando tener que re-editar decenas de archivos en el futuro.

---

### Fase 1: Cimientos y Resolución de Deuda Técnica (Core)

#### Paso 1: Centralización del Gestor de Estado (D.R.Y)

**Problema confirmado:** Las funciones `_get_config()` / `_load_json()` / `save_data()` están duplicadas en **seis archivos**: `launcher.py`, `meowSick.py`, `music.py`, `memory.py`, `evolution.py` y `utils.py`. Cualquier cambio en la lógica de persistencia debe replicarse manualmente en todos ellos.

1. Crear el módulo `shared/config_manager.py` con métodos seguros `load_json(path)` y `save_json(path, data)`.
2. **Estrategia de bloqueo diferenciada:**
   - Para `config.json` y `outputs.json` (escritos tanto por el Launcher como por el Bot): usar `filelock` con un timeout bajo (ej. `timeout=1.0`) para bloqueo real multi-proceso. Si el lock no se obtiene, reintentar o loguear el conflicto en lugar de fallar silenciosamente.
   - Para los archivos de memoria de la IA (`memoria.json`, `opiniones.json`, `autoconcepto.json`, `estado_animo.json`, `historial_estados.json`): **NO envolver con `filelock` desde el Launcher**. Estos archivos ya están protegidos por el worker pattern de `asyncio.Queue` dentro del bot (`_memory_worker`, `_evolution_worker`). Añadir `filelock` encima introduciría riesgo de deadlock si el worker sostiene el lock en el momento en que el Launcher intenta acceder. La UI del Launcher solo debe leer estos archivos, nunca escribirlos mientras el bot esté activo.
3. Reemplazar todas las funciones locales duplicadas en los seis archivos por llamadas a `shared/config_manager.py`.

> **⚠️ Nota sobre el Singleton `AIManager`:** `utils.py` exporta `ai_manager = AIManager()` como Singleton global. Al recargar un Cog (`CMD_RELOAD`), si el módulo no se reimporta completamente, el Singleton puede retener el estado de keys anterior. Esto está parcialmente mitigado por la `@property` lazy de `api_keys`, pero al migrar al `ConfigManager` asegurarse de que `_get_config()` dentro de `AIManager` sea reemplazado por `config_manager.load_json()` **sin cachear el resultado**, para que siempre refleje el archivo en disco.

#### Paso 2: Extracción de Temas y Estilos Visuales

El diccionario `COLORS` está fuertemente acoplado dentro de `launcher.py`.

1. Crear la carpeta `themes/` y un archivo `dark.json` que contenga la paleta de colores actual.
2. Crear la clase `ThemeManager` en `shared/theme_manager.py` que lea este archivo y provea los colores de forma dinámica.

#### Paso 3: Sistema Base de Idiomas (i18n)

1. Crear la carpeta `settings/locales/` y el archivo base `es.json` (Español) con todos los strings de la UI extraídos del código actual.
2. Crear la clase `LanguageManager` en `shared/language_manager.py` que cargue el JSON del idioma configurado en `config.json` y provea un método `get(key)` para inyectar los strings.
3. **Internacionalización del Bot (`outputs.json`)**: Migrar `outputs.json` a `settings/locales/outputs_es.json` y `outputs_en.json`. Ajustar el Launcher y los Cogs (`music.py`) para leer/escribir en el archivo que corresponda al idioma activo.
4. **Idioma de la IA**: Inyectar una variable de idioma (ej. "Responde en Español") dinámicamente en los System Prompts (`core.py`, `memory.py`) para que el ecosistema cognitivo respete la configuración local y procese sus pensamientos en el idioma correcto.
5. **Internacionalización de Consolas (Logs y Prints)**: Estandarizar todos los mensajes de consola (`print()` y futuros `logger`) emitidos por el bot (`meowSick.py`, `music.py`, `core.py`, etc.) para que utilicen el sistema de idiomas, garantizando que el registro del sistema coincida con el idioma configurado.

#### Paso 4: Estandarización de Variables de Entorno (`.env`)

1. Eliminar las funciones manuales destructivas `load_env_dict` y `update_env_key` de `launcher.py`.
2. Adoptar la librería `python-dotenv` como método oficial: `dotenv.load_dotenv()` para leer y `dotenv.set_key()` para escribir credenciales de forma segura y no destructiva.

#### Checklist de Progreso - Fase 1

- [x] **Paso 1: Centralización del Gestor de Estado (`shared/config_manager.py`)**
  - [x] Crear carpeta `shared/` y módulo `config_manager.py`.
  - [x] Implementar `load_json` y `save_json` seguros.
  - [x] Aplicar `filelock` con timeout solo para archivos de configuración compartidos (`config.json`, `outputs.json`). No aplicar a los archivos de memoria de la IA (ya protegidos por el worker pattern del bot).
  - [x] Reemplazar llamadas locales restantes en submódulos de Discord (Cogs):
    - [x] `cogs/AI/core.py` (Métodos: `_get_config` y lectura de `prefix` en `on_message`).
    - [x] `cogs/AI/memory.py` (Métodos: `_ensure_files`, `_get_config`, `_load_prompt`).
    - [x] `cogs/AI/evolution.py` (Lectura/escritura de JSONs de estados de ánimo).
    - [x] `cogs/AI/identity.py` (Lectura/escritura de `known_users.json`).
  - [x] **Paso 1.1: Refactorización de JSON en `launcher.py`** (Subdividido para evitar congelamientos):
    - [x] Bloque 1: Módulos (`update_module_state`, `toggle_module`).
    - [x] Bloque 2: Amnesia Selectiva (`open_amnesia_dialog`).
    - [x] Bloque 3: Estados de Ánimo (`load_moods`, `save_current_mood`, `save_possible_moods`).
    - [x] Bloque 4: Historial de Estados (`load_history`, `clear_history`).
    - [x] Bloque 5: Usuarios (`load_users`, `save_users`, `delete_user_record`).
    - [x] Bloque 6: Memoria de Hechos (`load_memory`, `save_single_fact`, `delete_single_fact`, `add_new_fact_ui`).
    - [x] Bloque 7: Opiniones (`load_opinions`, `save_single_opinion`, `delete_single_opinion`).
    - [x] Bloque 8: Rangos de Afinidad (`load_ranges`, `save_ranges`).
    - [x] Bloque 9: Autoconcepto (`load_self`, `save_self`).
    - [x] Bloque 10: Prompts (`load_prompts`, `save_prompts`).
  - [x] Verificar que `_get_config()` en `AIManager` (Singleton) no cachee el resultado para que el hot-reload de Cogs funcione correctamente.

- [x] **Paso 2: Extracción de Temas y Estilos Visuales (`themes/dark.json`)**
  - [x] Crear carpeta `themes/` y archivo `dark.json` con la paleta de colores.
  - [x] Crear clase `ThemeManager` en `shared/theme_manager.py`.
  - [x] **Paso 2.1: Plan de Migración de Colores en `launcher.py`** (Documentación para refactorización futura)
    - [x] Bloque 1: Ventana Principal y Sidebar (Métodos: `__init__`, `create_sidebar`, `render_*_sidebar`).
    - [x] Bloque 2: Dashboard (Método: `create_dashboard`).
    - [x] Bloque 3: Páginas de Módulos (Métodos: `create_music_page`, `create_modules_page`).
    - [x] Bloque 4: Configuración General y Música (Métodos: `create_config_general_frame`, `create_config_music_frame`).
    - [x] Bloque 5: Configuración de IA (Métodos: `create_config_ai_frame`, `create_config_ai_settings_frame`, `create_config_ai_engine_frame`).
    - [x] Bloque 6: Editores de Memoria IA (Parte 1) (Métodos: `create_ai_identity_frame`, `create_ai_moods_frame`, `create_ai_moods_history_frame`).
    - [x] Bloque 7: Editores de Memoria IA (Parte 2) (Métodos: `create_ai_users_frame`, `create_ai_memory_frame`, `create_ai_opinions_frame`).
    - [x] Bloque 8: Editores de Memoria IA (Parte 3) (Métodos: `create_ai_ranges_frame`, `create_ai_self_frame`, `create_ai_prompts_frame`).
    - [x] Bloque 9: Guías de Ayuda (Métodos: `create_*_guide_frame`).
    - [x] Bloque 10: Funciones de Utilidad y Callbacks (Métodos: `update_module_state`, `open_amnesia_dialog`, `toggle_password`, etc.).
    - [x] **Limpieza Final:** Eliminar el diccionario global `COLORS` de la cabecera del archivo.

- [x] **Paso 3: Sistema Base de Idiomas (`settings/locales/`)**
  - [x] Crear carpeta `settings/locales/` y archivo base `es.json`.
  - [x] Crear archivo `en.json` (traducción base).
  - [x] Crear clase `LanguageManager` en `shared/language_manager.py`.
  - [x] **Paso 3.1: Plan de Migración de Textos en `launcher.py`** (Documentación para refactorización futura)
    - [x] Bloque 1: Ventana Principal, Sidebar y Menús de Navegación.
    - [x] Bloque 2: Dashboard y Página de Módulos (Títulos, botones, descripciones).
    - [x] Bloque 3: Control y Configuración de Música.
    - [x] Bloque 4: Configuración General (Labels, placeholders, tooltips).
    - [x] Bloque 5: Configuración de IA (Ajustes generales, filtros y motores).
    - [x] Bloque 6: Editores de IA Parte 1 (Identidad, Autoconcepto, Prompts, Estados de Ánimo).
    - [x] Bloque 7: Editores de IA Parte 2 (Usuarios, Memoria, Opiniones, Rangos).
    - [x] Bloque 8: Ventanas Emergentes (Diálogos de Amnesia, Nuevo Usuario, Nuevo Estado).
    - [x] Bloque 9: Guías de Ayuda (Textos masivos de Privacidad, Discord, Local, etc.).
    - [x] Bloque 10: Alertas, Estados y Consola (`lbl_status`, `messagebox`, actualizaciones del bot).
    - [x] **Limpieza Final:** Verificar que no quede texto en español incrustado en la lógica del launcher.
  - [x] **Paso 3.2: Internacionalización del Bot (`outputs.json`)**
    - [x] Mover y renombrar `outputs.json` a `settings/locales/outputs_es.json` y crear `outputs_en.json`.
    - [x] Adaptar `launcher.py` (Ajustes de Música) para que edite el archivo `outputs` correspondiente al idioma actual.
    - [x] Adaptar `meowSick.py` y `cogs/music.py` para cargar las respuestas dinámicamente según el idioma configurado en `config.json`.
  - [x] **Paso 3.3: Idioma nativo de la IA**
    - [x] Añadir inyección de idioma en los Prompts del Sistema enviados a la API (Gemini/Ollama) para forzar a la IA a responder y analizar pensamientos en el idioma correcto.
  - [ ] **Paso 3.4: Internacionalización de Consolas (Logs y Prints)**
    - [ ] Diseñar estrategia para inyectar `LanguageManager` o una variante en los Cogs y el script principal del bot.
    - [ ] Extraer strings de inicialización y sistema (`meowSick.py`).
    - [ ] Extraer strings de eventos del módulo de audio (`music.py`).
    - [ ] Extraer logs operativos del ecosistema de IA (`core.py`, `memory.py`, `evolution.py`, `utils.py`).

- [ ] **Paso 4: Estandarización de Variables de Entorno (`python-dotenv`)**
  - [ ] Eliminar funciones manuales `load_env_dict` y `update_env_key` de `launcher.py`.
  - [ ] Implementar lectura y escritura con `python-dotenv` (`dotenv.load_dotenv` / `dotenv.set_key`).

---

### Fase 2: Refactorización y División de la UI

#### Paso 5: Preparar `launcher.py` para la Carga Perezosa

1. Modificar `__init__`: Eliminar todas las llamadas a `self.create_..._page()`.
2. Actualizar `show_frame()` para que acepte Clases en lugar de strings, instanciando la vista solicitada solo si no existe ya en memoria (Lazy Loading).
3. Instanciar `ThemeManager`, `LanguageManager` y `ConfigManager` en el `__init__` de `MeowLauncher` y pasarlos como dependencias (`controller`) a cada vista al momento de su creación.

#### Paso 6: Migrar la Primera Vista (Dashboard)

1. Crear `views/dashboard_view.py` con la clase `DashboardFrame(ctk.CTkFrame)`.
2. Su `__init__` debe aceptar `(self, parent, controller)`.
3. Mover el contenido del método `create_dashboard()` de `launcher.py` al `__init__` de `DashboardFrame`.
4. Adaptar referencias:
   - Reemplazar colores hardcodeados (ej. `COLORS["bg_dark"]`) por `self.controller.theme.get("bg_dark")`.
   - Reemplazar textos estáticos por `self.controller.lang.get("DASHBOARD_TITLE")`.
   - Reemplazar funciones globales (ej. `self.start_bot`) por `self.controller.start_bot`.
5. En `launcher.py`: importar `DashboardFrame` y modificar el botón del sidebar para llamar a `self.show_frame(DashboardFrame)`.

#### Paso 7: Migración Iterativa del Resto de Vistas

Repetir el Paso 6 metódicamente para las demás pantallas:

- `create_music_page` → `views/music/main_view.py`
- `create_modules_page` → `views/modules_view.py`
- `create_config_general_frame` → `views/config/general_view.py`
- `create_config_music_frame` → `views/config/music_view.py`
- `create_config_ai_frame` → `views/config/ai_general_view.py`
- `create_config_ai_settings_frame` → `views/config/ai_settings_view.py`
- `create_config_ai_engine_frame` → `views/config/ai_engine_view.py`
- *(Nueva vista de Personalidades)* → `views/config/ai_presets_view.py`

#### Paso 8: Migración de los Editores de IA

- `create_ai_identity_frame` → `views/ai/identity_editor.py`
- `create_ai_moods_frame` → `views/ai/moods_editor.py`
- `create_ai_moods_history_frame` → `views/ai/moods_history_editor.py`
- `create_ai_users_frame` → `views/ai/users_editor.py`
- `create_ai_memory_frame` → `views/ai/memory_editor.py`
- `create_ai_opinions_frame` → `views/ai/opinions_editor.py`
- `create_ai_ranges_frame` → `views/ai/ranges_editor.py`
- `create_ai_self_frame` → `views/ai/self_editor.py`
- `create_ai_prompts_frame` → `views/ai/prompts_editor.py`

> **Nota de Refactorización:** En todos estos editores (usuarios, memoria, opiniones, rangos), reemplazar los múltiples botones de "Guardar" individuales por fila por un único botón global de "Guardar Cambios" en la parte inferior, junto al botón "Recargar".

#### Paso 9: Migración de las Guías

- `create_discord_guide_frame` → `views/guides/discord_guide_view.py`
- `create_google_guide_frame` → `views/guides/google_guide_view.py`
- `create_id_guide_frame` → `views/guides/id_guide_view.py`
- `create_privacy_guide_frame` → `views/guides/privacy_guide_view.py`
- `create_local_guide_frame` → `views/guides/local_guide_view.py`

#### Tarea de Usabilidad: Reorganización del Menú de Configuración de IA y Nuevas Funciones

**Problema:** La configuración de IA está fragmentada y carece de opciones avanzadas para gestionar personalidades y reseteos precisos.

**Solución:**

1. Eliminar el botón "🤖 Motores de IA" de la barra lateral de configuración principal.
2. Añadir un nuevo botón "🧠 Núcleo Cognitivo (Motor)" en la barra lateral de ajustes de IA (`ai_engine_view.py`).
3. Renombrar "💥 Amnesia Selectiva" a "🔄 Restablecer" y moverlo a la configuración de IA. Implementar una interfaz de dos pestañas: la primera ("Memorias", por defecto) permitirá selección granular con menús expandibles para archivos compuestos (ej. hacer clic en "Autoconcepto" para desplegar y seleccionar borrar solo "Gustos" u "Opiniones").
4. Crear la nueva vista "🎭 Personalidades Prefabricadas" (`views/config/ai_presets_view.py`):
   - Desplegable para seleccionar la personalidad (inicialmente solo la "Por Defecto").
   - Panel informativo mostrando los detalles (identidad, personalidad, gustos, etc.) de la selección actual.
   - Menú expandible inferior para elegir qué importar y qué conservar del bot actual, incluyendo la opción de limpiar registros de usuarios y relaciones.
   - Botón de "Aplicar" precedido por una advertencia nativa integrada en la interfaz (sin popups, usando el estilo `warn_box` del resto del sistema).

#### Checklist de Progreso - Fase 2

- [ ] **Paso 5: Preparar `launcher.py` para Carga Perezosa**
  - [ ] Limpiar `__init__` eliminando las llamadas iniciales `create_*_page()`.
  - [ ] Actualizar `show_frame()` para instanciación dinámica (Lazy Loading por Clase).
  - [ ] Instanciar `ThemeManager`, `LanguageManager` y `ConfigManager` e inyectarlos como `controller`.

- [ ] **Paso 6: Migrar Vista Dashboard (`views/dashboard_view.py`)**
  - [ ] Crear carpeta `views/` con `__init__.py`.
  - [ ] Crear clase `DashboardFrame`, mover código y adaptarlo al controlador.
  - [ ] Aplicar inyección de temas y strings de idioma.

- [ ] **Paso 7: Migrar Vistas Principales**
  - [ ] Crear subcarpetas `views/music/` y `views/config/` con sus `__init__.py`.
  - [ ] `views/music/main_view.py`
  - [ ] `views/modules_view.py`
  - [ ] `views/config/general_view.py`
  - [ ] `views/config/music_view.py`
  - [ ] `views/config/ai_general_view.py`
  - [ ] `views/config/ai_settings_view.py`
  - [ ] `views/config/ai_engine_view.py`
  - [ ] `views/config/ai_presets_view.py` *(nueva)*

- [ ] **Paso 8: Migrar Editores de IA**
  - [ ] Crear subcarpeta `views/ai/` con `__init__.py`.
  - [ ] Reemplazar botones "Guardar" individuales por un botón global unificado por vista.
  - [ ] `views/ai/identity_editor.py`
  - [ ] `views/ai/moods_editor.py`
  - [ ] `views/ai/moods_history_editor.py`
  - [ ] `views/ai/users_editor.py`
  - [ ] `views/ai/memory_editor.py`
  - [ ] `views/ai/opinions_editor.py`
  - [ ] `views/ai/ranges_editor.py`
  - [ ] `views/ai/self_editor.py`
  - [ ] `views/ai/prompts_editor.py`

- [ ] **Paso 9: Migrar Guías**
  - [ ] Crear subcarpeta `views/guides/` con `__init__.py`.
  - [ ] `views/guides/discord_guide_view.py`
  - [ ] `views/guides/google_guide_view.py`
  - [ ] `views/guides/id_guide_view.py`
  - [ ] `views/guides/privacy_guide_view.py`
  - [ ] `views/guides/local_guide_view.py`

- [ ] **Tarea de Usabilidad: Reorganizar Menú de Configuración de IA**
  - [ ] Eliminar botón "🤖 Motores de IA" del menú de configuración general.
  - [ ] Añadir botón "🧠 Núcleo Cognitivo" en el submenú de IA.
  - [ ] Implementar vista "🔄 Restablecer" con pestañas y selección granular expansible.
  - [ ] Implementar vista "🎭 Personalidades Prefabricadas" con selector, panel informativo y alerta nativa integrada.

---

### Fase 3: Estabilización Post-Refactorización

#### Paso 10: Implementación de Sistema de Logging Real

Los múltiples bloques `except: pass` a lo largo del código están ocultando fallos silenciosos críticos.

1. Crear la carpeta `logs/`.
2. Configurar el módulo estándar `logging` de Python en el arranque de `launcher.py` y `meowSick.py` con un `RotatingFileHandler` que escriba en `logs/system.log`.
3. Sustituir sistemáticamente todos los bloques `except: pass` en los cogs (`music.py`, `memory.py`, `evolution.py`, `core.py`, `utils.py`) y en la nueva UI (`views/`) por `logger.error("Descripción del contexto", exc_info=True)`.

#### Paso 11: Afectaciones a Otros Archivos (`build.py` y Config)

1. **`build.py`**: Actualizar las banderas `--hidden-import` y `--collect-all` de PyInstaller para incluir las nuevas carpetas `views/`, `shared/` y `themes/`. Modificar `create_clean_dist_files()` para que genere automáticamente las carpetas `settings/locales/` y `themes/` en la compilación limpia.
2. **`config.json`**: Añadir los parámetros globales `"language": "es"` y `"theme": "dark"` para recordar las preferencias del usuario entre sesiones.

#### Tarea de Corrección: Unificar y Reparar Sistema de Restablecimiento (Factory Reset)

**Problema:** El reseteo de IA está fragmentado ("Amnesia Selectiva" vs "Restablecer a fábrica"). Usa valores hardcodeados incompletos en `build.py`, los rangos de afinidad tienen un salto brusco (50-100), y no permite borrar partes específicas de un archivo compuesto.

**Solución:** Centralizar la lógica de reseteo para que lea las plantillas originales desde `build.py` (en lugar de hardcodearlas de nuevo en la UI). Integrar con la nueva interfaz de selección granular del Paso 9. Ajustar los rangos de afinidad base para mayor granularidad (ej. subdividir el tramo 50–100 en `50-70 / 71-85 / 86-100`) y asegurarse de que el botón de reset restaure estos rangos correctamente.

#### Tarea de Corrección: Refinar Valores por Defecto de la IA

**Problema:** La IA se enoja demasiado rápido, ignora `estados_posibles.json` inventando sus propios estados, y la identidad inicial es demasiado volátil.

**Solución:**

1. Ajustar la personalidad base a un lienzo en blanco neutral/estable.
2. Modificar el prompt `evolucion_analisis` en `prompts.json` aplicando una directriz estricta que obligue a la IA a elegir **exclusivamente** de los estados listados en `estados_posibles.json` (o una combinación de ellos), penalizando la invención de emociones no registradas.

#### Tarea de Corrección: Solucionar Bugs de Auto-Reconocimiento y Duplicidad en Memoria

**Problema:** La IA se registra a sí misma en `known_users.json` o `memoria.json` como si fuera un usuario externo. Además, se generan entradas duplicadas para el mismo usuario en ocasiones. (Nota: ya existen parches parciales con `if uid == bot_id: continue` en `memory.py`, pero la cobertura no es completa.)

**Solución:**

- Añadir validaciones estrictas y completas en `identity.py` (`register_user_if_new`) y en los tres tasks de `memory.py` (`_task_update_opinions`, `_task_update_self`, `_task_extract_facts`) para ignorar siempre `self.bot.user.id`.
- Implementar verificaciones de unicidad (normalización de keys, deduplicación de listas de hechos) para prevenir registros repetidos.

#### Checklist de Progreso - Fase 3

- [ ] **Paso 10: Implementar Sistema de Logging Real (`logs/system.log`)**
  - [ ] Crear carpeta `logs/`.
  - [ ] Configurar `logging` con `RotatingFileHandler` en `launcher.py` y `meowSick.py`.
  - [ ] Reemplazar bloques `except: pass` en todos los Cogs y vistas por `logger.error(..., exc_info=True)`.

- [ ] **Paso 11: Actualizar `build.py` y configuración global**
  - [ ] Ajustar `hidden-import` y `collect-all` en PyInstaller para `views/`, `shared/` y `themes/`.
  - [ ] Actualizar `create_clean_dist_files()` para generar `settings/locales/`, `themes/` y `logs/` limpios.
  - [ ] Añadir parámetros `"language"` y `"theme"` a `config.json`.

- [ ] **Tarea de Corrección: Unificar y Reparar Sistema de Restablecimiento**
  - [ ] Centralizar lógica de reset para leer plantillas desde `build.py`.
  - [ ] Soportar reseteo parcial de archivos compuestos (ej. solo "gustos" de `autoconcepto.json`).
  - [ ] Ajustar rangos de afinidad por defecto para mayor granularidad (subdividir tramo 50–100).

- [ ] **Tarea de Corrección: Refinar Valores por Defecto de la IA**
  - [ ] Estandarizar personalidad base como neutral/estable.
  - [ ] Modificar prompt `evolucion_analisis` para bloquear invención de estados no listados en `estados_posibles.json`.

- [ ] **Tarea de Corrección: Bugs de Memoria y Auto-Reconocimiento**
  - [ ] Añadir validación completa de `bot.user.id` en `identity.py` y en los tres tasks de `memory.py`.
  - [ ] Implementar verificaciones de unicidad para prevenir entradas duplicadas por usuario.

---

### Fase 4: Documentación General (`README.md`)

Una vez que la estructura del código esté limpia y estabilizada, se procederá a **actualizar** el `README.md` existente (que ya es funcional) para reflejar el estado real de MeowSick V3 post-refactorización.

#### Paso 12: Actualizar Guía de Usuario

- Revisar y actualizar la sección de instalación y despliegue portable.
- Actualizar el listado de comandos disponibles en Discord si cambiaron.
- Actualizar la sección de ajustes del Panel de Control para reflejar el nuevo menú de configuración de IA y las Personalidades Prefabricadas.

#### Paso 13: Actualizar Guía del Desarrollador (Arquitectura)

- Actualizar el diagrama de estructura de archivos para reflejar la nueva arquitectura (`views/`, `shared/`, `themes/`, `logs/`).
- Documentar el nuevo patrón MVC implementado (Controller → Views → Managers).
- Actualizar la sección del Sistema IPC para reflejar el nuevo protocolo JSON estructurado.
- Documentar `TTSManager` y `STTManager` como motores intercambiables.

#### Checklist de Progreso - Fase 4

- [ ] **Paso 12: Actualizar Guía de Usuario**
  - [ ] Revisar sección de instalación y despliegue portable.
  - [ ] Actualizar listado de comandos disponibles en Discord.
  - [ ] Actualizar sección de ajustes del Panel de Control (nuevo menú de IA, Personalidades Prefabricadas).

- [ ] **Paso 13: Actualizar Guía del Desarrollador (Arquitectura)**
  - [ ] Actualizar diagrama de estructura de archivos con `views/`, `shared/`, `themes/`, `logs/`.
  - [ ] Documentar el patrón MVC implementado (Controller → Views → Managers).
  - [ ] Actualizar sección IPC para reflejar el nuevo protocolo JSON estructurado con prefijo de canal.
  - [ ] Documentar `TTSManager` y `STTManager` como motores abstraídos e intercambiables.

---

### Fase 5: Mejoras de Arquitectura y Desacoplamiento

#### Tarea 14: Desacoplamiento del Script de Compilación (`build.py`)

**Problema:** `build.py` contiene copias hardcodeadas de todos los archivos de configuración y memoria por defecto. Si se añade una nueva opción de configuración en el código, hay que recordar actualizarla manualmente en `build.py`, lo cual es muy propenso a desincronización.

**Solución:** Modificar `build.py` para que, en lugar de tener el contenido incrustado, lea los archivos de configuración del entorno de desarrollo y los copie a la carpeta de distribución, purgando únicamente los valores sensibles (tokens, API keys).

#### Tarea 15: Abstracción de Motores Multimodales (TTS/STT)

**Problema:** La lógica para manejar los diferentes motores de Texto-a-Voz (Edge-TTS, Piper) y Voz-a-Texto (Whisper) está mezclada directamente dentro de `cogs/AI/core.py`.

**Solución:** Crear los archivos `cogs/AI/tts_manager.py` y `cogs/AI/stt_manager.py` (como módulos separados, **no** dentro de `utils.py`, para no convertirlo en un nuevo God Object). Cada clase encapsulará la lógica específica de su motor, permitiendo que `core.py` simplemente llame a `tts_manager.speak(text)` sin conocer la implementación. Esto facilitará la adición de nuevos motores en el futuro (ej. ElevenLabs, Coqui).

#### Tarea 16: Extracción de "Valores Mágicos" a Configuración

**Problema:** El código contiene valores hardcodeados que afectan el comportamiento del bot y no pueden ajustarse desde el Launcher.

**Solución:** Extraer los siguientes parámetros a `config.json` con su respectiva opción en la UI:

- **`cogs/AI/core.py`**:
  - `random.random() < 0.05` → Probabilidad de respuesta espontánea (5%).
  - `now - last < 3.0` → Cooldown anti-spam (3 segundos).
  - `limit = min(limit, 5)` → Reducción de mensajes en Modo Gamer.
  - `beam_size=5` → Nivel de precisión de Whisper (STT local).
- **`cogs/music.py`**:
  - `YTDL_OPTIONS` → Opciones de extracción de YouTube (ej. `'format': 'bestaudio/best'`).
  - `FFMPEG_OPTIONS` → Argumentos de reconexión (`-reconnect_delay_max 5`).
  - `await asyncio.sleep(60)` → Tiempo de inactividad antes de la auto-desconexión.
  - `MAX_RETRIES = 3` → Límite de reintentos en fallo de extracción.
  - `timeout=60` → Caducidad de botones interactivos de la cola (`QueueView`).
- **`cogs/AI/utils.py`**:
  - `"repeat_penalty": 1.1` → Penalización de repetición en llamadas a Ollama.
  - `aiohttp.ClientTimeout(total=180)` → Timeout para modelos locales pesados.

#### Tarea 17: Robustecimiento del Sistema IPC

**Problema:** La comunicación Launcher ↔ Bot se basa en parseo de strings con prefijos (`IPC_PROGRESS:`, `CMD_MUSIC:`). Un `print` accidental puede romper la UI. La invocación de comandos desde el Launcher depende de un "hack" que reutiliza el último contexto de un canal, lo cual es poco fiable.

**Solución (incremental):** Mantener las tuberías estándar (`stdin`/`stdout`) por su simplicidad, pero migrar el formato a **mensajes JSON estructurados por línea**:

- **Launcher → Bot:**
  - *Antes:* `CMD_MUSIC:play:some song`
  - *Ahora:* `{"type": "command", "name": "music_play", "payload": {"query": "some song"}}`
- **Bot → Launcher:**
  - *Antes:* `IPC_PROGRESS:0.5:Cargando...`
  - *Ahora:* `{"type": "event", "name": "progress_update", "payload": {"percent": 0.5, "message": "Cargando..."}}`
- El `console_listener` del bot se modificará para parsear estos JSON e invocar funciones internas de los cogs directamente.
- **Seguridad IPC:** Añadir un prefijo único de canal al inicio de cada línea IPC (ej. `IPC>>` antes del JSON) y filtrar estrictamente en el Launcher para que solo líneas con ese prefijo sean parseadas como comandos. Esto previene que la IA, un usuario, o un `print` de debug generen un JSON válido en `stdout` que confunda al parser.

#### Checklist de Progreso - Fase 5

- [ ] **Tarea 14: Desacoplar Script de Compilación (`build.py`)**
  - [ ] Modificar para leer configs del entorno de desarrollo en lugar de tenerlas hardcodeadas.
  - [ ] Purgar solo valores sensibles (tokens, keys) al generar la distribución.

- [ ] **Tarea 15: Abstraer Motores Multimodales (TTS/STT)**
  - [ ] Crear `cogs/AI/tts_manager.py` con clase `TTSManager` (Edge-TTS, Piper, etc.).
  - [ ] Crear `cogs/AI/stt_manager.py` con clase `STTManager` (Whisper, Gemini Audio, etc.).
  - [ ] Refactorizar `core.py` para delegar a `tts_manager.speak()` y `stt_manager.transcribe()`.
  - [ ] **No agregar estos managers a `utils.py`** para no convertirlo en un nuevo God Object.

- [ ] **Tarea 16: Extraer "Valores Mágicos" a `config.json`**
  - [ ] Parametrizar probabilidad espontánea, cooldown, límite Gamer y beam_size en `core.py`.
  - [ ] Parametrizar `YTDL_OPTIONS`, `FFMPEG_OPTIONS`, sleep de inactividad, `MAX_RETRIES` y timeout de botones en `music.py`.
  - [ ] Parametrizar `repeat_penalty` y `ClientTimeout` en `utils.py`.

- [ ] **Tarea 17: Robustecer el Sistema IPC**
  - [ ] Migrar protocolo `stdin`/`stdout` de strings con prefijos a JSON estructurado por línea.
  - [ ] Añadir prefijo de canal único (ej. `IPC>>`) a cada mensaje IPC para aislarlos del `stdout` general del bot.
  - [ ] Actualizar el parser del Launcher para filtrar estrictamente por ese prefijo.
  - [ ] Refactorizar `console_listener` del bot para invocar funciones internas de los cogs directamente (en lugar de reenviar comandos de Discord).

---

### Fase 6: QoL y Mejoras Futuras (Post-Refactorización)

#### Checklist de Progreso - Fase 6

- [ ] **Tarea 19: Asistente de Configuración Inicial (Wizard)**
  - [ ] Crear pantalla de bienvenida bloqueante para el primer arranque.
  - [ ] Forzar configuración de Idioma, Token, Admin ID y canales básicos.

- [ ] **Tarea 20: Comando `!config` vía Discord**
  - [ ] Crear comando restringido a `ADMIN_ID` para configuraciones remotas.
  - [ ] Extraer y separar variables de canal compartidas (crear `MUSIC_CHANNEL_ID` en lugar de reusar `WELCOME_CHANNEL_ID`).