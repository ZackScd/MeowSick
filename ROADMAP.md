# ROADMAP de Refactorización - MeowSick V3

Este documento describe el plan de acción para refactorizar el archivo `launcher.py`, que ha crecido a más de 3000 líneas y presenta problemas de rendimiento y mantenibilidad.

## 1. Problema Actual

- **"God Object"**: El archivo `launcher.py` contiene toda la lógica de la interfaz gráfica, convirtiéndose en un "objeto dios" difícil de navegar y modificar.
- **Rendimiento de la UI**: La aplicación crea **todos** los widgets de **todas** las ventanas al iniciarse. Esto causa:
  - Un tiempo de arranque más lento.
  - Tirones o parpadeos ("flickering") al cambiar entre pestañas, ya que Tkinter debe recalcular la geometría de cientos de elementos.
- **Escalabilidad**: Añadir nuevas ventanas o modificar las existentes es propenso a errores y complica el código innecesariamente.
- **Textos Hardcodeados**: Los textos de la interfaz (títulos, botones, mensajes, descripciones) están incrustados directamente en el código de la UI. Esto ensucia la lógica, dificulta las modificaciones y hace imposible cambiar el idioma de la aplicación.

## 2. Objetivo de la Refactorización

- **Modularización**: Dividir la interfaz en componentes lógicos (vistas/páginas), donde cada uno reside en su propio archivo.
- **Rendimiento**: Implementar **"Carga Perezosa" (Lazy Loading)**. Las vistas solo se crearán en memoria la primera vez que el usuario haga clic en su respectivo botón, mejorando drásticamente el tiempo de arranque y la fluidez.
- **Mantenibilidad**: Simplificar `launcher.py` para que actúe solo como un controlador principal, facilitando la depuración y la adición de nuevas características.
- **Internacionalización (i18n)**: Extraer todos los strings y textos de la interfaz hacia diccionarios externos (`.json`). Esto separará la vista de los datos y dejará la aplicación preparada para el soporte multi-idioma.

## 3. Nueva Estructura de Archivos (Propuesta)

Se creará una nueva carpeta `views` para alojar cada pantalla de la aplicación.

```
MeowSick/
├── launcher.py           # <-- Archivo principal, muy reducido.
├── views/
│   ├── __init__.py
│   ├── dashboard_view.py   # Clase DashboardFrame
│   ├── music_view.py       # Clase MusicFrame
│   ├── modules_view.py     # Clase ModulesFrame
│   ├── config/
│   │   ├── __init__.py
│   │   ├── general_view.py
│   │   └── music_view.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── main_view.py
│   │   ├── settings_view.py
│   │   ├── identity_editor.py
│   │   ├── moods_editor.py
│   │   ├── moods_history_editor.py
│   │   ├── users_editor.py
│   │   ├── memory_editor.py
│   │   ├── opinions_editor.py
│   │   ├── ranges_editor.py
│   │   ├── self_editor.py
│   │   └── prompts_editor.py
│   └── guides/
│       ├── __init__.py
│       ├── discord_guide_view.py
│       ├── google_guide_view.py
│       ├── id_guide_view.py
│       ├── privacy_guide_view.py
│       └── local_guide_view.py
├── settings/
│   └── locales/            # <-- Nueva carpeta para idiomas
│       ├── es.json
│       └── en.json
```

## 4. Plan de Acción (Paso a Paso)

**⚠️ Importante**: El orden de ejecución es vital. Primero construiremos los cimientos centrales (Gestores de Configuración, Tema e Idioma). De esta forma, al momento de extraer las vistas a nuevos archivos, ya insertaremos el código limpio usando estos gestores, evitando tener que re-editar decenas de archivos en el futuro.

### Fase 1: Cimientos y Resolución de Deuda Técnica (Core)

#### Paso 1: Centralización del Gestor de Estado (D.R.Y)
Actualmente `launcher.py`, `meowSick.py`, `music.py` y `memory.py` poseen sus propias funciones duplicadas para leer/guardar archivos JSON.
1.  Crear un nuevo módulo `shared/config_manager.py`.
2.  Implementar métodos seguros (`load_json`, `save_json`) que prevengan corrupciones de disco mediante control de concurrencia (`threading.Lock()`).
3.  Eliminar las funciones `_load_json` locales y reemplazarlas por este gestor.

#### Paso 2: Extracción de Temas y Estilos Visuales
El diccionario `COLORS` está fuertemente acoplado dentro de `launcher.py`.
1.  Crear la carpeta `themes/` y un archivo `dark.json` que contenga la paleta de colores actual.
2.  Crear una clase `ThemeManager` que lea este archivo y provea los colores de forma dinámica.

#### Paso 3: Sistema Base de Idiomas (i18n)
1.  Crear la carpeta `settings/locales/` y el archivo base `es.json` (Español).
2.  Crear una clase `LanguageManager` que se encargue de cargar el archivo JSON y proveer un método (ej. `get_text()`) para inyectar los strings.

#### Paso 4: Estandarización de Variables de Entorno (`.env`)
1.  Eliminar las funciones manuales destructivas (`load_env_dict` y `update_env_key`) de `launcher.py`.
2.  Añadir la librería `python-dotenv` como el método oficial para leer y guardar (`dotenv.set_key()`) las credenciales.

### Fase 2: Refactorización y División de la UI

#### Paso 5: Preparar `launcher.py` para la Carga Perezosa
1.  Modificar `__init__`: Eliminar las llamadas a `self.create_..._page()`.
2.  Actualizar `show_frame()` para que acepte Clases en lugar de strings, instanciando la vista solicitada solo si no existe en memoria (Lazy Loading).
3.  Instanciar los nuevos `ThemeManager`, `LanguageManager` y `ConfigManager` en el `__init__` de MeowLauncher para pasarlos como dependencias (controller) a las futuras vistas.

#### Paso 6: Migrar la Primera Vista (Dashboard)

1.  **Crear `views/dashboard_view.py`**.
2.  Dentro, crear la clase `DashboardFrame(ctk.CTkFrame)`.
3.  Su `__init__` debe aceptar `(self, parent, controller)` (donde el controller dará acceso a los gestores de la Fase 1).
4.  **Mover el código**: Copiar todo el contenido del método `create_dashboard()` de `launcher.py` al `__init__` de `DashboardFrame`.
5.  **Adaptar referencias**:
    -   Reemplazar colores hardcodeados (ej. `COLORS["bg_dark"]`) por llamadas al `ThemeManager`.
    -   Reemplazar textos estáticos por llamadas al `LanguageManager` (ej. `lang.get("DASHBOARD_TITLE")`).
    -   Reemplazar funciones globales (ej. `self.start_bot`) por `self.controller.start_bot`.
6.  **Actualizar `launcher.py`**:
    -   Importar la nueva clase: `from views.dashboard_view import DashboardFrame`.
    -   Modificar el botón del dashboard en la sidebar para que llame a `self.show_frame(DashboardFrame)`.

#### Paso 7: Migración Iterativa del Resto de Vistas

Repetir el "Paso 6" metódicamente (limpiando textos, colores y estado local) para las demás pantallas:

-   `create_music_page` -> `views/music_view.py`
-   `create_modules_page` -> `views/modules_view.py`
-   `create_config_general_frame` -> `views/config/general_view.py`
-   `create_config_music_frame` -> `views/config/music_view.py`
-   `create_config_ai_frame` -> `views/config/ai_general_view.py`
-   `create_config_ai_settings_frame` -> `views/config/ai_settings_view.py`
-   `create_config_ai_engine_frame` -> `views/config/ai_engine_view.py`

#### Paso 8: Migración de los Editores de IA

-   `create_ai_identity_frame` -> `views/ai/identity_editor.py`
-   `create_ai_moods_frame` -> `views/ai/moods_editor.py`
-   `create_ai_moods_history_frame` -> `views/ai/moods_history_editor.py`
-   `create_ai_users_frame` -> `views/ai/users_editor.py`
-   `create_ai_memory_frame` -> `views/ai/memory_editor.py`
-   `create_ai_opinions_frame` -> `views/ai/opinions_editor.py`
-   `create_ai_ranges_frame` -> `views/ai/ranges_editor.py`
-   `create_ai_self_frame` -> `views/ai/self_editor.py`
-   `create_ai_prompts_frame` -> `views/ai/prompts_editor.py`
    -   *Nota de Refactorización*: En todos estos editores (usuarios, memoria, opiniones, rangos), reemplazar los múltiples botones de "Guardar" individuales por fila, por un único botón global de "Guardar Cambios" ubicado en la parte inferior junto a "Recargar".

#### Paso 9: Migración de las Guías

-   `create_discord_guide_frame` -> `views/guides/discord_guide_view.py`
-   `create_google_guide_frame` -> `views/guides/google_guide_view.py`
-   `create_id_guide_frame` -> `views/guides/id_guide_view.py`
-   `create_privacy_guide_frame` -> `views/guides/privacy_guide_view.py`
-   `create_local_guide_frame` -> `views/guides/local_guide_view.py`

#### Tarea de Usabilidad: Reorganización del Menú de Configuración de IA y Nuevas Funciones
-   **Problema**: La configuración de IA está fragmentada y carece de opciones avanzadas para gestionar personalidades y reseteos precisos.
-   **Solución**: Centralizar todas las configuraciones de la IA bajo su propio submenú y mejorar drásticamente la UX.
    1.  Eliminar el botón "🤖 Motores de IA" de la barra lateral de configuración principal.
    2.  Añadir un nuevo botón "🧠 Núcleo Cognitivo (Motor)" en la barra lateral de ajustes de IA (`config_ai_engine_view.py`).
    3.  Renombrar "💥 Amnesia Selectiva" a "🔄 Restablecer" y moverlo a la configuración de IA. Deberá tener una interfaz de dos pestañas (similar a "Autoconcepto"). La primera pestaña ("Memorias" por defecto) permitirá selección granular, incluyendo menús expandibles para archivos compuestos (ej. hacer clic en "Autoconcepto" para desplegar y seleccionar borrar solo "Gustos" u "Opiniones").
    4.  Crear una nueva vista "🎭 Personalidades Prefabricadas" (`views/config/ai_presets_view.py`) planificada desde ya.
        - Contendrá un desplegable para seleccionar la personalidad (inicialmente solo la "Por Defecto").
        - Un panel informativo mostrando los detalles (identidad, personalidad, gustos, etc.) de la selección actual.
        - Un menú expandible inferior para elegir qué importar y qué conservar del bot actual. Incluirá la opción de limpiar registros o ponerlos por defecto (usuarios conocidos, relaciones), ya que las relaciones pueden ser inherentes a la personalidad importada.
        - Un botón de "Guardar" precedido por una advertencia nativa integrada en la propia interfaz (sin ventanas emergentes/popups, consistente con los colores y la caja `warn_box` del resto del sistema).


### Fase 3: Estabilización Post-Refactorización

#### Paso 10: Implementación de Sistema de Logging Real
Los múltiples bloques `except Exception as e: pass` a lo largo del código están ocultando fallos silenciosos críticos en las llamadas a APIs o la música.
1.  Crear una carpeta `logs/`.
2.  Configurar el módulo estándar `logging` de Python en el arranque de `launcher.py` y `meowSick.py` para que escriba automáticamente en `logs/system.log` con rotación (para no llenar el disco con archivos gigantes).
3.  Buscar sistemáticamente todos los bloques `except: pass` en los *cogs* y la UI.
4.  Sustituirlos por `logger.error("Descripción del contexto", exc_info=True)` para mantener un registro detallado de excepciones sin provocar crasheos.

#### Paso 11: Afectaciones a Otros Archivos (`build.py` y Config)
1.  **`build.py`**: Actualizar las banderas `--hidden-import` o `--collect-all` de PyInstaller para incluir la nueva carpeta `views/` y los módulos `shared/`. Modificar la función `create_clean_dist_files()` para que genere automáticamente la carpeta `settings/locales/` y la carpeta de `themes/` al crear una compilación limpia.
2.  **`config.json`**: Añadir parámetros globales (ej. `"language": "es"`, `"theme": "dark"`) para recordar las preferencias del usuario.

#### Tarea de Corrección: Unificar y Reparar Sistema de Restablecimiento (Factory Reset)
-   **Problema**: El reseteo de IA está fragmentado ("Amnesia Selectiva" vs "Restablecer a fábrica"). Usa valores hardcodeados incompletos, los rangos de afinidad tienen saltos bruscos, y no permite borrar partes específicas de un mismo archivo compuesto.
-   **Solución**: Centralizar la lógica de reseteo para que lea las plantillas originales completas (las de `build.py`). Integrarlo con la nueva UI de selección granular expansible. Ajustar los rangos de afinidad base para mayor granularidad (ej: 50-70, 71-85, 86-100) y asegurarse de que el botón de reseteo restaure estos rangos correctamente.

#### Tarea de Corrección: Refinar Valores por Defecto de la IA
-   **Problema**: La IA se enoja demasiado rápido, ignora la lista de *estados_posibles* inventando los suyos propios, y la identidad inicial es demasiado volátil.
-   **Solución**: 
    1. Ajustar la personalidad base a un lienzo en blanco neutral/estable.
    2. Modificar el prompt de `evolucion_analisis` aplicando una directriz estricta que obligue a la IA a elegir **exclusivamente** de los estados de la lista (o una combinación de ellos), penalizando la invención de emociones no registradas.

#### Tarea de Corrección: Solucionar Bugs de Auto-Reconocimiento y Duplicidad en Memoria
-   **Problema**: La IA se reconoce a sí misma en el chat como un usuario externo, añadiendo su propio ID a `known_users.json` o `memoria.json`. Además, en ocasiones se generan entradas duplicadas para los mismos usuarios.
-   **Solución**: 
    - Añadir validaciones estrictas en el pipeline de memoria (registro de usuarios y extracción de hechos) para ignorar siempre el ID del bot (`self.bot.user.id`).
    - Implementar verificaciones de unicidad sólidas para fusionar o evitar registros de usuarios repetidos.

### Fase 4: Documentación General (`README.md`)

Una vez que la estructura del código esté limpia y estabilizada, se procederá a actualizar el archivo `README.md` para reflejar el estado real de MeowSick V3.

#### Paso 12: Guía de Usuario
Redactar una sección clara y amigable orientada a quienes solo quieren ejecutar el bot: despliegue portable, configuración de credenciales en el Launcher y listado exhaustivo de comandos/uso en Discord (Música, Voz, IA, etc).

#### Paso 13: Guía del Desarrollador (Arquitectura)
Documentar a fondo la arquitectura técnica interna para futuros mantenedores: estructura de los nuevos módulos MVC (`views/`, `shared/`), el sistema IPC (Comunicación Launcher-Bot), el ecosistema cognitivo/modular de los cogs (`core`, `evolution`, `memory`) y el pipeline del motor asíncrono de música.

### Fase 5: Mejoras de Arquitectura y Desacoplamiento

Una vez que el código esté refactorizado y documentado, se pueden abordar problemas arquitectónicos más profundos para aumentar la robustez y flexibilidad del sistema.

#### Tarea 14: Desacoplamiento del Script de Compilación (`build.py`)
-   **Problema**: El script `build.py` contiene copias hardcodeadas de todos los archivos de configuración y memoria por defecto (`config.json`, `outputs.json`, `prompts.json`, etc.). Si se añade una nueva opción de configuración en el código, es necesario acordarse de actualizarla manualmente en `build.py`, lo que es muy propenso a errores y desincronización.
-   **Solución**: Modificar `build.py` para que, en lugar de tener el contenido en el propio script, lea los archivos de configuración del entorno de desarrollo y simplemente los copie a la carpeta de distribución, purgando únicamente los valores sensibles (como tokens y API keys).

#### Tarea 15: Abstracción de Motores Multimodales (TTS/STT)
-   **Problema**: La lógica para manejar los diferentes motores de Texto-a-Voz (Edge-TTS, Piper) y Voz-a-Texto (Whisper) está mezclada directamente dentro de `cogs/AI/core.py`.
-   **Solución**: Crear clases `TTSManager` y `STTManager` en `cogs/AI/utils.py`. Estas clases encapsularán la lógica específica de cada motor, permitiendo que `core.py` simplemente llame a `tts_manager.speak(text)` sin preocuparse por la implementación subyacente. Esto facilitará enormemente la adición de nuevos motores en el futuro (ej. ElevenLabs, Coqui).

#### Tarea 16: Extracción de "Valores Mágicos" a Configuración
-   **Problema**: El código contiene numerosos valores "mágicos" hardcodeados que afectan directamente el comportamiento del bot y no pueden ajustarse desde el Launcher.
-   **Solución**: Extraer los siguientes parámetros y moverlos a `config.json` con su respectiva opción en la UI:
    -   **`cogs/AI/core.py`**:
        -   `random.random() < 0.05` -> Probabilidad de respuesta espontánea (5%).
        -   `now - last < 3.0` -> Cooldown estricto anti-spam (3 segundos).
        -   `limit = min(limit, 5)` -> Reducción de mensajes al procesar contexto en Modo Gamer.
        -   `beam_size=5` -> Nivel de precisión/búsqueda del modelo Whisper (STT local).
    -   **`cogs/music.py`**:
        -   `YTDL_OPTIONS` -> Opciones de extracción de YouTube (ej. `'format': 'bestaudio/best'`).
        -   `FFMPEG_OPTIONS` -> Argumentos de red (`-reconnect_delay_max 5`).
        -   `await asyncio.sleep(60)` -> Tiempo exacto de inactividad antes de la auto-desconexión.
        -   `MAX_RETRIES = 3` -> Límite de reintentos cuando falla la extracción de una canción.
        -   `timeout=60` -> Caducidad (en segundos) de los botones interactivos de la cola (`QueueView`).
    -   **`cogs/AI/utils.py`**:
        -   `"repeat_penalty": 1.1` -> Penalización de repetición al llamar a Ollama.
        -   `aiohttp.ClientTimeout(total=180)` -> Tiempo máximo de espera (Timeout) para modelos locales pesados.

#### Tarea 17: Robustecimiento del Sistema IPC
-   **Problema**: La comunicación entre el Launcher y el Bot se basa en el parseo de strings con prefijos (`IPC_PROGRESS:`, `CMD_MUSIC:`). Este método es frágil; un cambio en un `print` o un error de formato puede romper la comunicación. Además, la invocación de comandos desde el Launcher depende de un "hack" que reutiliza el último contexto de un canal, lo cual no es fiable.
-   **Solución (A Largo Plazo)**: Investigar y migrar a un sistema IPC más robusto. Opciones:
    1.  **Sockets Locales**: Establecer un servidor de sockets simple en el bot al que el Launcher se conecte para enviar y recibir comandos JSON estructurados.
    2.  **API REST Local**: Levantar un micro-servidor web (ej. con `aiohttp`) en el proceso del bot que exponga endpoints para controlarlo (`/music/play`, `/ai/reload`).

---

## 5. Checklist de Progreso

**Fase 1: Cimientos y Resolución de Deuda Técnica (Core)**
- [ ] Paso 1: Centralización del Gestor de Estado (`shared/config_manager.py`)
  - [ ] Crear módulo `shared/config_manager.py`.
  - [ ] Implementar `load_json` y `save_json` seguros con `threading.Lock()`.
  - [ ] Reemplazar llamadas locales duplicadas en `launcher.py`, `meowSick.py`, `music.py` y `memory.py`.
- [ ] Paso 2: Extracción de Temas y Estilos Visuales (`themes/dark.json`)
  - [ ] Crear archivo base `themes/dark.json` con la paleta de colores.
  - [ ] Crear clase `ThemeManager`.
- [ ] Paso 3: Sistema Base de Idiomas (`settings/locales/es.json`)
  - [ ] Crear carpeta `settings/locales/` y archivo `es.json`.
  - [ ] Crear clase `LanguageManager`.
- [ ] Paso 4: Estandarización de Variables de Entorno (`python-dotenv`)
  - [ ] Eliminar funciones manuales `load_env_dict` y `update_env_key` de `launcher.py`.
  - [ ] Implementar guardado y carga oficial con `dotenv.set_key()`.

**Fase 2: Refactorización y División de la UI**
- [ ] Paso 5: Preparar `launcher.py` para la Carga Perezosa
  - [ ] Limpiar `__init__` eliminando las llamadas iniciales `create_*_page()`.
  - [ ] Actualizar `show_frame()` para instanciación dinámica (Lazy Loading).
  - [ ] Instanciar `ThemeManager`, `LanguageManager` y `ConfigManager` inyectándolos como dependencias.
- [ ] Paso 6: Migrar Vista Dashboard (`views/dashboard_view.py`)
  - [ ] Crear clase `DashboardFrame`.
  - [ ] Mover código de `create_dashboard()` y adaptarlo al controlador.
  - [ ] Aplicar inyección de idiomas y temas.
- [ ] Paso 7: Migrar Vistas Principales Iterativamente
  - [ ] `views/music_view.py`
  - [ ] `views/modules_view.py`
  - [ ] `views/config/general_view.py`
  - [ ] `views/config/music_view.py`
  - [ ] `views/config/ai_general_view.py`
  - [ ] `views/config/ai_settings_view.py`
  - [ ] `views/config/ai_engine_view.py`
  - [ ] `views/config/ai_presets_view.py` (Nueva vista de Personalidades)
- [ ] Paso 8: Migrar Editores de IA
  - [ ] Reemplazar botones de "Guardar" individuales por un botón global unificado por vista.
  - [ ] `views/ai/identity_editor.py`
  - [ ] `views/ai/moods_editor.py`
  - [ ] `views/ai/moods_history_editor.py`
  - [ ] `views/ai/users_editor.py`
  - [ ] `views/ai/memory_editor.py`
  - [ ] `views/ai/opinions_editor.py`
  - [ ] `views/ai/ranges_editor.py`
  - [ ] `views/ai/self_editor.py`
  - [ ] `views/ai/prompts_editor.py`
- [ ] Paso 9: Migrar Guías
  - [ ] `views/guides/discord_guide_view.py`
  - [ ] `views/guides/google_guide_view.py`
  - [ ] `views/guides/id_guide_view.py`
  - [ ] `views/guides/privacy_guide_view.py`
  - [ ] `views/guides/local_guide_view.py`
- [ ] Tarea de Usabilidad: Reorganizar Menú de Configuración de IA
  - [ ] Eliminar botón de motores del menú de configuración general.
  - [ ] Añadir botón "Núcleo Cognitivo" en el submenú de IA.
  - [ ] Implementar vista "Restablecer" con pestañas y selección granular expansible.
  - [ ] Añadir menú de "Personalidades Prefabricadas" con selector, info, y alerta nativa integrada.

**Fase 3: Estabilización Post-Refactorización**
- [ ] Paso 10: Implementar Sistema de Logging Real (`logs/system.log`)
  - [ ] Configurar módulo `logging` con rotación al arrancar `launcher.py` y `meowSick.py`.
  - [ ] Reemplazar bloques `except: pass` silenciosos en Cogs (`music.py`, `memory.py`, etc).
  - [ ] Reemplazar bloques `except: pass` en la nueva UI (`views/`).
- [ ] Paso 11: Actualizar `build.py` y configuración global
  - [ ] Ajustar `hidden-import` y `collect-all` en PyInstaller para las nuevas carpetas.
  - [ ] Actualizar la función generadora de entorno limpio en el script de compilación.
  - [ ] Añadir los parámetros globales `language` y `theme` al `config.json`.
- [ ] Tarea de Corrección: Unificar y Reparar Sistema de Restablecimiento
  - [ ] Unificar lógica de "Restablecer" con la plantilla base de memoria completa.
  - [ ] Soportar reseteo parcial de archivos (ej. resetear gustos pero no opiniones).
  - [ ] Ajustar rangos de afinidad por defecto para mayor granularidad (eliminar salto 50-100).
- [ ] Tarea de Corrección: Refinar Valores y Prompts
  - [ ] Estandarizar personalidad base como neutral/estable.
  - [ ] Modificar prompt de evolución para bloquear invención de estados de ánimo no listados.
- [ ] Tarea de Corrección: Bugs de Memoria y Auto-Reconocimiento
  - [ ] Bloquear que el bot registre su propio ID en `known_users.json` y `memoria.json`.
  - [ ] Añadir validación de unicidad para evitar entradas duplicadas de usuarios.

**Fase 4: Documentación General (`README.md`)**
- [ ] Paso 12: Redactar Guía de Usuario
  - [ ] Detallar instalación y despliegue portable.
  - [ ] Listar comandos disponibles en Discord.
  - [ ] Explicar ajustes en el Panel de Control.
- [ ] Paso 13: Redactar Guía del Desarrollador (Arquitectura)
  - [ ] Explicar el nuevo stack tecnológico y el patrón MVC implementado.
  - [ ] Detallar el Sistema IPC (Comunicación Launcher-Bot).
  - [ ] Documentar el Pipeline Cognitivo / IA.
  - [ ] Documentar el motor asíncrono musical.

**Fase 5: Mejoras de Arquitectura y Desacoplamiento**
- [ ] Tarea 14: Desacoplar Script de Compilación (`build.py`)
  - [ ] Forzar lectura de configuraciones locales dinámicamente en lugar de escribirlas en código.
- [ ] Tarea 15: Abstraer Motores Multimodales
  - [ ] Crear clase gestora `TTSManager` en `utils.py`.
  - [ ] Crear clase gestora `STTManager` en `utils.py`.
- [ ] Tarea 16: Extraer "Valores Mágicos" a `config.json`
  - [ ] Parametrizar variables de probabilidad y timeouts en IA (`core.py`, `utils.py`).
  - [ ] Parametrizar opciones de descarga, red y tiempos de espera en `music.py`.
- [ ] Tarea 17: Robustecer el Sistema IPC
  - [ ] Evaluar y preparar la transición a un modelo de Sockets o API REST local asíncrona.