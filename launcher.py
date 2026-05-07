"""
Punto de Entrada Gráfico (Launcher) de MeowSick.

Este archivo actúa como el "Controlador" (Controller) en el patrón MVC.
Gestiona la ventana de CustomTkinter, orquesta la carga perezosa de las Vistas (Views),
y maneja la creación y comunicación multiproceso (IPC) con el Daemon de Discord (meowSick.py).
"""

import customtkinter as ctk
import subprocess
import sys
import os
import threading
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from tkinter import messagebox
from PIL import Image
from dotenv import set_key, dotenv_values
from shared.config_manager import ConfigManager
from shared.theme_manager import ThemeManager
from shared.language_manager import LanguageManager
from views.dashboard_view import DashboardFrame
from views.music.main_view import MusicFrame
from views.modules_view import ModulesFrame
from views.config.general_view import GeneralConfigFrame
from views.config.music_view import MusicConfigFrame
from views.config.ai_general_view import AIGeneralConfigFrame
from views.config.ai_settings_view import AISettingsConfigFrame
from views.config.ai_engine_view import AIEngineConfigFrame
from views.config.ai_amnesia_view import AIAmnesiaConfigFrame
from views.ai.identity_editor import IdentityEditor
from views.ai.moods_editor import MoodsEditor
from views.ai.users_editor import UsersEditor
from views.ai.memory_editor import MemoryEditor
from views.ai.opinions_editor import OpinionsEditor
from views.ai.ranges_editor import RangesEditor
from views.ai.self_editor import SelfEditor
from views.ai.prompts_editor import PromptsEditor
from views.guides.wizard_view import WizardView
from views.guides.ai_wizard_view import AIWizardView

# --- CONFIGURACIÓN DE RUTAS Y VISUAL ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    RUNTIME_DIR = getattr(sys, '_MEIPASS', BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RUNTIME_DIR = BASE_DIR

# Rutas relativas a la carpeta de usuario
SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
ENV_PATH = os.path.join(SETTINGS_DIR, ".env")

# --- CONFIGURACIÓN DE LOGGING ---
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler(os.path.join(LOGS_DIR, "system.log"), maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Launcher")

# Configuración global del motor gráfico
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("dark-blue")

class MeowLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Inicializar Gestor de Temas Dinámico
        self.theme_manager = ThemeManager(os.path.join(BASE_DIR, "themes"), "dark")
        
        # Inicializar Gestor de Idiomas
        config_data = ConfigManager.load_json(os.path.join(SETTINGS_DIR, "config.json"), use_lock=True) or {}
        lang_code = config_data.get("language", "es")
        self.lang_code = lang_code
        self.lang_manager = LanguageManager(os.path.join(SETTINGS_DIR, "locales"), lang_code)

        # Inyectar ConfigManager como dependencia del controlador
        self.config_manager = ConfigManager

        self.title(self.lang_manager.get("app_title"))
        self.geometry("1280x720")
        self.minsize(800, 600)
        self.configure(fg_color=self.theme_manager.get("bg_dark"))
        
        # Carga del ícono (Evitando fallos si el archivo es borrado)
        ico_path = os.path.join(RUNTIME_DIR, "res", "img", "meowSick_logo1x1_256x256.ico")
        if os.path.exists(ico_path):
            self.iconbitmap(ico_path)
        
        # Estados de control interno
        self.bot_process = None
        self.module_buttons = {}
        self.frames = {}
        self.ai_reload_functions = {}

        # Configuración del Grid principal (Barra lateral auto-ajustable vs Contenido expansible)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Inicialización de la interfaz
        self.create_sidebar()
        
        env_data = dotenv_values(ENV_PATH)
        token = env_data.get("DISCORD_TOKEN", "").strip()
        if not token:
            self.sidebar_frame.grid_remove() # Oculta la navegación
            self.show_frame(WizardView)
        else:
            self.show_frame(DashboardFrame)

        # Hook de interrupción al cerrar la ventana (X)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_frame(self, view_class):
        """
        Sistema de Enrutamiento y Carga Perezosa (Lazy Loading).
        Renderiza la vista solicitada. Si es la primera vez que se llama,
        la instancia en memoria, ahorrando recursos y acelerando el arranque inicial.
        """
        name = view_class.__name__
        
        if name not in self.frames:
            # Instanciamos la vista inyectando este Launcher como 'controller'
            self.frames[name] = view_class(parent=self, controller=self)
            
        # Oculta todas las vistas actualmente dibujadas
        for frame in self.frames.values():
            frame.grid_forget()
            
        # Dibuja la vista objetivo
        if name in self.frames:
            self.frames[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Control dinámico de la advertencia en la barra lateral de IA
        if hasattr(self, 'warning_box') and self.warning_box.winfo_exists():
            ai_editors = ["IdentityEditor", "MoodsEditor", "MoodsHistoryEditor", "UsersEditor", "MemoryEditor", "OpinionsEditor", "RangesEditor", "SelfEditor", "PromptsEditor"]
            if name in ai_editors:
                self.logo_frame.pack_forget()
                self.warning_box.pack(fill="x")
            else:
                self.warning_box.pack_forget()
                self.logo_frame.pack(fill="both", expand=True)

    def finish_wizard(self):
        """
        Método de transición llamado por el WizardView al terminar la configuración inicial.
        Restaura la UI, aplica el nuevo idioma/tema y lleva al Dashboard.
        """
        config_data = self.config_manager.load_json(os.path.join(SETTINGS_DIR, "config.json")) or {}
        self.lang_code = config_data.get("language", "es")
        
        if hasattr(self.lang_manager, "load_language"):
            self.lang_manager.load_language(self.lang_code)
            
        self.title(self.lang_manager.get("app_title"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.render_main_sidebar()
        self.show_frame(DashboardFrame)

    def _fix_scroll(self, widget):
        """
        Parche de Usabilidad para CustomTkinter.
        Permite que el scroll del mouse fluya hacia el contenedor padre general a menos
        que el puntero esté activamente enfocado dentro de un Textbox en particular.
        """
        def _on_mousewheel(event):
            if widget.focus_get() == widget._textbox:
                return
            
            # Escalamiento del árbol de jerarquía (DOM) para encontrar el ScrollableFrame padre
            parent = widget.master
            while parent:
                if isinstance(parent, ctk.CTkScrollableFrame) and hasattr(parent, "_parent_canvas"):
                    if sys.platform == "darwin": # macOS
                        parent._parent_canvas.yview_scroll(int(-1*(event.delta)), "units")
                    else: # Windows / Linux
                        parent._parent_canvas.yview_scroll(int(-1*(event.delta/6)), "units")
                    break
                parent = parent.master
            return "break"
        widget._textbox.bind("<MouseWheel>", _on_mousewheel)

    # --- BARRA LATERAL (ESTILO V2) ---
    def create_sidebar(self):
        """Construye los cimientos inmutables de la barra lateral izquierda."""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=self.theme_manager.get("bg_sidebar"), border_width=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False) # Fija la anchura independientemente del contenido
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        # 1. Contenedor superior (Logo corporativo o Bloque de Advertencias)
        self.top_sidebar_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", height=135)
        self.top_sidebar_container.grid(row=0, column=0, sticky="ew", padx=15, pady=(20, 0))
        self.top_sidebar_container.pack_propagate(False)

        self.logo_frame = ctk.CTkFrame(self.top_sidebar_container, fg_color="transparent")
        self.logo_frame.pack(fill="both", expand=True)
        
        logo_path = os.path.join(RUNTIME_DIR, "res", "img", "meowSick_logo1x1_1159x1159.png")
        if os.path.exists(logo_path):
            logo_img = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(72, 72))
            ctk.CTkLabel(self.logo_frame, image=logo_img, text="").pack(pady=(0, 5))
        else:
            ctk.CTkLabel(self.logo_frame, text="🐱", font=ctk.CTkFont(size=48), text_color=self.theme_manager.get("text_dim")).pack(pady=(0, 5))
            
        ctk.CTkLabel(self.logo_frame, text="MeowSick", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.theme_manager.get("accent")).pack(pady=(0, 10))

        # Warning Box (Oculta por defecto)
        self.warning_box = ctk.CTkFrame(self.top_sidebar_container, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("red"), border_width=1, corner_radius=8)
        ctk.CTkLabel(self.warning_box, text=self.lang_manager.get("sidebar_warning_title"), text_color=self.theme_manager.get("red"), font=ctk.CTkFont(weight="bold", size=12)).pack(pady=(10, 0))
        ctk.CTkLabel(self.warning_box, text=self.lang_manager.get("sidebar_warning_text"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), justify="center").pack(padx=10, pady=(5, 10))

        # 2. Contenedor Dinámico de Navegación (Su contenido cambia según el menú activo)
        self.nav_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_container.grid(row=1, column=0, sticky="nsew")

        # 3. Footer Estático
        ctk.CTkLabel(self.sidebar_frame, text=self.lang_manager.get("sidebar_version_footer"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11)).grid(row=2, column=0, pady=20)

        self.render_main_sidebar()

    def render_main_sidebar(self):
        """Destruye el menú actual e hidrata el nav_container con el menú principal de Raíz."""
        for widget in self.nav_container.winfo_children():
            widget.destroy()

        btn_opts = {"fg_color": self.theme_manager.get("bg_card"), "hover_color": self.theme_manager.get("border"), "text_color": self.theme_manager.get("text"), "height": 36, "corner_radius": 8, "anchor": "center"}
        
        # 1. Sección Superior (Dashboard, Módulos)
        top_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        top_frame.pack(side="top", fill="x")
        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_dashboard"), command=lambda: self.show_frame(DashboardFrame), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_modules"), command=lambda: self.show_frame(ModulesFrame), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        # 2. Separador Superior
        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="top", fill="x", padx=20, pady=10)

        # 3. Sección Inferior (Configuración) - Se empaqueta abajo primero para fijarlo
        bottom_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(bottom_frame, text=self.lang_manager.get("nav_config"), command=self.open_config_menu, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        
        # 4. Separador Inferior (Arriba de configuración)
        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="bottom", fill="x", padx=20, pady=10)

        # 5. Lista Desplazable de Atajos
        scroll_shortcuts = ctk.CTkScrollableFrame(
            self.nav_container, 
            fg_color="transparent", 
            corner_radius=0,
            scrollbar_button_color=self.theme_manager.get("bg_sidebar"),
            scrollbar_button_hover_color=self.theme_manager.get("bg_sidebar")
        )
        scroll_shortcuts.pack(side="top", fill="both", expand=True)
        
        # Lista de accesos directos
        ctk.CTkButton(scroll_shortcuts, text=self.lang_manager.get("nav_music"), command=lambda: self.show_frame(MusicFrame), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_shortcuts, text=self.lang_manager.get("nav_ai"), command=self.open_ai_menu, **btn_opts).pack(padx=(12, 0), pady=6, fill="x")

    def render_config_sidebar(self):
        """Navegación: Menú de Configuración Principal."""
        for widget in self.nav_container.winfo_children():
            widget.destroy()

        btn_opts = {"fg_color": self.theme_manager.get("bg_card"), "hover_color": self.theme_manager.get("border"), "text_color": self.theme_manager.get("text"), "height": 36, "corner_radius": 8, "anchor": "center"}

        # 1. Sección Superior (Volver, General)
        top_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        top_frame.pack(side="top", fill="x")

        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_back"), command=self.exit_config_menu, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_general"), command=lambda: self.show_frame(GeneralConfigFrame), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        # 2. Separador Superior
        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="top", fill="x", padx=20, pady=10)

        # 3. Lista de Módulos (Config)
        scroll_mods = ctk.CTkScrollableFrame(
            self.nav_container, 
            fg_color="transparent", 
            corner_radius=0,
            scrollbar_button_color=self.theme_manager.get("bg_sidebar"),
            scrollbar_button_hover_color=self.theme_manager.get("bg_sidebar")
        )
        scroll_mods.pack(side="top", fill="both", expand=True)
        
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_music_settings"), command=lambda: self.show_frame(MusicConfigFrame), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_settings"), command=self.open_config_ai_menu, **btn_opts).pack(padx=(12, 0), pady=6, fill="x")

    def open_config_menu(self):
        self.render_config_sidebar()
        self.show_frame(GeneralConfigFrame)

    def exit_config_menu(self):
        self.render_main_sidebar()
        self.show_frame(DashboardFrame)
        
    def render_config_ai_sidebar(self):
        """Navegación: Submenú de configuraciones avanzadas para la Inteligencia Artificial."""
        for widget in self.nav_container.winfo_children():
            widget.destroy()

        btn_opts = {"fg_color": self.theme_manager.get("bg_card"), "hover_color": self.theme_manager.get("border"), "text_color": self.theme_manager.get("text"), "height": 36, "corner_radius": 8, "anchor": "center"}

        top_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        top_frame.pack(side="top", fill="x")

        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_back"), command=self.exit_config_ai_menu, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="top", fill="x", padx=20, pady=10)

        scroll_mods = ctk.CTkScrollableFrame(self.nav_container, fg_color="transparent", corner_radius=0, scrollbar_button_color=self.theme_manager.get("bg_sidebar"), scrollbar_button_hover_color=self.theme_manager.get("bg_sidebar"))
        scroll_mods.pack(side="top", fill="both", expand=True)

        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_engines"), command=lambda: self.show_frame(AIEngineConfigFrame), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_general_settings"), command=lambda: self.show_frame(AISettingsConfigFrame), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_affinity_ranges"), command=lambda: self.show_frame(RangesEditor), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_internal_prompts"), command=lambda: self.show_frame(PromptsEditor), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_amnesia"), command=lambda: self.show_frame(AIAmnesiaConfigFrame), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")

    def open_config_ai_menu(self):
        self.render_config_ai_sidebar()
        self.show_frame(AISettingsConfigFrame)
        
    def exit_config_ai_menu(self):
        self.render_config_sidebar()
        self.show_frame(GeneralConfigFrame)

    def render_ai_sidebar(self):
        for widget in self.nav_container.winfo_children():
            widget.destroy()

        btn_opts = {"fg_color": self.theme_manager.get("bg_card"), "hover_color": self.theme_manager.get("border"), "text_color": self.theme_manager.get("text"), "height": 36, "corner_radius": 8, "anchor": "center"}

        top_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        top_frame.pack(side="top", fill="x")

        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_back"), command=self.exit_ai_menu, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        
        cfg = self._load_json_file("config.json")
        if cfg.get("ai_config", {}).get("ai_first_run", True):
            # Si es el primer arranque, el sidebar se queda bloqueado solo con el botón de Volver
            return
            
        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_ai_general"), command=lambda: self.show_frame(AIGeneralConfigFrame), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkLabel(top_frame, text=self.lang_manager.get("nav_memory_editors_title"), font=ctk.CTkFont(size=12, weight="bold"), text_color=self.theme_manager.get("accent")).pack(padx=(16, 16), pady=(10, 0), fill="x", anchor="w")

        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="top", fill="x", padx=20, pady=10)

        menu_ai = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        menu_ai.pack(side="top", fill="x")

        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_identity"), command=lambda: self.show_frame(IdentityEditor), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_moods"), command=lambda: self.show_frame(MoodsEditor), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_users"), command=lambda: self.show_frame(UsersEditor), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_memory"), command=lambda: self.show_frame(MemoryEditor), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_opinions"), command=lambda: self.show_frame(OpinionsEditor), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_self"), command=lambda: self.show_frame(SelfEditor), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        bottom_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(bottom_frame, text=self.lang_manager.get("nav_ai_reload_files"), command=self.reload_all_ai_files, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="bottom", fill="x", padx=20, pady=10)

    def open_ai_menu(self):
        self.render_ai_sidebar()
        
        cfg = self._load_json_file("config.json")
        if cfg.get("ai_config", {}).get("ai_first_run", True):
            self.show_frame(AIWizardView)
        else:
            self.show_frame(AIGeneralConfigFrame)

    def exit_ai_menu(self):
        self.render_main_sidebar()
        self.show_frame(DashboardFrame)

    def reload_all_ai_files(self):
        """Ejecuta los callbacks inyectados por las Vistas para refrescar la UI forzosamente."""
        for func in self.ai_reload_functions.values():
            try: func()
            except Exception: logger.error("Error al recargar archivos de IA en la vista", exc_info=True)

    # --- HELPER JSON ---
    def _load_json_file(self, filename):
        """
        Método utilitario heredado por las vistas. 
        Usa bloqueos I/O (`use_lock`) para evitar corrupción al leer datos compartidos con el bot.
        """
        path = os.path.join(SETTINGS_DIR, filename)
        use_lock = filename == "config.json" or "outputs_" in filename
        return ConfigManager.load_json(path, use_lock=use_lock)

    def _save_json_file(self, filename, data):
        """
        Método utilitario de escritura I/O segura en disco, con candados multiproceso.
        """
        path = os.path.join(SETTINGS_DIR, filename)
        use_lock = filename == "config.json" or "outputs_" in filename
        ConfigManager.save_json(path, data, use_lock=use_lock)

    def toggle_password(self, entry, btn):
        """Alterna la visibilidad de campos de contraseñas (Ej: Tokens y API Keys)."""
        if entry.cget("show") == "*":
            entry.configure(show="")
            btn.configure(text_color=self.theme_manager.get("accent"))
        else:
            entry.configure(show="*")
            btn.configure(text_color=self.theme_manager.get("text_dim"))

    def toggle_help(self, widget, layout="pack", **kwargs):
        """Animación de despliegue dinámico para información de Ayuda (?)."""
        if widget.winfo_viewable():
            if layout == "grid": widget.grid_remove()
            else: widget.pack_forget()
        else:
            if layout == "grid": widget.grid(**kwargs)
            else: widget.pack(**kwargs)

    # --- LÓGICA DEL BOT ---
    def start_bot(self):
        """
        Invoca la creación del subproceso (Daemon) principal del bot de Discord.
        Enruta la salida estándar de consola a través de PIPES para leer sus salidas
        mediante un hilo en segundo plano (threading).
        """
        if self.bot_process: return

        # UI Updates
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_label.configure(text=self.lang_manager.get("dash_status_starting"), text_color=self.theme_manager.get("accent"))
        self.progress_bar.pack(side="left", padx=(15, 0))
        self.progress_bar.set(0)
        
        # Limpiar consolas (Lazy Loading Safe)
        consoles_to_clean = []
        dash = self.frames.get("DashboardFrame")
        mus = self.frames.get("MusicFrame")
        ai_gen = self.frames.get("AIGeneralConfigFrame")
        
        c_main = getattr(self, "console_main", None) or (getattr(dash, "console_main", None) if dash else None)
        if c_main: consoles_to_clean.append(c_main)
        c_mus = getattr(self, "console_music", None) or (getattr(mus, "console_music", None) if mus else None)
        if c_mus: consoles_to_clean.append(c_mus)
        c_err = getattr(self, "console_errors", None) or (getattr(dash, "console_errors", None) if dash else None)
        if c_err: consoles_to_clean.append(c_err)
        c_ai = getattr(self, "console_ai", None) or (getattr(ai_gen, "console_ai", None) if ai_gen else None)
        if c_ai: consoles_to_clean.append(c_ai)
        
        for console in consoles_to_clean:
            console.configure(state="normal")
            console.delete("0.0", "end")
            console.configure(state="disabled")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--run-bot"]
        else:
            python_exe = sys.executable
            meow_script = os.path.join(BASE_DIR, "meowSick.py")
            cmd = [python_exe, "-u", meow_script]

        try:
            self.bot_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE,
                text=True, bufsize=1, cwd=BASE_DIR, encoding='utf-8', env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            threading.Thread(target=self.read_output, daemon=True).start()
        except Exception as e:
            self.log_to_console(self.lang_manager.get("msg_err_starting").format(e=e), "main")
            self.stop_bot()

    def stop_bot(self):
        """
        Despacha una señal de apagado gracefully a la tubería IPC. 
        Permite al Bot cerrar conexiones web y vaciar memoria RAM ordenadamente.
        """
        if self.bot_process:
            self.log_to_console(self.lang_manager.get("msg_sending_stop"), "main")
            self.send_to_bot("IPC>>" + json.dumps({"type": "command", "name": "stop"}))

    def read_output(self):
        """
        Hilo receptor asíncrono (I/O). Lee el STDOUT del subproceso continuamente.
        Aplica enrutamiento IPC y expresiones regulares primitivas para dividir y renderizar texto en GUI.
        """
        # Prefijos de ruido que NO deben ir a la Terminal limpia
        NOISE_PREFIXES = (
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",  # logging estándar
            "asyncio", "discord.", "websocket", "heartbeat",   # internals de discord.py
            "2025", "2026",  # timestamps del logging (formato: YYYY-MM-DD HH:MM:SS)
            "🔥",            # Filtro para ignorar los ON_MESSAGE pasivos
        )
        while self.bot_process and self.bot_process.stdout:
            try:
                line = self.bot_process.stdout.readline()
                if not line: break
                
                # ═══ REGISTRO COMPLETO: recibe absolutamente todo, sin filtro ═══
                self.after(0, lambda l=line: self._write_to_widget(self.console_errors, l))

                # 0. PROTOCOLO IPC ESTRUCTURADO
                if line.startswith("IPC>>"):
                    try:
                        payload = json.loads(line[5:])
                        msg_type = payload.get("type")
                        msg_name = payload.get("name")
                        data = payload.get("payload")

                        if msg_type == "event":
                            if msg_name == "progress_update":
                                self.after(0, lambda p=float(data["percent"]), m=data["message"]: self._update_progress(p, m))
                            elif msg_name == "queue_update":
                                self.after(0, lambda d=data: self.update_queue_ui(d))
                            elif msg_name == "now_playing":
                                self.after(0, lambda t=data["title"]: self.update_now_playing_ui(t))
                    except Exception: 
                        logger.error("Error procesando IPC JSON", exc_info=True)
                    continue  # No mostrar en ninguna consola visual

                # ═══ FILTRO DE TERMINAL LIMPIA (UX GUI) ═══
                # Elimina logs ruidosos y de bajo nivel (Asyncio/Discord.py) para ofrecer una experiencia estética al humano.
                line_stripped = line.strip()
                is_noise = any(line_stripped.startswith(p) for p in NOISE_PREFIXES)
                has_bot_emoji = any(e in line for e in ("🎵", "🧠", "⚙️", "📥", "📤", "✅", "❌", "⚠️", "💬", "💾", "🔑", "🌐", "🎙️", "📝", "✨", "💤", "📉", "🔁", "🔄", "👁️", "📡", "🧹", "📦", "🛑", "👋", "🤖", "🧟", "💀", "[LAUNCHER]", "[WORKER", "[SISTEMA]", "[SHUTDOWN]", "[IPC]", "[ONLINE]"))
                
                if not is_noise or has_bot_emoji:
                    self.after(0, lambda l=line: self.log_to_console(l, "main"))

                # Filtros por módulo (consolas específicas)
                if "🎵" in line:
                    self.after(0, lambda l=line: self.log_to_console(l, "music"))
                    
                if any(m in line for m in ("🧠", "📥", "📤", "⚙️", "📝", "[IDENTITY]")):
                    self.after(0, lambda l=line: self.log_to_console(l, "ai"))

            except Exception: 
                logger.error("Error de lectura en I/O de bot_process", exc_info=True)
                break
        
        # Proceso terminado
        self.bot_process = None
        self.after(0, self._reset_ui_stopped)

    def _update_progress(self, pct, msg):
        """Actualizador asíncrono para la barra de carga UI del bot."""
        self.progress_bar.set(pct)
        self.status_label.configure(text=f"{self.lang_manager.get('dash_status_prefix')} {msg}")
        if pct >= 1.0:
            self.status_label.configure(text=self.lang_manager.get("dash_status_on"), text_color=self.theme_manager.get("green"))
            self.after(1500, self.progress_bar.pack_forget) # Oculta la barra suavemente tras terminar

    def _reset_ui_stopped(self):
        """Desencadena un reinicio de parámetros visuales post-apagado del Daemon."""
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_label.configure(text=self.lang_manager.get("dash_status_off"), text_color=self.theme_manager.get("red"))
        self.progress_bar.pack_forget()
        self.log_to_console(self.lang_manager.get("msg_process_finished"), "main")
        
        # Resetear UI de música
        try:
            music_frame = self.frames.get("MusicFrame")
            lbl = getattr(self, "lbl_now_playing", None) or (getattr(music_frame, "lbl_now_playing", None) if music_frame else None)
            if lbl: lbl.configure(text=self.lang_manager.get("mus_lbl_now_playing_empty"))
        except Exception: logger.error("Error reiniciando UI de música post-apagado", exc_info=True)

    def log_to_console(self, text, target):
        """Enrutador de textos hacia las instancias CtkTextbox específicas."""
        widget = None
        if target == "main":
            dash = self.frames.get("DashboardFrame")
            widget = getattr(self, "console_main", None) or (getattr(dash, "console_main", None) if dash else None)
        elif target == "music":
            mus = self.frames.get("MusicFrame")
            widget = getattr(self, "console_music", None) or (getattr(mus, "console_music", None) if mus else None)
        elif target == "ai":
            ai_gen = self.frames.get("AIGeneralConfigFrame")
            widget = getattr(self, "console_ai", None) or (getattr(ai_gen, "console_ai", None) if ai_gen else None)
            
        if widget:
            self._write_to_widget(widget, text)

    def _write_to_widget(self, widget, text):
        """Inyección thread-safe de texto en un CtkTextbox deshabilitado para edición."""
        try:
            widget.configure(state="normal")
            widget.insert("end", text)
            widget.see("end")
            widget.configure(state="disabled")
        except Exception: logger.error("Error inyectando texto a CtkTextbox", exc_info=True)

    def send_to_bot(self, text):
        """
        Transmisor IPC (Inter-Process Communication). 
        Inyecta cadenas serializadas directo a la RAM/Stdin del subproceso del Bot.
        """
        if self.bot_process and self.bot_process.stdin:
            try:
                self.bot_process.stdin.write(text + "\n")
                self.bot_process.stdin.flush()
            except Exception: logger.error("Error enviando comando IPC al bot", exc_info=True)
            
    def send_music_cmd(self, action):
        """Transmisor IPC Estructurado para el módulo musical."""
        if not self.bot_process: return
        payload = {"type": "command", "name": f"music_{action}"}
        
        if action in ["play", "next"]:
            if hasattr(self, 'music_entry'):
                query = self.music_entry.get()
                if query:
                    payload["payload"] = {"query": query}
                    self.music_entry.delete(0, 'end')
                else:
                    return
                    
        self.send_to_bot("IPC>>" + json.dumps(payload))

    # --- FUNCIONES DE MÚSICA ---
    def update_now_playing_ui(self, title):
        """Actualiza el texto de 'Reproduciendo ahora' encolando la búsqueda segura del widget."""
        music_frame = self.frames.get("MusicFrame")
        lbl = getattr(self, "lbl_now_playing", None) or (getattr(music_frame, "lbl_now_playing", None) if music_frame else None)
        if lbl:
            lbl.configure(text=f"{self.lang_manager.get('mus_lbl_now_playing_prefix')}{title}")

    def update_queue_ui(self, queue_list):
        """Disparador que redibuja la lista visual de música tras recibir un paquete IPC."""
        music_frame = self.frames.get("MusicFrame")
        queue_widget = getattr(self, "queue_display", None) or (getattr(music_frame, "queue_display", None) if music_frame else None)
        if not queue_widget: return
        
        queue_widget.configure(state="normal")
        queue_widget.delete("0.0", "end")
        if not queue_list:
            queue_widget.insert("end", self.lang_manager.get("mus_queue_empty"))
        else:
            for i, title in enumerate(queue_list, 1):
                queue_widget.insert("end", f"{i}. {title}\n")
        queue_widget.configure(state="disabled")

    # --- GESTIÓN DE MÓDULOS ---
    def update_module_state(self, module_name, button):
        """
        Lee el registro en tiempo real de 'config.json' para sincronizar el color
        de los botones UI de Activado/Desactivado con el estado estricto en disco.
        """
        try:
            data = self._load_json_file("config.json")
            is_active = data.get("modules", {}).get(module_name, False)
            if is_active:
                button.configure(text=self.lang_manager.get("mod_btn_on"), fg_color=self.theme_manager.get("accent"), text_color=self.theme_manager.get("bg_dark"))
            else:
                button.configure(text=self.lang_manager.get("mod_btn_off"), fg_color=self.theme_manager.get("bg_dark"), text_color=self.theme_manager.get("red"))
        except Exception: logger.error("Error actualizando el estado del botón del módulo", exc_info=True)

    def toggle_module(self, module_name, button):
        """
        Modificador de estado de submódulos. 
        Invierte su booleano, lo guarda a disco y emite una orden de Hot-Reload (CMD_RELOAD) al bot.
        """
        try:
            data = self._load_json_file("config.json")
            
            if "modules" not in data:
                data["modules"] = {}
            
            # Obtenemos el estado actual del diccionario asegurado
            new_state = not data["modules"].get(module_name, False)
            data["modules"][module_name] = new_state
            
            self._save_json_file("config.json", data)
            
            for btn in self.module_buttons.get(module_name, []):
                self.update_module_state(module_name, btn)
            
            # Recarga en caliente si el bot está on
            if self.bot_process:
                self.log_to_console(self.lang_manager.get("msg_module_toggle").format(module_name=module_name, new_state=new_state), "main")
                self.send_to_bot("IPC>>" + json.dumps({"type": "command", "name": "reload"}))
        except Exception as e:
            print(self.lang_manager.get("msg_err_toggle").format(e=e))

    def on_closing(self):
        """Captura el evento de cierre de Windows y asegura que el daemon no quede huérfano (Zombie)."""
        if self.bot_process:
            self.stop_bot()
            try:
                self.bot_process.kill() # Ejecución Forzosa: Mata al proceso zombie al instante
            except Exception: logger.error("Error forzando la terminación del proceso zombie", exc_info=True)
            self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    import sys
    
    # Forzar codificación UTF-8 para evitar errores con emojis en Windows (cp1252)
    # line_buffering=True obliga a la consola a imprimir al instante y no retener memoria
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
        
    if len(sys.argv) > 1 and sys.argv[1] == "--run-bot":
        import asyncio
        import meowSick
        asyncio.run(meowSick.main())
        sys.exit(0)
        
    app = MeowLauncher()
    app.mainloop()