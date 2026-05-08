# Tareas Completadas y Contexto Inicial

> **Instrucción de Mantenimiento:** Para añadir nuevas entradas o mover fases a este archivo, la información debe estar sintetizada, limpia y reflejar fielmente los cambios reales implementados en el código.

## Resumen de la Refactorización V3

### Problemas Resueltos:
- **Eliminación del "God Object"**: Se desfragmentó `launcher.py` (antes >3000 líneas) para mejorar la navegación y mantenibilidad.
- **Rendimiento de la UI**: Se solucionaron los tiempos de arranque lentos y el "flickering" al cambiar de pestañas implementando Carga Perezosa (Lazy Loading).
- **Textos Hardcodeados**: Se eliminó la rigidez de los textos incrustados extrayéndolos a un sistema de internacionalización (i18n).
- **Deuda Técnica de JSON y .env**: Se eliminó la duplicidad de funciones manuales destructivas centralizando la lógica en managers seguros (`ConfigManager`, `dotenv`).
- **IPC Frágil**: Se robusteció la comunicación entre procesos pasando de un parseo de strings simple a un protocolo JSON estructurado con prefijos protegidos (`IPC>>`).

### Objetivos Logrados:
- **Modularización**: Interfaz separada en componentes lógicos (Vistas) independientes.
- **Mantenibilidad**: `launcher.py` ahora actúa de forma eficiente solo como Controlador central.
- **Internacionalización**: Aplicación preparada para soporte multi-idioma (separación de Vista/Datos).
- **Arquitectura Segura**: Gestión centralizada y con candados (filelocks) para la lectura/escritura y para evitar colisiones de subprocesos.

*(Este archivo documenta los hitos de la refactorización inicial para mantener limpio el ROADMAP de desarrollo activo).*

---

## Fases Completadas

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
  - [x] **Paso 3.4: Internacionalización de Consolas (Logs y Prints)**
    - [x] Diseñar estrategia para inyectar `LanguageManager` o una variante en los Cogs y el script principal del bot.
    - [x] Extraer strings de inicialización y sistema (`meowSick.py`).
    - [x] Extraer strings de eventos del módulo de audio (`music.py`).
    - [x] Extraer logs operativos del ecosistema de IA (`core.py`, `memory.py`, `evolution.py`, `utils.py`).

- [x] **Paso 4: Estandarización de Variables de Entorno (`python-dotenv`)**
  - [x] **Paso 4.1:** Importar `dotenv` (`set_key`, `dotenv_values`) en `launcher.py` y definir ruta estandarizada hacia `.env`.
  - [x] **Paso 4.2:** Refactorizar lectura/escritura en **Configuración General** (`DISCORD_TOKEN`, `ADMIN_ID`, `WELCOME_CHANNEL_ID`).
  - [x] **Paso 4.3:** Refactorizar lectura/escritura en **Configuración de Música** (`PLAYLIST_URL`).
  - [x] **Paso 4.4:** Refactorizar lectura/escritura en **Configuración de IA** (`AI_TARGET_CHANNELS`, `GEMINI_API_KEY`, `GEMINI_API_KEY_2`).
  - [x] **Paso 4.5:** Limpieza final: Eliminar métodos manuales `load_env_dict` y `update_env_key` de `launcher.py`.

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

- [x] **Paso 5: Preparar `launcher.py` para Carga Perezosa**
  - [x] Limpiar `__init__` eliminando las llamadas iniciales `create_*_page()`.
  - [x] Actualizar `show_frame()` para instanciación dinámica (Lazy Loading por Clase).
  - [x] Instanciar `ThemeManager`, `LanguageManager` y `ConfigManager` e inyectarlos como `controller`.

- [x] **Paso 6: Migrar Vista Dashboard (`views/dashboard_view.py`)**
  - [x] Crear carpeta `views/` con `__init__.py`.
  - [x] Crear clase `DashboardFrame`, mover código y adaptarlo al controlador.
  - [x] Aplicar inyección de temas y strings de idioma.

- [x] **Paso 7: Migrar Vistas Principales**
  - [x] Crear subcarpetas `views/music/` y `views/config/` con sus `__init__.py`.
  - [x] `views/music/main_view.py`
    - [x] Crear clase y migrar código de `create_music_page`.
    - [x] Adaptar referencias y variables al `self.controller`.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/modules_view.py`
    - [x] Crear clase y migrar código de `create_modules_page`.
    - [x] Adaptar referencias y variables al `self.controller`.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/config/general_view.py`
    - [x] Crear clase y migrar código de `create_config_general_frame`.
    - [x] Adaptar referencias y variables al `self.controller`.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/config/music_view.py`
    - [x] Crear clase y migrar código de `create_config_music_frame`.
    - [x] Adaptar referencias y variables al `self.controller`.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/config/ai_general_view.py`
    - [x] Crear clase y migrar código de `create_config_ai_frame`.
    - [x] Adaptar referencias y variables al `self.controller`.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/config/ai_settings_view.py`
    - [x] Crear clase y migrar código de `create_config_ai_settings_frame`.
    - [x] Adaptar referencias y variables al `self.controller`.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/config/ai_engine_view.py`
    - [x] Crear clase y migrar código de `create_config_ai_engine_frame`.
    - [x] Adaptar referencias y variables al `self.controller`.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/config/ai_presets_view.py` *(nueva)*
    - [x] Crear interfaz base y enlazarla al menú lateral.
  
- [x] **Paso 8: Migrar Editores de IA**
  - [x] Crear subcarpeta `views/ai/` con `__init__.py`.
  - [x] Reemplazar botones "Guardar" individuales por un botón global unificado por vista.
  - [x] `views/ai/identity_editor.py`
    - [x] Crear clase, migrar `create_ai_identity_frame` y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/moods_editor.py`
    - [x] Crear clase, migrar `create_ai_moods_frame` y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/moods_history_editor.py`
    - [x] Crear clase, migrar `create_ai_moods_history_frame` y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/users_editor.py`
    - [x] Crear clase, migrar `create_ai_users_frame`, unificar botón "Guardar" y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/memory_editor.py`
    - [x] Crear clase, migrar `create_ai_memory_frame`, unificar botón "Guardar" y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/opinions_editor.py`
    - [x] Crear clase, migrar `create_ai_opinions_frame`, unificar botón "Guardar" y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/ranges_editor.py`
    - [x] Crear clase, migrar `create_ai_ranges_frame`, unificar botón "Guardar" y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/self_editor.py`
    - [x] Crear clase, migrar `create_ai_self_frame`, unificar botón "Guardar" y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.
  - [x] `views/ai/prompts_editor.py`
    - [x] Crear clase, migrar `create_ai_prompts_frame` y adaptar controlador.
    - [x] Actualizar botón en el launcher y borrar método original.

- [x] **Paso 9: Migrar Guías**
  - [x] Crear subcarpeta `views/guides/` con `__init__.py`.
  - [x] `views/guides/discord_guide_view.py`
  - [x] `views/guides/google_guide_view.py`
  - [x] `views/guides/id_guide_view.py`
  - [x] `views/guides/privacy_guide_view.py`
  - [x] `views/guides/local_guide_view.py`

- [x] **Tarea de Usabilidad: Reorganizar Menú de Configuración de IA**
  - [x] Eliminar botón "🤖 Motores de IA" del menú de configuración general.
  - [x] Añadir botón "🧠 Núcleo Cognitivo" en el submenú de IA.
  - [x] Implementar vista unificada "🎭 Personalidades y Restablecimiento" (Presets + Borrado granular modular en una sola pantalla).

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

**Problema:** La IA se registra a sí misma en `known_users.json` o `memoria.json` como si fuera un usuario externo. Además, se generan entradas duplicadas para el mismo usuario en ocasiones.

**Solución:**

- Añadir validaciones estrictas y completas en `identity.py` (`register_user_if_new`) y en los tres tasks de `memory.py` (`_task_update_opinions`, `_task_update_self`, `_task_extract_facts`) para ignorar siempre `self.bot.user.id`.
- Implementar verificaciones de unicidad (normalización de keys, deduplicación de listas de hechos) para prevenir registros repetidos.

#### Checklist de Progreso - Fase 3

- [x] **Paso 10: Implementar Sistema de Logging Real (`logs/system.log`)**
  - [x] Crear carpeta `logs/`.
  - [x] Configurar `logging` con `RotatingFileHandler` en `launcher.py` y `meowSick.py`.
  - [x] Reemplazar bloques `except: pass` en todos los Cogs y vistas por `logger.error(..., exc_info=True)`.

- [x] **Paso 11: Actualizar `build.py` y configuración global**
  - [x] Ajustar `hidden-import` y `collect-all` en PyInstaller para `views/`, `shared/` y `themes/`.
  - [x] Actualizar `create_clean_dist_files()` para generar `settings/locales/`, `themes/` y `logs/` limpios.
  - [x] Añadir parámetros `"language"` y `"theme"` a `config.json`.

- [x] **Tarea de Corrección: Unificar y Reparar Sistema de Restablecimiento**
  - [x] Centralizar lógica de reset para leer plantillas desde `build.py`.
  - [x] Soportar reseteo parcial de archivos compuestos (ej. solo "gustos" de `autoconcepto.json`).
  - [x] Ajustar rangos de afinidad por defecto para mayor granularidad (subdividir tramos, ej: 50–100).

- [x] **Tarea de Corrección: Refinar Valores por Defecto de la IA**
  - [x] Estandarizar personalidad base como neutral/estable.
  - [x] Modificar prompt `evolucion_analisis` para bloquear invención de estados no listados en `estados_posibles.json`.

- [x] **Tarea de Corrección: Bugs de Memoria y Auto-Reconocimiento**
  - [x] Añadir validación completa de `bot.user.id` en `identity.py` y en los tres tasks de `memory.py`.
  - [x] Implementar verificaciones de unicidad para prevenir entradas duplicadas por usuario.

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

- [x] **Paso 12: Actualizar Guía de Usuario**
  - [x] Revisar sección de instalación y despliegue portable.
  - [x] Actualizar listado de comandos disponibles en Discord.
  - [x] Actualizar sección de ajustes del Panel de Control (nuevo menú de IA, Personalidades Prefabricadas).

- [x] **Paso 13: Actualizar Guía del Desarrollador (Arquitectura)**
  - [x] Actualizar diagrama de estructura de archivos con `views/`, `shared/`, `themes/`, `logs/`.
  - [x] Documentar el patrón MVC implementado (Controller → Views → Managers).
  - [x] Actualizar sección IPC para reflejar el nuevo protocolo JSON estructurado con prefijo de canal.
  - [x] Documentar `TTSManager` y `STTManager` como motores abstraídos e intercambiables.


---

### Fase 5: Mejoras de Arquitectura y Desacoplamiento

#### Tarea 14: Desacoplamiento de `build.py`
- Refactorización de `build.py` para leer configuraciones directamente del entorno, purgando valores sensibles (tokens/keys) al compilar, eliminando el hardcodeo previo.

#### Tarea 15: Abstracción de Motores Multimodales (TTS/STT)
- Extracción de la lógica de voz desde `core.py` hacia gestores independientes (`tts_manager.py` y `stt_manager.py`), evitando crear un *God Object* en `utils.py` y facilitando futuras integraciones (ej. Piper, Edge-TTS, Whisper).

#### Tarea 16: Centralización de "Valores Mágicos"
- Traslado de parámetros fijos de comportamiento (probabilidades espontáneas, cooldowns, límites de modo gamer, opciones de yt-dlp/ffmpeg y timeouts) de los Cogs (`core.py`, `music.py`, `utils.py`) hacia `config.json` para permitir su manipulación desde la UI.

#### Tarea 17: Robustecimiento del Sistema IPC
- **Protocolo Estructurado:** Reemplazo de strings simples por mensajes JSON estandarizados para la comunicación bot-launcher.
- **Seguridad de Tuberías:** Incorporación del prefijo de canal `IPC>>` para evitar roturas de UI por `print()` accidentales, actualizando el listener para despachar directamente comandos internos.

#### Checklist de Progreso - Fase 5
- [x] **Tarea 14: Desacoplar Script de Compilación (`build.py`)**
  - [x] Leer configs de desarrollo y purgar valores sensibles en la compilación.
- [x] **Tarea 15: Abstraer Motores Multimodales (TTS/STT)**
  - [x] Crear `tts_manager.py` y `stt_manager.py` y refactorizar `core.py` para delegar su funcionalidad.
- [x] **Tarea 16: Extraer "Valores Mágicos" a Configuración**
  - [x] Parametrizar variables duras en `core.py`, `music.py` y `utils.py` hacia `config.json`.
- [x] **Tarea 17: Robustecer el Sistema IPC**
  - [x] Migrar a JSON estructurado (`{"type": "...", "name": "...", ...}`) con prefijo de seguridad `IPC>>` y actualizar los parsers.


---

### Fase 6: Mejoras de Calidad de Vida (QoL) y UI

#### 📌 Tarea 19: Selector de Idioma Dinámico en Interfaz
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

#### 📌 Tarea 20: Asistente de Configuración Inicial (Wizard)
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

#### 📌 Tarea 21: Restricción de Canal para Módulo de Música
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

#### 📌 Tarea 22: Ampliación de Personalidades Prefabricadas
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

#### 📌 Tarea 23: Expansión de Temas Visuales y Colores Custom
- **Fase de Análisis Previo (Obligatorio):**
  - **Detalles, Problema y Mejoras:** 
  El ThemeManager actual está parcialmente hardcodeado en `launcher.py` para cargar siempre `"dark"`. Añadir más temas base y una herramienta de personalización de colores HEX permite adaptar la interfaz a los gustos específicos de cada servidor. Se decidió crear un entorno independiente de "Previsualización en tiempo real" (Ventana Toplevel) para ver los cambios antes de guardarlos.
  - **Archivos a modificar y dependencias:**
    - `launcher.py`: Modificar la inyección de `ThemeManager` para leer el estado guardado.
    - `themes/`: Crear físicamente los archivos prefabricados `light.json` y `midnight.json`.
    - `views/config/general_view.py`: Añadir menú de temas e instanciar la clase `ThemeEditorWindow` como Toplevel.
    - `settings/locales/es.json` (y `en.json`): Nuevas claves para la UI (`cfg_gen_theme`, `cfg_gen_theme_editor`, `msg_restart_theme`).

- **Checklist de Implementación:**
  - [x] `themes/`: Crear físicamente los archivos base `light.json` (escala Zinc) y `midnight.json` (OLED).
  - [x] `launcher.py`: Modificar el `__init__` para inyectar el tema desde `config.json` en lugar del `"dark"` estático.
  - [x] `shared/theme_manager.py`: Añadir métodos de lectura dinámica de directorio y guardado custom.
  - [x] `settings/locales/es.json` (y `en.json`): Añadir claves de texto para la nueva interfaz.
  - [x] `views/config/general_view.py`: Integrar `CTkOptionMenu` que guarde la variable temática.
  - [x] `views/config/general_view.py`: Añadir la interfaz de edición HEX en ventana dedicada (Toplevel) con Previsualización.
  - [x] `views/config/general_view.py`: Implementar el popup de aviso de reinicio al cambiar de colores visuales.
  - [x] `views/config/general_view.py`: Implementar "Efecto Negativo/Complementario" en tiempo real al hacer hover sobre los campos.