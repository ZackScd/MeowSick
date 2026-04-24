# Registro de Cambios (Changelog) - MeowSick V3

Todas las modificaciones, refactorizaciones y nuevas implementaciones realizadas durante este proceso serán registradas aquí en orden cronológico.

## [Unreleased] - Fase 1: Cimientos

### Añadido
- Creado el gestor centralizado `ConfigManager` en `shared/config_manager.py` con protección segura `filelock`.
- Diseñado un plan de refactorización específico en el `ROADMAP.md` para `launcher.py`, subdividido en 10 bloques funcionales para mitigar riesgos durante la migración de archivos.

### Modificado
- Aplicado el `ConfigManager` a `meowSick.py` para lectura/escritura unificada.
- Aplicado el `ConfigManager` a `cogs/music.py` para lectura segura de la configuración musical.
- Aplicado el `ConfigManager` a `cogs/AI/utils.py` (Singleton `AIManager`), eliminando el caché interno de configuraciones para garantizar un Hot-Reloading efectivo.
- Aplicado parcialmente el `ConfigManager` a `cogs/AI/memory.py` (métodos `load_data` y `save_data`).
- Aplicado el `ConfigManager` a las funciones restantes de `cogs/AI/core.py`, asegurando que `_get_config` y la lectura de prefijos utilicen el gestor centralizado.
- Aplicado el `ConfigManager` en la lectura local y métodos base de `cogs/AI/memory.py`, `cogs/AI/evolution.py` y `cogs/AI/identity.py` (gestión del subconsciente de la IA y base de datos RAG local).
- Aplicado el `ConfigManager` al Bloque 1 del `launcher.py` (`update_module_state`, `toggle_module`), erradicando `open()` nativo en la gestión de módulos.
- Aplicado el `ConfigManager` al Bloque 2 del `launcher.py` (`open_amnesia_dialog`), estandarizando el reseteo de fábrica de los archivos JSON de memoria.
- Aplicado el `ConfigManager` al Bloque 3 del `launcher.py`, mejorando la estabilidad de lectura/escritura en los editores de "Estados de Ánimo" de la IA.
- Aplicado el `ConfigManager` al Bloque 4 del `launcher.py`, securizando la vista y limpieza del historial emocional del bot.
- Aplicado el `ConfigManager` al Bloque 5 del `launcher.py`, protegiendo la carga, creación, borrado y edición del registro de usuarios (`known_users.json`).
- Aplicado el `ConfigManager` al Bloque 6 del `launcher.py`, unificando la gestión de la base de datos de "Hechos" de la IA (`memoria.json`).
- Aplicado el `ConfigManager` al Bloque 7 del `launcher.py`, securizando el editor de Relaciones y Opiniones de la IA.
- Aplicado el `ConfigManager` al Bloque 8 del `launcher.py`, mejorando la edición y guardado de los rangos de afinidad de la IA (`afinidad_rangos.json`).
- Aplicado el `ConfigManager` al Bloque 9 del `launcher.py`, simplificando y securizando el acceso al autoconcepto de la IA (`autoconcepto.json`).
- Aplicado el `ConfigManager` al Bloque 10 del `launcher.py`, finalizando el Paso 1.1 al securizar la lectura y edición de los Prompts del Sistema (`prompts.json`).

### Añadido (Fase 2)
- Creado el gestor de temas `ThemeManager` en `shared/theme_manager.py` para la carga dinámica de paletas de colores.
- Extraída la paleta de colores por defecto a `themes/dark.json`, desacoplando los estilos visuales del código del `launcher.py`.

### Modificado (Fase 2)
- **Bloque 1 (`launcher.py`)**: Instanciado el `ThemeManager` en el inicializador (`__init__`) de `MeowLauncher`. 
- Erradicadas las referencias estáticas y "hardcodeadas" al diccionario global `COLORS` en la Ventana Principal y la Barra Lateral Completa (Dashboard, Navegación Principal, Submenús de Configuración y Submenús de IA).
- Estas secciones de la UI ahora inyectan dinámicamente sus colores (fondos, botones, bordes, scrollbars y fuentes) utilizando `self.theme_manager.get("color")`, dejando la estructura preparada para soportar múltiples temas en la refactorización final.
- **Bloque 2 (`launcher.py`)**: Migrada la vista del Dashboard (`create_dashboard`) y sus funciones satélite de actualización de estado (`start_bot`, `_update_progress`, `_reset_ui_stopped`) para utilizar los colores dinámicos del `ThemeManager`.
- **Bloque 3 (`launcher.py`)**: Desacoplados los colores de las páginas "Música" (`create_music_page`) y "Módulos" (`create_modules_page`). Los botones de control multimedia, la consola filtrada de música y las tarjetas informativas de los módulos ahora leen sus propiedades visuales desde el `ThemeManager`.
- **Bloque 4 (`launcher.py`)**: Extraídos todos los colores "hardcodeados" en las pantallas "Configuración General" (`create_config_general_frame`) y "Configuración de Música" (`create_config_music_frame`). Las tarjetas de credenciales, los inputs de texto, y los labels dinámicos de éxito/error ahora dependen exclusivamente del gestor centralizado de temas.
- **Bloque 5 (`launcher.py`)**: Refactorizadas las vistas de configuración de IA (`create_config_ai_frame`, `create_config_ai_settings_frame`, `create_config_ai_engine_frame` y sus funciones satélite de guardado) para utilizar el `ThemeManager` de manera exclusiva, eliminando las dependencias estáticas de colores.
- **Bloque 6 (`launcher.py`)**: Migrados los colores de los editores de memoria de la IA (Identidad, Estados de Ánimo e Historial) para que utilicen el `ThemeManager`, asegurando que los fondos, textos, botones y ventanas emergentes de estas secciones sean dinámicos.
- **Bloque 7 (`launcher.py`)**: Refactorizadas las vistas de edición de "Usuarios", "Memoria de Hechos" y "Relaciones/Opiniones" para que sus componentes visuales (tarjetas, inputs, botones y diálogos emergentes) dependan del `ThemeManager`.
- **Bloque 8 (`launcher.py`)**: Migrados los colores de los editores de memoria restantes (Rangos de Afinidad, Autoconcepto y Prompts del Sistema) para que dependan exclusivamente del `ThemeManager`. También se adaptó la renderización condicional (colores del canvas) en la barra interactiva de rangos.
- **Bloque 9 (`launcher.py`)**: Extraídos los colores estáticos de todas las Guías de Ayuda (`create_discord_guide_frame`, `create_google_guide_frame`, `create_id_guide_frame`, `create_privacy_guide_frame`, `create_local_guide_frame`), delegando los fondos, bordes y fuentes de los textos al `ThemeManager`.
- **Bloque 10 y Limpieza Final (`launcher.py`)**: Desacopladas las funciones utilitarias y de guardado (`toggle_password`, `update_module_state`, `save_env`). **Se eliminó exitosamente el diccionario estático global `COLORS`**. La interfaz gráfica ahora depende al 100% del gestor de temas dinámicos.

### Añadido (Fase 3)
- Creado el sistema base de idiomas `LanguageManager` en `shared/language_manager.py`.
- Añadidos los archivos base `es.json` y `en.json` en `settings/locales/` para comenzar la extracción paulatina de los textos de la interfaz gráfica.
- **Bloque 1 (`launcher.py`)**: Migrados los textos estáticos de la Ventana Principal, la Barra Lateral y todos los submenús de navegación hacia el archivo `es.json`. La UI ahora solicita estos textos dinámicamente mediante el `LanguageManager`.
- **Bloque 2 (`launcher.py`)**: Extraídos los textos de la página Dashboard (Etiquetas de estado, botones y consolas) y la página de Módulos (Títulos, descripciones largas y botones de activación) hacia `es.json`.
- **Bloque 3 (`launcher.py`)**: Extraídos los textos, controles y consolas de la vista del Reproductor de Música (`create_music_page`), junto con las descripciones, ayudas y títulos de la ventana de Configuración Musical (`create_config_music_frame`) hacia `es.json`.
- **Bloque 4 (`launcher.py`)**: Extraídos los textos estáticos de la pestaña de Configuración General (`create_config_general_frame`) hacia `es.json`.
- **Bloque 5 (`launcher.py`)**: Desacoplados y extraídos todos los textos correspondientes a los ajustes de Inteligencia Artificial (Subprocesos, Filtros y Límites, Motores y Credenciales) en `es.json`.
- **Bloque 6 (`launcher.py`)**: Extraídos de forma nativa los títulos, placeholders, diálogos emergentes y tooltips de ayuda de los editores de "Identidad", "Estados de Ánimo", "Historial de Estados", "Autoconcepto" y "Prompts del Sistema" hacia el archivo `es.json`.
- **Bloque 7 (`launcher.py`)**: Extraídos los textos de las vistas de edición "Registro de Usuarios", "Memoria de Hechos", "Relaciones y Afinidad" y "Rangos de Afinidad" hacia el archivo base de idioma `es.json`.
- **Bloque 8 (`launcher.py`)**: Extraídos los textos de las Ventanas Emergentes (Amnesia Selectiva y mensajes de diálogo asociados) hacia `es.json`.
- **Bloque 9 (`launcher.py`)**: Extraídos los textos masivos de las Guías de Ayuda (Discord, Google, IDs, Privacidad, Local) hacia `es.json`, reduciendo significativamente el peso visual del archivo de código.
- **Bloque 10 y Limpieza Final (`launcher.py`)**: Extraídos todos los mensajes residuales de la consola local (`[LAUNCHER]...`) y alertas de error genéricas hacia el archivo de idioma. **El archivo `launcher.py` ha sido completamente purgado de textos en español**.
- Creados los archivos de mensajes del bot `outputs_es.json` y `outputs_en.json` en `settings/locales/`, reemplazando el archivo estático `outputs.json` para dar soporte multi-idioma (Paso 3.2).
- Adaptado `launcher.py` en la vista de Configuración General y Configuración de Música para que lea y edite correctamente `outputs_XX.json` basándose en el idioma activo (Paso 3.2).
- Adaptados `meowSick.py` y `cogs/music.py` para cargar los mensajes de respuesta dinámicamente según el idioma configurado en `config.json` (Paso 3.2).
- Implementada la inyección dinámica de idioma en los Prompts de la IA (`cogs/AI/identity.py` y `cogs/AI/memory.py`), forzando al ecosistema cognitivo a analizar y generar texto/JSON estrictamente en el idioma configurado en el sistema (Paso 3.3).
