# 🐱 MeowSick - Guía Completa (Usuario y Desarrollador)

MeowSick es un framework para crear un Bot de Discord Multimodal avanzado, diseñado bajo una arquitectura modular y 100% portátil. A diferencia de los bots tradicionales que corren como scripts de terminal, MeowSick integra una **Interfaz Gráfica de Usuario (GUI) nativa**, un motor de **Reproducción Musical** robusto, y un ecosistema de **Inteligencia Artificial Cognitiva** capaz de ver, escuchar, hablar, buscar en internet y simular memoria a largo plazo con emociones.

*Nota: Aunque el proyecto se llama "MeowSick", el bot adopta dinámicamente el nombre y la identidad que tú le configures en tu servidor.*

---

## 🌟 Características Principales

1. **Despliegue Portable (Standalone):** No requiere que el usuario final instale Python, Node.js, Docker ni configure bases de datos (SQL/Mongo). Todo el código, las dependencias de red, y los binarios de C++ (FFmpeg) se empaquetan en un único archivo ejecutable (`.exe`) para Windows.
2. **Control en Interfaz Gráfica (GUI):** Cuenta con un panel de control local de escritorio construido en `CustomTkinter` que permite monitorear consolas, alterar prompts, editar recuerdos de la IA y encender/apagar submódulos en caliente (Hot-Reloading) sin apagar el bot.
3. **IA Cognitiva Local (Pseudo-RAG):** El bot no usa memoria contextual simple. Posee una base de datos de grafos de conocimiento en disco (archivos JSON) que actúa como un sistema RAG (Retrieval-Augmented Generation) interno, inyectando hechos y opiniones del usuario en milisegundos antes de que la IA genere una respuesta.
4. **Comportamiento Emergente y Decaimiento:** El bot altera su propio estado de ánimo leyendo el chat. Si no se le habla durante ciertas horas, sus emociones decaen hacia un estado neutral.
5. **Interacción Multimodal:** Capacidad de leer imágenes, transcribir y procesar mensajes de voz en tiempo real, hablar mediante Texto-a-Voz (TTS) neuronal y realizar búsquedas web autónomas.

---
---

#  PARTE 1: GUÍA DE USUARIO

Esta sección está destinada a las personas que solo quieren ejecutar el bot en su servidor de Discord.

## 🚀 Instalación Rápida

1. Ejecuta `MeowSick.exe` (o `python launcher.py` si estás en el código fuente).
2. Ve a la pestaña **Configuración > 🔐 Credenciales**.
3. Pega tu **Token de Discord** (Puedes usar el botón "Guía" en la app para saber cómo obtenerlo).
4. Pega tu **Google AI Key (Gemini)** en caso de querer usar el motor de IA (Obtenida de Google AI Studio, es gratuita).
5. Opcional, pero recomendado: Añade **tu ID de discord** en la configuración general.
6. Guarda los cambios, ve a la pestaña **Dashboard** y haz clic en **▶ Iniciar Bot**.

## 🎮 Comandos Disponibles

### 🧠 Inteligencia Artificial
MeowSick funciona de manera orgánica. **No necesitas comandos** para hablarle en texto. Simplemente **menciónalo (`@NombreDeTuBot`)**, responde a uno de sus mensajes, o envíale un mensaje directo (DM).

*   **Visión:** Si envías una imagen (PNG, JPG) junto a tu mensaje, ella la mirará y te dará su opinión basándose en su personalidad.
*   `!ask [pregunta]`: Fuerza a la IA a buscar información en internet en tiempo real (Noticias, clima, etc) y responder en base a los resultados.
*   `!reloadai`: (Solo Admin) Recarga la memoria de la IA en caliente.

### 🎙️ Comandos de Voz y Multimodal
*   `!voice`: Invoca al bot a tu canal de voz. A partir de ese momento, cualquier respuesta de texto que la IA genere, también la leerá en voz alta usando redes neuronales (TTS). *Vuelve a escribirlo para apagarlo.*
*   `!talk`: Despliega un panel interactivo con un botón verde en el chat.
    *   Haz clic en **🎙️ Hablar**, habla por tu micrófono en el canal de voz de Discord.
    *   Haz clic de nuevo para detener. La IA procesará tu audio y te responderá hablando.

### 🎵 Música
*   `!play [canción o URL]`: Busca en YouTube y reproduce la canción.
*   `!stop`: Detiene la música y vacía la cola.
*   `!skip`: Salta a la siguiente canción.
*   `!pause` / `!resume`: Pausa o reanuda la música.
*   `!list`: Muestra la cola actual de canciones.
*   `!shuffle`: Mezcla el orden de las canciones en la cola.
*   `!leave`: Desconecta al bot del canal de voz.
*   `!playlist` / `!pls`: Carga automáticamente tu playlist favorita (configurable desde el Launcher en Ajustes de Música).

## ⚙️ Personalización en el Launcher
El Panel de Control de MeowSick te permite alterar su "cerebro" en tiempo real desde la pestaña **Configuración > 🧠 IA General**:
*   **Editores de Memoria:** Puedes forzar a la IA a que le "guste" o "odie" a un usuario específico editando su nivel de Afinidad (-100 a 100).
*   **Personalidad:** Puedes cambiar quién es en la pestaña *Identidad*. ¿Quieres que sea un pirata sarcástico o una sirvienta amable? Solo edita el texto y guarda.
*   **Estados de Ánimo:** Crea nuevas emociones para que la IA transite por ellas dependiendo de cómo la traten los usuarios.

## 🛡️ Privacidad y Responsabilidad Legal
*   **Zero-Data-Retention:** Se recomienda encarecidamente a los usuarios utilizar la instalación de modelos locales (cuando esté disponible) para garantizar una privacidad absoluta de los chats de su servidor al evitar enviar datos a la nube.
*   **Aislamiento Total:** El desarrollador original **NO** recopila, monitorea, ni tiene acceso a NINGÚN tipo de dato, historial, Token o API Key de los usuarios. Cada instancia de MeowSick funciona de manera 100% aislada en la máquina de quien la ejecuta.
*   **Responsabilidad:** El creador se deslinda de cualquier uso indebido, malicioso o ilegal que se le dé a esta aplicación. La descarga, configuración y moderación del bot recaen puramente en la responsabilidad del usuario final.

---
---

# 💻 PARTE 2: GUÍA DEL DESARROLLADOR

Esta sección detalla la arquitectura interna para quienes deseen modificar el código fuente.

---

## 🛠️ Stack Tecnológico

- **Lenguaje Base:** Python 3.10+
- **Librería de Discord:** `discord.py` (Manejo de API y WebSockets, 100% asíncrono con `asyncio`).
- **Interfaz Gráfica e IPC:** `CustomTkinter` (GUI moderna), `Pillow` (Procesamiento de imágenes) y tuberías estándar (`sys.stdin` / `sys.stdout`) para comunicación entre procesos.
- **Inteligencia Artificial:** API de Google Gemini (`aiohttp` para peticiones asíncronas).
  - *Modelos Frontales:* `gemini-3-flash-preview` / `gemini-2.5-flash` (Respuestas rápidas).
  - *Modelos Analíticos (Fondo):* `gemma-3-27b-it` / `gemma-3-12b-it` (Extracción de datos).
- **Multimodalidad:** `edge-tts` (Generación de voz neuronal), `discord-ext-voice-recv` (Captura de sumideros de audio), `duckduckgo-search` (Scraping web asíncrono).
- **Motor de Música:** `yt-dlp` (Extracción optimizada) y `FFmpeg` (Codificación PCM / Opus).
- **Compilación y Empaquetado:** `PyInstaller` (Generación de ejecutables con inyección de metadatos Win32).

---

## 🏗️ Arquitectura del Sistema (IPC)

El programa opera mediante un paradigma de **Multiprocesamiento (IPC - Inter-Process Communication)**, dividiendo el sistema en dos piezas principales que se comunican entre sí en tiempo real:

1. **Proceso Padre (Launcher - `launcher.py`):** Dibuja la interfaz gráfica. Modifica archivos `.json` de configuración y memoria, y genera subprocesos Popen.
2. **Proceso Hijo (Daemon - `meowSick.py`):** Se conecta al WebSocket de Discord. Se ejecuta 100% asíncrono (`asyncio`).

**¿Cómo se comunican?**
- **Launcher -> Bot:** El Launcher inyecta comandos en la tubería `stdin`. El bot posee una corrutina `console_listener` que usa `loop.run_in_executor` para leer órdenes asíncronamente y disparar recargas o comandos internos.
- **Bot -> Launcher:** El Bot imprime variables JSON marcadas en consola (`stdout`). El Launcher las captura para actualizar elementos visuales en tiempo real (como la lista de canciones actual).

---

## 🧠 Ecosistema Cognitivo y Multimodal

La IA de MeowSick no es un chatbot tradicional de pregunta y respuesta; es un ecosistema de agentes paralelos diseñados para **simular procesos cognitivos humanos**. 

Para lograr esta ilusión de "vida", el cerebro del bot divide sus tareas asíncronamente simulando órganos reales:
- **Percepción (Sentidos):** Escucha audios, lee textos y observa imágenes en tiempo real.
- **Lóbulo Frontal (Conciencia):** El único agente encargado de generar palabras y hablar, ensamblando todo el contexto psicológico antes de emitir una respuesta.
- **Sistema Límbico (Emociones):** Un subproceso que lee pasivamente el ambiente del servidor para mutar la personalidad de la IA hacia el enojo, la tristeza o la felicidad de forma orgánica.
- **Hipocampo (Memoria):** Un juez social que filtra el ruido, evalúa numéricamente si alguien le cae bien o mal, y guarda recuerdos biográficos en el disco duro, evitando la "amnesia" típica de los LLMs comunes.

### 🔄 Flujo de Información (Pipeline Cognitivo)
El procesamiento de cada mensaje sigue un riguroso ciclo de vida asíncrono que simula la cognición humana:

1. **Recepción y Filtrado:** El bot lee un mensaje en Discord. Primero valida contra listas blancas (Whitelist) de canales y decide si debe ignorar a otros bots. 
2. **Bifurcación (Forking):** El mensaje se envía simultáneamente a los "buffers" (memoria RAM) del módulo de Emociones y del módulo de Memoria. Estos procesos corren en segundo plano (*Fire & Forget*) sin ralentizar al bot.
3. **Evaluación de Gatillo:** El bot evalúa: *¿Este mensaje requiere una respuesta activa?* (Mención, mensaje directo o respuesta directa). Si es falso, el bot simplemente "escucha", aprende silenciosamente y calla.
4. **Ensamblaje Psicológico (RAG Interno):** Si debe responder, `core.py` detiene todo y hace una recolección masiva de bases de datos locales:
   - *¿Quién soy?* (Identidad base)
   - *¿Cómo me siento ahora mismo?* (Estado de ánimo)
   - *¿Quién me habla?* (Ficha del usuario)
   - *¿Me cae bien esta persona?* (Afinidad y Relación)
   - *¿Qué hechos biográficos recuerdo de él/ella?* (Hechos concretos)
5. **Inyección y Petición:** Toda esta psicología se empaqueta en un gigantesco `System Prompt` que se envía a la API de Google Gemini junto con los últimos mensajes del chat para dar contexto temporal. En este paso decide si debe ver imágenes, escuchar audios o buscar en la web.
6. **Retroalimentación:** La IA genera la respuesta. El bot la envía a Discord (texto o voz neuronal) y se retroalimenta a sí mismo enviando lo que acaba de decir a sus propios módulos de memoria para ser consciente de sus propias palabras.

### 1. Conciencia Frontal y Multimodalidad (`core.py`)
Es el director de orquesta. 
- **Visión:** Intercepta `message.attachments`. Mide el peso límite configurado, descarga el binario a la RAM vía `att.read()`, lo codifica en Base64 y lo inyecta como `inlineData` en el payload de Google.
- **Voz (STT/TTS):** Genera un `WaveSink` filtrado por usuario (`voice_recv.UserFilter`) aislando el audio emitido en Discord. Envía ese WAV en Base64 a la API de Gemini 1.5. Cuando Gemini responde, lanza un subproceso asíncrono con `edge_tts` para descargar un `.mp3` temporal y enrutarlo al canal con `FFmpeg`.
- **Búsqueda Web:** Posee un selector algorítmico. Puede delegar la búsqueda al ecosistema nativo de Google (`tools: googleSearch`) o realizar scraping anónimo local inyectando sumarios de duckduckgo (`DDGS`) al prompt principal de contexto.

### 2. Módem de Comunicaciones (`utils.py`)
- **Cascada de Modelos:** Si Flash Preview falla, retrocede a Flash Latest automáticamente.
- **Rotación de Tokens:** Si la API devuelve Error 429 (Cuota Agotada), salta al siguiente `GEMINI_API_KEY_2` indexado en `.env` sin cancelar la ejecución en curso.

### 3. Subconscientes en Background
- **Subconsciente Emocional (`evolution.py`):** Absorbe mensajes en un buffer RAM. Llama a modelos densos (Gemma-27b) en segundo plano pidiendo que evalúen la trayectoria emocional del chat, alterando su propio estado base (ej: "Irritada" -> "Feliz").
- **Hipocampo de Memoria (`memory.py`):** Ejecuta 3 tareas simultáneas tras conversaciones largas:
  1. *Filtrado:* Extrae hechos biográficos (`memoria_filtrado`).
  2. *Juicio Social:* Evalúa matemáticamente (-100 a 100) la afinidad de un usuario (`memoria_opiniones`).
  3. *Autoconcepto:* Guarda cosas que la IA haya inventado sobre sí misma para no contradecirse en el futuro.

---

## 🎵 Motor de Música de Alto Rendimiento (Optimizado para YouTube)

El módulo de audio (`cogs/music.py`) no es un simple reproductor, sino un enrutador de streaming avanzado diseñado para ser a prueba de fallos, con protección contra caducidad de tokens y **optimizado específicamente para la extracción y reproducción en tiempo real desde YouTube**, logrando cero bloqueos de E/S (*I/O Bound*).

1. **Extracción Ultrarrápida (`yt-dlp` en modo Flat):** Al solicitar playlists masivas, utiliza el flag `extract_flat: in_playlist` para extraer solo URLs base, evitando colapsos de RAM o latencia infinita.
2. **Carga Perezosa Estricta:** Resuelve la URL M3U8 profunda de YouTube exactamente milisegundos antes del evento `play()` en lugar de precargarla, evadiendo los clásicos errores HTTP 403 por tokens caducados.
3. **Thread Pooling:** Desvía todas las operaciones síncronas de red a `loop.run_in_executor` manteniendo el bot receptivo.
4. **Reconexión FFmpeg:** Utiliza `-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5` para tolerar caídas de micro-red al transmitir paquetes Opus.

---

## 📦 Entorno de Compilación (`build.py`)

MeowSick utiliza un script propio para automatizar su despliegue y distribución.

1. **Entorno Limpio:** Antes de compilar, crea una carpeta temporal donde inyecta archivos `.json` de configuración y memoria totalmente vírgenes y libres de tokens personales.
2. **Inyección de Metadatos:** Genera un archivo de recursos de Windows (`version_info.txt`) que estampa el autor y la versión en el `.exe` final para evitar falsos positivos agresivos en Windows Defender.
3. **PyInstaller:** Inclusión agresiva de módulos ocultos (`yt-dlp`, `discord.ext.voice_recv`, `duckduckgo_search`) no detectables por análisis de AST.
4. **Distribución Portable:** Toma el `.exe`, la carpeta de configuraciones virgen y el binario externo de codificación de audio (`ffmpeg.exe`) y los consolida en `dist/MeowSick_portable`, listo para ejecutarse con doble clic en cualquier PC.