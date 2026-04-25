import customtkinter as ctk
import subprocess
import sys
import os
import threading
import json
import time
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
from views.config.ai_presets_view import AIPresetsConfigFrame

# --- CONFIGURACIÓN DE RUTAS Y VISUAL ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    RUNTIME_DIR = getattr(sys, '_MEIPASS', BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RUNTIME_DIR = BASE_DIR

SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
ENV_PATH = os.path.join(SETTINGS_DIR, ".env")

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
        
        ico_path = os.path.join(RUNTIME_DIR, "res", "img", "meowSick_logo1x1_256x256.ico")
        if os.path.exists(ico_path):
            self.iconbitmap(ico_path)
        
        self.bot_process = None
        self.module_buttons = {}
        self.frames = {}
        self.general_entries = {}
        self.ai_reload_functions = {}

        # Grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Construcción de la UI
        self.create_sidebar()
        
        self.show_frame(DashboardFrame)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_frame(self, view_class_or_name):
        if isinstance(view_class_or_name, str):
            name = view_class_or_name
            # Puente temporal: Instancia la vista antigua si se solicita por string
            if name not in self.frames:
                creator = getattr(self, f"create_{name}_page", None) or getattr(self, f"create_{name}_frame", None)
                if creator: creator()
        else:
            name = view_class_or_name.__name__
            # Carga Perezosa (Lazy Loading): Solo instancia la vista de clase si no existe
            if name not in self.frames:
                # Se inyecta self como 'controller'
                self.frames[name] = view_class_or_name(parent=self, controller=self)
            
        for frame in self.frames.values():
            frame.grid_forget()
            
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

    def _fix_scroll(self, widget):
        """Permite que el scroll fluya al contenedor principal a menos que el textbox esté enfocado."""
        def _on_mousewheel(event):
            # Si el cuadro de texto está seleccionado, permite el scroll interno
            if widget.focus_get() == widget._textbox:
                return
            
            # Si no está seleccionado, delega el movimiento al marco deslizable padre
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
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=self.theme_manager.get("bg_sidebar"), border_width=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(1, weight=1) # El contenedor de nav toma el espacio

        # Contenedor superior dinámico (Logo o Advertencia)
        self.top_sidebar_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", height=135)
        self.top_sidebar_container.grid(row=0, column=0, sticky="ew", padx=15, pady=(20, 0))
        self.top_sidebar_container.pack_propagate(False) # Evita que su tamaño dependa de los hijos

        # Logo / Imagen
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

        # Contenedor dinámico de navegación
        self.nav_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_container.grid(row=1, column=0, sticky="nsew")

        # Footer
        ctk.CTkLabel(self.sidebar_frame, text=self.lang_manager.get("sidebar_version_footer"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11)).grid(row=2, column=0, pady=20)

        # Renderizar menú principal
        self.render_main_sidebar()

    def render_main_sidebar(self):
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

        # 5. Lista Desplazable (Atajos de Módulos) - Toma el espacio restante
        # Hacemos la barra de scroll invisible (camuflada con el fondo)
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

        # 3. Sección Inferior (Credenciales)
        bottom_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(bottom_frame, text=self.lang_manager.get("nav_ai_engines"), command=lambda: self.show_frame(AIEngineConfigFrame), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        # 4. Separador Inferior
        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="bottom", fill="x", padx=20, pady=10)
        
        # 5. Lista de Módulos (Config)
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
        for widget in self.nav_container.winfo_children():
            widget.destroy()

        btn_opts = {"fg_color": self.theme_manager.get("bg_card"), "hover_color": self.theme_manager.get("border"), "text_color": self.theme_manager.get("text"), "height": 36, "corner_radius": 8, "anchor": "center"}

        top_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        top_frame.pack(side="top", fill="x")

        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_back"), command=self.exit_config_ai_menu, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="top", fill="x", padx=20, pady=10)

        scroll_mods = ctk.CTkScrollableFrame(self.nav_container, fg_color="transparent", corner_radius=0, scrollbar_button_color=self.theme_manager.get("bg_sidebar"), scrollbar_button_hover_color=self.theme_manager.get("bg_sidebar"))
        scroll_mods.pack(side="top", fill="both", expand=True)

        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_general_settings"), command=lambda: self.show_frame(AISettingsConfigFrame), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_affinity_ranges"), command=lambda: self.show_frame("config_ai_ranges"), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_internal_prompts"), command=lambda: self.show_frame("config_ai_prompts"), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")
        ctk.CTkButton(scroll_mods, text=self.lang_manager.get("nav_ai_presets", "🎭 Personalidades"), command=lambda: self.show_frame(AIPresetsConfigFrame), **btn_opts).pack(padx=(12, 0), pady=6, fill="x")

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

        # 1. Sección Superior (Volver, General)
        top_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        top_frame.pack(side="top", fill="x")

        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_back"), command=self.exit_ai_menu, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(top_frame, text=self.lang_manager.get("nav_ai_general"), command=lambda: self.show_frame(AIGeneralConfigFrame), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkLabel(top_frame, text=self.lang_manager.get("nav_memory_editors_title"), font=ctk.CTkFont(size=12, weight="bold"), text_color=self.theme_manager.get("accent")).pack(padx=(16, 16), pady=(10, 0), fill="x", anchor="w")

        # 2. Separador Superior
        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="top", fill="x", padx=20, pady=10)

        # 3. Lista Fija de Módulos (Editores)
        menu_ai = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        menu_ai.pack(side="top", fill="x")

        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_identity"), command=lambda: self.show_frame("config_ai_identity"), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_moods"), command=lambda: self.show_frame("config_ai_moods"), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_users"), command=lambda: self.show_frame("config_ai_users"), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_memory"), command=lambda: self.show_frame("config_ai_memory"), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_opinions"), command=lambda: self.show_frame("config_ai_opinions"), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")
        ctk.CTkButton(menu_ai, text=self.lang_manager.get("nav_ai_self"), command=lambda: self.show_frame("config_ai_self"), **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        # 4. Botones de Acción (Anclados al fondo)
        bottom_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(bottom_frame, text=self.lang_manager.get("nav_ai_amnesia"), command=self.open_amnesia_dialog, fg_color="#331a20", hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("red"), height=36, corner_radius=8).pack(padx=(12, 16), pady=(6, 0), fill="x")
        ctk.CTkButton(bottom_frame, text=self.lang_manager.get("nav_ai_reload_files"), command=self.reload_all_ai_files, **btn_opts).pack(padx=(12, 16), pady=6, fill="x")

        # 5. Separador Inferior (Empaquetado DESPUÉS para que quede arriba del botón)
        ctk.CTkFrame(self.nav_container, height=2, fg_color=self.theme_manager.get("border")).pack(side="bottom", fill="x", padx=20, pady=10)

    def open_ai_menu(self):
        self.render_ai_sidebar()
        self.show_frame(AIGeneralConfigFrame)

    def exit_ai_menu(self):
        self.render_main_sidebar()
        self.show_frame(DashboardFrame)

    def open_amnesia_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.lang_manager.get("dlg_amnesia_title"))
        dialog.geometry("400x450")
        dialog.configure(fg_color=self.theme_manager.get("bg_dark"))
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=self.lang_manager.get("dlg_amnesia_header"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("red")).pack(pady=(20, 10))
        ctk.CTkLabel(dialog, text=self.lang_manager.get("dlg_amnesia_desc"), text_color=self.theme_manager.get("text_dim"), justify="center").pack(pady=(0, 15))
        
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)
        
        chk_vars = {}
        options = [
            ("identity", self.lang_manager.get("dlg_amnesia_opt_id")), 
            ("users", self.lang_manager.get("dlg_amnesia_opt_users")), 
            ("memory", self.lang_manager.get("dlg_amnesia_opt_mem")), 
            ("opinions", self.lang_manager.get("dlg_amnesia_opt_opi")), 
            ("moods", self.lang_manager.get("dlg_amnesia_opt_moods")), 
            ("self", self.lang_manager.get("dlg_amnesia_opt_self"))
        ]
        for key, text in options:
            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(form, text=text, variable=var, text_color=self.theme_manager.get("text"), checkbox_height=20, checkbox_width=20, fg_color=self.theme_manager.get("red"), hover_color="#c5536b")
            chk.pack(anchor="w", pady=8)
            chk_vars[key] = var
            
        def apply_amnesia():
            mem_dir = os.path.join(BASE_DIR, "cogs", "AI", "memory")
            try:
                if chk_vars["identity"].get():
                    with open(os.path.join(mem_dir, "identity.txt"), "w", encoding="utf-8") as f: f.write("Eres un asistente virtual. Tienes tu propia personalidad, responde de forma natural y conversacional.")
                    with open(os.path.join(mem_dir, "guidelines.txt"), "w", encoding="utf-8") as f: f.write("1. Sé breve.\n2. No uses emojis excesivamente.")
                if chk_vars["users"].get():
                    ConfigManager.save_json(os.path.join(mem_dir, "known_users.json"), {}, use_lock=False)
                if chk_vars["memory"].get():
                    ConfigManager.save_json(os.path.join(mem_dir, "memoria.json"), {}, use_lock=False)
                if chk_vars["opinions"].get():
                    ConfigManager.save_json(os.path.join(mem_dir, "opiniones.json"), {}, use_lock=False)
                if chk_vars["self"].get():
                    ConfigManager.save_json(os.path.join(mem_dir, "autoconcepto.json"), {"gustos": [], "opiniones": {}}, use_lock=False)
                if chk_vars["moods"].get():
                    ConfigManager.save_json(os.path.join(mem_dir, "estado_animo.json"), {"estado_animo": "Neutral: Comportamiento por defecto."}, use_lock=False)
                    ConfigManager.save_json(os.path.join(mem_dir, "historial_estados.json"), [], use_lock=False)
                    ConfigManager.save_json(os.path.join(mem_dir, "estados_posibles.json"), ["Neutral: Estoy tranquila, existiendo.", "Feliz: Me siento bien, contenta."], use_lock=False)
                self.reload_all_ai_files()
                messagebox.showinfo(self.lang_manager.get("dlg_amnesia_msg_ok_title"), self.lang_manager.get("dlg_amnesia_msg_ok"))
                dialog.destroy()
            except Exception as e: messagebox.showerror(self.lang_manager.get("dlg_amnesia_msg_err_title"), self.lang_manager.get("dlg_amnesia_msg_err").format(e=e))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))
        ctk.CTkButton(btn_frame, text=self.lang_manager.get("btn_cancel"), width=100, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=dialog.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=self.lang_manager.get("dlg_amnesia_btn_del"), width=160, fg_color=self.theme_manager.get("red"), hover_color="#c5536b", text_color=self.theme_manager.get("bg_dark"), font=ctk.CTkFont(weight="bold"), command=apply_amnesia).pack(side="left", padx=10)

    def reload_all_ai_files(self):
        for func in self.ai_reload_functions.values():
            try: func()
            except: pass

    # --- HELPER JSON ---
    def _load_json_file(self, filename):
        path = os.path.join(SETTINGS_DIR, filename)
        use_lock = filename == "config.json" or "outputs_" in filename
        return ConfigManager.load_json(path, use_lock=use_lock)

    def _save_json_file(self, filename, data):
        path = os.path.join(SETTINGS_DIR, filename)
        use_lock = filename == "config.json" or "outputs_" in filename
        ConfigManager.save_json(path, data, use_lock=use_lock)

    def create_ai_identity_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_identity"] = frame

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text=self.lang_manager.get("ai_id_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")
        
        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(side="top", fill="both", expand=True)
        
        # Contenedor Identity
        id_wrap = ctk.CTkFrame(content, fg_color="transparent")
        id_wrap.pack(side="top", fill="both", expand=True, pady=(0, 10))
        
        id_top = ctk.CTkFrame(id_wrap, fg_color="transparent")
        id_top.pack(fill="x")
        
        id_lbl_row = ctk.CTkFrame(id_top, fg_color="transparent")
        id_lbl_row.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(id_lbl_row, text=self.lang_manager.get("ai_id_lbl_identity"), text_color=self.theme_manager.get("text"), anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        id_help = ctk.CTkFrame(id_top, fg_color="transparent")
        ctk.CTkLabel(id_help, text=self.lang_manager.get("ai_id_help_identity"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left")
        ctk.CTkButton(id_lbl_row, text="?", width=24, height=24, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=id_help: self.toggle_help(h, "pack", fill="x", pady=(0, 5))).pack(side="left", padx=10)
        
        txt_identity = ctk.CTkTextbox(id_wrap, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), border_width=1, border_color=self.theme_manager.get("border"))
        txt_identity.pack(fill="both", expand=True)
        
        # Contenedor Guidelines
        gl_wrap = ctk.CTkFrame(content, fg_color="transparent")
        gl_wrap.pack(side="top", fill="both", expand=True)
        
        gl_top = ctk.CTkFrame(gl_wrap, fg_color="transparent")
        gl_top.pack(fill="x")
        
        gl_lbl_row = ctk.CTkFrame(gl_top, fg_color="transparent")
        gl_lbl_row.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(gl_lbl_row, text=self.lang_manager.get("ai_id_lbl_guidelines"), text_color=self.theme_manager.get("text"), anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        gl_help = ctk.CTkFrame(gl_top, fg_color="transparent")
        ctk.CTkLabel(gl_help, text=self.lang_manager.get("ai_id_help_guidelines"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left")
        ctk.CTkButton(gl_lbl_row, text="?", width=24, height=24, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=gl_help: self.toggle_help(h, "pack", fill="x", pady=(0, 5))).pack(side="left", padx=10)
        
        txt_guidelines = ctk.CTkTextbox(gl_wrap, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), border_width=1, border_color=self.theme_manager.get("border"))
        txt_guidelines.pack(fill="both", expand=True)

        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        def load_files():
            txt_identity.delete("0.0", "end")
            txt_guidelines.delete("0.0", "end")
            id_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "identity.txt")
            gl_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "guidelines.txt")
            
            if os.path.exists(id_path):
                with open(id_path, "r", encoding="utf-8") as f: txt_identity.insert("0.0", f.read())
            if os.path.exists(gl_path):
                with open(gl_path, "r", encoding="utf-8") as f: txt_guidelines.insert("0.0", f.read())
            lbl_status.configure(text=self.lang_manager.get("msg_files_loaded"), text_color=self.theme_manager.get("text_dim"))

        def save_files():
            id_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "identity.txt")
            gl_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "guidelines.txt")
            os.makedirs(os.path.dirname(id_path), exist_ok=True)
            
            with open(id_path, "w", encoding="utf-8") as f: f.write(txt_identity.get("0.0", "end").strip())
            with open(gl_path, "w", encoding="utf-8") as f: f.write(txt_guidelines.get("0.0", "end").strip())
            
            lbl_status.configure(text=self.lang_manager.get("msg_saved_success"), text_color=self.theme_manager.get("green"))
            self.after(3000, lambda: lbl_status.configure(text=""))

        ctk.CTkButton(controls, text=self.lang_manager.get("btn_reload"), command=load_files, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.lang_manager.get("btn_save_changes"), command=save_files, fg_color=self.theme_manager.get("accent"), hover_color=self.theme_manager.get("accent_dim"), text_color=self.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        load_files()
        self.ai_reload_functions["config_ai_identity"] = load_files

    def create_ai_moods_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_moods"] = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_moods_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_moods_desc"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=(5,0))
        
        lbl_status = ctk.CTkLabel(title_row, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=15)

        # Controles inferiores (Recargar e Historial)
        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))

        btn_reload = ctk.CTkButton(controls, text=self.lang_manager.get("btn_reload"), width=120, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
        btn_reload.pack(side="left")
        
        btn_history = ctk.CTkButton(controls, text=self.lang_manager.get("ai_moods_btn_history"), fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: self.show_frame("config_ai_moods_history"))
        btn_history.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Scroll principal
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", scrollbar_button_color=self.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.theme_manager.get("bg_dark"))
        scroll.pack(side="top", fill="both", expand=True)

        # 1. ESTADO ACTUAL
        curr_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        curr_frame.pack(fill="x", pady=(5, 10))
        
        # Wrapper para mantener el título y la ayuda juntos
        curr_header_wrap = ctk.CTkFrame(curr_frame, fg_color="transparent")
        curr_header_wrap.pack(fill="x")
        
        curr_lbl_row = ctk.CTkFrame(curr_header_wrap, fg_color="transparent")
        curr_lbl_row.pack(fill="x")
        ctk.CTkLabel(curr_lbl_row, text=self.lang_manager.get("ai_moods_lbl_current"), font=ctk.CTkFont(weight="bold", size=13), text_color=self.theme_manager.get("text")).pack(side="left")
        
        curr_help = ctk.CTkFrame(curr_header_wrap, fg_color="transparent")
        ctk.CTkLabel(curr_help, text=self.lang_manager.get("ai_moods_help_current"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        ctk.CTkButton(curr_lbl_row, text="?", width=24, height=24, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=curr_help: self.toggle_help(h, "pack", fill="x")).pack(side="left", padx=10)
        
        btn_save_curr = ctk.CTkButton(curr_lbl_row, text=self.lang_manager.get("ai_moods_btn_save_current"), width=120, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
        btn_save_curr.pack(side="right")
        
        # Título editable del estado
        entry_mood_name = ctk.CTkEntry(curr_frame, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold", size=14))
        entry_mood_name.pack(fill="x", pady=(5, 5))
        
        # Contenedor visible para la descripción
        desc_container = ctk.CTkFrame(curr_frame, fg_color=self.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.theme_manager.get("border"))
        desc_container.pack(fill="x")
        
        entry_mood_desc = ctk.CTkTextbox(desc_container, height=60, font=("Consolas", 13), fg_color="transparent", border_width=0, text_color=self.theme_manager.get("text"), wrap="word")
        entry_mood_desc.pack(fill="x", padx=10, pady=10)
        self._fix_scroll(entry_mood_desc)

        def resize_desc_current(event=None):
            try:
                dl = entry_mood_desc._textbox.count("1.0", "end", "displaylines")
                lines = dl[0] if dl else 1
                entry_mood_desc.configure(height=max(60, lines * 22)) # 22px por línea aprox
            except: pass
        entry_mood_desc.bind("<KeyRelease>", resize_desc_current)

        # 2. ESTADOS POSIBLES
        poss_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        poss_frame.pack(fill="x", pady=(5, 15))
        
        # Wrapper para mantener el título y la ayuda juntos
        poss_header_wrap = ctk.CTkFrame(poss_frame, fg_color="transparent")
        poss_header_wrap.pack(fill="x")
        
        poss_lbl_row = ctk.CTkFrame(poss_header_wrap, fg_color="transparent")
        poss_lbl_row.pack(fill="x")
        ctk.CTkLabel(poss_lbl_row, text=self.lang_manager.get("ai_moods_lbl_possible"), font=ctk.CTkFont(weight="bold", size=13), text_color=self.theme_manager.get("text")).pack(side="left")
        
        poss_help = ctk.CTkFrame(poss_header_wrap, fg_color="transparent")
        ctk.CTkLabel(poss_help, text=self.lang_manager.get("ai_moods_help_possible"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        ctk.CTkButton(poss_lbl_row, text="?", width=24, height=24, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=poss_help: self.toggle_help(h, "pack", fill="x")).pack(side="left", padx=10)

        btn_save_poss = ctk.CTkButton(poss_lbl_row, text=self.lang_manager.get("ai_moods_btn_save_list"), width=120, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
        btn_save_poss.pack(side="right")
        
        btn_add_poss = ctk.CTkButton(poss_lbl_row, text=self.lang_manager.get("btn_add"), width=80, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
        btn_add_poss.pack(side="right", padx=(0, 5))

        poss_list_container = ctk.CTkFrame(poss_frame, fg_color="transparent")
        poss_list_container.pack(fill="x", pady=(5, 0))

        self.poss_moods_entries = []

        def add_possible_mood(name_val, desc_val):
            row = ctk.CTkFrame(poss_list_container, fg_color=self.theme_manager.get("bg_card"), corner_radius=8)
            row.pack(fill="x", pady=4)
            
            btn_del = ctk.CTkButton(row, text="🗑", width=30, height=30, fg_color="transparent", hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("text_dim"))
            btn_del.pack(side="right", padx=10)
            
            content = ctk.CTkFrame(row, fg_color="transparent")
            content.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            
            name_entry = ctk.CTkEntry(content, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold"))
            name_entry.pack(fill="x", pady=(0, 5))
            name_entry.insert(0, name_val)
            
            desc_txt = ctk.CTkTextbox(content, height=46, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), wrap="word")
            desc_txt.pack(fill="x")
            desc_txt.insert("0.0", desc_val)
            self._fix_scroll(desc_txt)
            
            def resize_desc(event=None):
                try:
                    dl = desc_txt._textbox.count("1.0", "end", "displaylines")
                    lines = dl[0] if dl else 1
                    desc_txt.configure(height=max(46, lines * 20))
                except: pass
            desc_txt.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc) # Refresco para cuando se genera dinámicamente
            
            entry_data = {"row": row, "name": name_entry, "desc": desc_txt}
            self.poss_moods_entries.append(entry_data)
            
            btn_del.configure(command=lambda r=row, d=entry_data: delete_possible_mood(r, d))

        def delete_possible_mood(row, data):
            row.destroy()
            if data in self.poss_moods_entries:
                self.poss_moods_entries.remove(data)

        def open_new_mood_dialog():
            dialog = ctk.CTkToplevel(self)
            dialog.title(self.lang_manager.get("ai_moods_dlg_title"))
            dialog.geometry("450x400")
            dialog.configure(fg_color=self.theme_manager.get("bg_dark"))
            dialog.transient(self) # Mantener la ventana por encima del launcher
            dialog.grab_set() # Bloquear interacción con la ventana principal
            
            ctk.CTkLabel(dialog, text=self.lang_manager.get("ai_moods_dlg_header"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("accent")).pack(pady=(20, 10))
            
            form = ctk.CTkFrame(dialog, fg_color="transparent")
            form.pack(fill="both", expand=True, padx=20)
            
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_moods_dlg_name"), text_color=self.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_name = ctk.CTkEntry(form, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), font=ctk.CTkFont(weight="bold"))
            entry_name.pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_moods_dlg_name_ph"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_moods_dlg_desc"), text_color=self.theme_manager.get("text"), anchor="w").pack(fill="x")
            txt_desc = ctk.CTkTextbox(form, height=80, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
            txt_desc.pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_moods_dlg_desc_ph"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", pady=(0, 10))
            
            lbl_err = ctk.CTkLabel(dialog, text="", text_color=self.theme_manager.get("red"), font=ctk.CTkFont(size=12))
            lbl_err.pack(pady=(5, 5))
            
            def save_new():
                name_val = entry_name.get().strip()
                desc_val = txt_desc.get("0.0", "end").strip()
                if not name_val:
                    return lbl_err.configure(text=self.lang_manager.get("ai_moods_err_name"))
                
                add_possible_mood(name_val, desc_val)
                dialog.destroy()

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=(0, 20))
            
            ctk.CTkButton(btn_frame, text=self.lang_manager.get("btn_cancel"), width=100, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=dialog.destroy).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text=self.lang_manager.get("btn_save_short"), width=100, fg_color=self.theme_manager.get("accent"), hover_color=self.theme_manager.get("accent_dim"), text_color=self.theme_manager.get("bg_dark"), command=save_new).pack(side="left", padx=10)

        btn_add_poss.configure(command=open_new_mood_dialog)

        # RUTAS
        curr_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "estado_animo.json")
        poss_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "estados_posibles.json")
        hist_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "historial_estados.json")

        def load_moods():
            entry_mood_name.delete(0, "end")
            entry_mood_desc.delete("0.0", "end")
            for w in poss_list_container.winfo_children(): w.destroy()
            self.poss_moods_entries.clear()

            curr_data = ConfigManager.load_json(curr_path, use_lock=False)
            if curr_data:
                val = curr_data.get("estado_animo", "")
                if ":" in val:
                    name, desc = val.split(":", 1)
                    entry_mood_name.insert(0, name.strip())
                    entry_mood_desc.insert("0.0", desc.strip())
                else:
                    entry_mood_name.insert(0, val.strip())
                self.after(50, resize_desc_current)
                
            poss_data = ConfigManager.load_json(poss_path, use_lock=False)
            if isinstance(poss_data, list) and poss_data:
                for val in poss_data:
                    if ":" in val:
                        name, desc = val.split(":", 1)
                        add_possible_mood(name.strip(), desc.strip())
                    else:
                        add_possible_mood(val.strip(), "")
                
            if not self.poss_moods_entries:
                add_possible_mood("Neutral", self.lang_manager.get("ai_moods_def_neutral"))
                
            lbl_status.configure(text=self.lang_manager.get("msg_files_loaded"), text_color=self.theme_manager.get("text_dim"))

        def save_current_mood():
            try:
                name = entry_mood_name.get().strip()
                desc = entry_mood_desc.get("0.0", "end").strip()
                full_val = f"{name}: {desc}" if desc else name
                
                ConfigManager.save_json(curr_path, {"estado_animo": full_val}, use_lock=False)
                lbl_status.configure(text=self.lang_manager.get("ai_moods_msg_saved_curr"), text_color=self.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))
            
        def save_possible_moods():
            try:
                poss_list = []
                for item in self.poss_moods_entries:
                    name = item["name"].get().strip()
                    desc = item["desc"].get("0.0", "end").strip()
                    if name:
                        full_val = f"{name}: {desc}" if desc else name
                        poss_list.append(full_val)
                
                ConfigManager.save_json(poss_path, poss_list, use_lock=False)
                
                lbl_status.configure(text=self.lang_manager.get("ai_moods_msg_saved_list"), text_color=self.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        btn_save_curr.configure(command=save_current_mood)
        btn_save_poss.configure(command=save_possible_moods)
        btn_reload.configure(command=load_moods)

        load_moods()
        self.ai_reload_functions["config_ai_moods"] = load_moods

    def create_ai_moods_history_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_moods_history"] = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        ctk.CTkButton(header, text=self.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: self.show_frame("config_ai_moods")).pack(side="left")
        ctk.CTkLabel(header, text=self.lang_manager.get("ai_mh_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left", padx=20)
        
        txt_history = ctk.CTkTextbox(frame, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
        txt_history.pack(side="top", fill="both", expand=True)

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        def clear_history():
            hist_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "historial_estados.json")
            ConfigManager.save_json(hist_path, [], use_lock=False)
            load_history()
            
        ctk.CTkButton(controls, text=self.lang_manager.get("ai_mh_btn_reload"), command=lambda: load_history(), fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left")
        ctk.CTkButton(controls, text=self.lang_manager.get("ai_mh_btn_clear"), command=clear_history, fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("red")).pack(side="right")

        def load_history():
            txt_history.configure(state="normal")
            txt_history.delete("0.0", "end")
            hist_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "historial_estados.json")
            if os.path.exists(hist_path):
                data = ConfigManager.load_json(hist_path, use_lock=False)
                if isinstance(data, list):
                    if data:
                        for entry in reversed(data): # Del más reciente al más antiguo
                            if isinstance(entry, dict):
                                ts = entry.get("timestamp", "").split(".")[0]
                                mood = entry.get("estado_animo", "")
                                txt_history.insert("end", f"[{ts}]\n{mood}\n\n")
                    else:
                        txt_history.insert("end", self.lang_manager.get("ai_mh_msg_empty"))
                else:
                    txt_history.insert("end", self.lang_manager.get("ai_mh_msg_err_fmt"))
            else:
                txt_history.insert("end", self.lang_manager.get("ai_mh_msg_no_hist"))
            txt_history.configure(state="disabled")

        load_history()
        self.ai_reload_functions["config_ai_moods_history"] = load_history

    def create_ai_users_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_users"] = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_users_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.lang_manager.get("ai_users_desc"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=help_frame: self.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        # Controls (Bottom)
        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        # Table Header (Cabeceras de Columnas)
        table_header = ctk.CTkFrame(frame, fg_color=self.theme_manager.get("bg_card"), corner_radius=6)
        # Se añade padding izquierdo de 10 para alinear con el scroll interior, y 16 a la derecha por el scrollbar
        table_header.pack(side="top", fill="x", padx=(10, 16), pady=(0, 2))
        
        ctk.CTkLabel(table_header, text=self.lang_manager.get("ai_users_col_id"), width=150, anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.theme_manager.get("accent")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(table_header, text=self.lang_manager.get("ai_users_col_name"), width=150, anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.theme_manager.get("accent")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(table_header, text=self.lang_manager.get("ai_users_col_role"), width=150, anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.theme_manager.get("accent")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(table_header, text=self.lang_manager.get("ai_users_col_rel"), anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.theme_manager.get("accent")).pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Scrollable Content (Filas)
        scroll = ctk.CTkScrollableFrame(
            frame, 
            fg_color="transparent",
            scrollbar_button_color=self.theme_manager.get("bg_dark"),
            scrollbar_button_hover_color=self.theme_manager.get("bg_dark")
        )
        scroll.pack(side="top", fill="both", expand=True)

        self.users_entries_data = []
        file_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "known_users.json")

        def delete_user_record(uid_to_delete):
            try:
                data = ConfigManager.load_json(file_path, use_lock=False)
                if isinstance(data, dict) and uid_to_delete in data:
                    del data[uid_to_delete]
                    ConfigManager.save_json(file_path, data, use_lock=False)
                    load_users()
                    lbl_status.configure(text=self.lang_manager.get("ai_users_msg_del"), text_color=self.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e:
                lbl_status.configure(text=self.lang_manager.get("ai_users_msg_err_del").format(e=e), text_color=self.theme_manager.get("red"))
                self.after(3000, lambda: lbl_status.configure(text=""))

        def load_users():
            for widget in scroll.winfo_children():
                widget.destroy()
            self.users_entries_data.clear()
            
            data = ConfigManager.load_json(file_path, use_lock=False)
            if isinstance(data, dict) and data:
                try:
                    for uid, info in data.items():
                        row = ctk.CTkFrame(scroll, fg_color=self.theme_manager.get("bg_card"), corner_radius=8)
                        row.pack(fill="x", pady=4)
                        
                        btn_del = ctk.CTkButton(row, text="🗑", width=30, height=46, fg_color="transparent", hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("text_dim"))
                        btn_del.pack(side="right", padx=10, pady=10)
                        
                        # ID (Solo texto, seleccionable pero no editable)
                        id_entry = ctk.CTkEntry(row, width=150, height=46, fg_color="transparent", border_width=0, text_color=self.theme_manager.get("text_dim"))
                        id_entry.pack(side="left", padx=5, pady=10)
                        id_entry.insert(0, uid)
                        id_entry.configure(state="readonly")
                        
                        name_entry = ctk.CTkEntry(row, width=150, height=46, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
                        name_entry.pack(side="left", padx=5, pady=10)
                        name_entry.insert(0, info.get("nombre", ""))
                        
                        role_entry = ctk.CTkEntry(row, width=150, height=46, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
                        role_entry.pack(side="left", padx=5, pady=10)
                        role_entry.insert(0, info.get("rol_base", ""))
                        
                        rel_txt = ctk.CTkTextbox(row, height=46, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
                        rel_txt.pack(side="left", fill="x", expand=True, padx=(5, 10), pady=10)
                        rel_txt.insert("0.0", info.get("relacion", ""))
                        self._fix_scroll(rel_txt)
                        
                        self.users_entries_data.append({
                            "uid": uid, "nombre": name_entry, "rol_base": role_entry, "relacion": rel_txt
                        })
                        
                        btn_del.configure(command=lambda u=uid: delete_user_record(u))
                        
                    lbl_status.configure(text=self.lang_manager.get("ai_users_msg_loaded"), text_color=self.theme_manager.get("text_dim"))
                except Exception as e:
                    lbl_status.configure(text=self.lang_manager.get("ai_users_msg_err_load"), text_color=self.theme_manager.get("red"))
            else:
                lbl_status.configure(text=self.lang_manager.get("ai_users_msg_empty"), text_color=self.theme_manager.get("text_dim"))

        def save_users():
            data = {item["uid"]: {"nombre": item["nombre"].get().strip(), "rol_base": item["rol_base"].get().strip(), "relacion": item["relacion"].get("0.0", "end").strip()} for item in self.users_entries_data}
            try:
                ConfigManager.save_json(file_path, data, use_lock=False)
                lbl_status.configure(text=self.lang_manager.get("msg_saved_success"), text_color=self.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e:
                lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        def open_new_user_dialog():
            dialog = ctk.CTkToplevel(self)
            dialog.title(self.lang_manager.get("ai_users_dlg_title"))
            dialog.geometry("450x550")
            dialog.configure(fg_color=self.theme_manager.get("bg_dark"))
            dialog.transient(self) # Mantener la ventana por encima del launcher
            dialog.grab_set() # Bloquear interacción con la ventana principal
            
            ctk.CTkLabel(dialog, text=self.lang_manager.get("ai_users_dlg_header"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("accent")).pack(pady=(20, 10))
            
            form = ctk.CTkFrame(dialog, fg_color="transparent")
            form.pack(fill="both", expand=True, padx=20)
            
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_users_dlg_lbl_id"), text_color=self.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_id = ctk.CTkEntry(form, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
            entry_id.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_users_dlg_lbl_name"), text_color=self.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_name = ctk.CTkEntry(form, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
            entry_name.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_users_dlg_lbl_role"), text_color=self.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_role = ctk.CTkEntry(form, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
            entry_role.pack(fill="x", pady=(0, 10))
            entry_role.insert(0, self.lang_manager.get("ai_users_def_role")) # Valor por defecto
            
            ctk.CTkLabel(form, text=self.lang_manager.get("ai_users_dlg_lbl_rel"), text_color=self.theme_manager.get("text"), anchor="w").pack(fill="x")
            txt_rel = ctk.CTkTextbox(form, height=100, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
            txt_rel.pack(fill="x", pady=(0, 10))
            
            lbl_err = ctk.CTkLabel(dialog, text="", text_color=self.theme_manager.get("red"), font=ctk.CTkFont(size=12))
            lbl_err.pack(pady=(5, 5))
            
            def save_new():
                uid = entry_id.get().strip()
                name = entry_name.get().strip()
                role = entry_role.get().strip()
                rel = txt_rel.get("0.0", "end").strip()
                
                if not uid: return lbl_err.configure(text=self.lang_manager.get("ai_users_dlg_err_id_req"))
                if not uid.isdigit(): return lbl_err.configure(text=self.lang_manager.get("ai_users_dlg_err_id_num"))
                if not name: return lbl_err.configure(text=self.lang_manager.get("ai_users_dlg_err_name_req"))
                
                try:
                    data = ConfigManager.load_json(file_path, use_lock=False)
                    if not isinstance(data, dict): data = {}
                    if uid in data: return lbl_err.configure(text=self.lang_manager.get("ai_users_dlg_err_exists"))
                        
                    data[uid] = {"nombre": name, "rol_base": role, "relacion": rel}
                    ConfigManager.save_json(file_path, data, use_lock=False)
                    
                    dialog.destroy()
                    load_users()
                    lbl_status.configure(text=self.lang_manager.get("ai_users_dlg_msg_success"), text_color=self.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
                except Exception as e: lbl_err.configure(text=self.lang_manager.get("msg_err_saving").format(e=e))

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=(0, 20))
            
            ctk.CTkButton(btn_frame, text=self.lang_manager.get("btn_cancel"), width=100, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=dialog.destroy).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text=self.lang_manager.get("btn_save_short"), width=100, fg_color=self.theme_manager.get("accent"), hover_color=self.theme_manager.get("accent_dim"), text_color=self.theme_manager.get("bg_dark"), command=save_new).pack(side="left", padx=10)

        ctk.CTkButton(controls, text=self.lang_manager.get("btn_reload"), command=load_users, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.lang_manager.get("ai_users_btn_new"), command=open_new_user_dialog, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.lang_manager.get("btn_save_changes"), command=save_users, fg_color=self.theme_manager.get("accent"), hover_color=self.theme_manager.get("accent_dim"), text_color=self.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        load_users()
        self.ai_reload_functions["config_ai_users"] = load_users

    def create_ai_memory_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_memory"] = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_mem_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.lang_manager.get("ai_mem_desc"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=help_frame: self.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", scrollbar_button_color=self.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.theme_manager.get("bg_dark"))
        scroll.pack(side="top", fill="both", expand=True)

        mem_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "memoria.json")
        users_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "known_users.json")

        def toggle_facts(container, btn):
            if container.winfo_viewable():
                container.pack_forget()
                btn.configure(text=self.lang_manager.get("ai_mem_btn_expand"))
            else:
                container.pack(fill="x", pady=(0, 5))
                btn.configure(text=self.lang_manager.get("ai_mem_btn_collapse"))
                # Refrescar tamaños una vez que el contenedor es visible y tiene ancho
                def refresh():
                    for row in container.winfo_children():
                        for widget in row.winfo_children():
                            if isinstance(widget, ctk.CTkTextbox):
                                widget.event_generate("<KeyRelease>")
                container.after(50, refresh)

        def save_single_fact(uid, idx, new_text):
            try:
                data = ConfigManager.load_json(mem_path, use_lock=False)
                if isinstance(data, dict) and uid in data and len(data[uid]) > idx:
                    data[uid][idx] = new_text
                    ConfigManager.save_json(mem_path, data, use_lock=False)
                    lbl_status.configure(text=self.lang_manager.get("ai_mem_msg_saved"), text_color=self.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        def delete_single_fact(uid, idx):
            try:
                data = ConfigManager.load_json(mem_path, use_lock=False)
                if isinstance(data, dict) and uid in data and len(data[uid]) > idx:
                    data[uid].pop(idx)
                    if not data[uid]: del data[uid]
                    ConfigManager.save_json(mem_path, data, use_lock=False)
                    load_memory(expand_uid=uid)
                    lbl_status.configure(text=self.lang_manager.get("ai_mem_msg_del"), text_color=self.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        def add_new_fact_ui(uid):
            data = ConfigManager.load_json(mem_path, use_lock=False)
            if isinstance(data, dict):
                if uid not in data: data[uid] = []
                data[uid].append(self.lang_manager.get("ai_mem_new_fact"))
                ConfigManager.save_json(mem_path, data, use_lock=False)
                load_memory(expand_uid=uid)

        def build_fact_row(container, uid, idx, fact_text):
            row = ctk.CTkFrame(container, fg_color=self.theme_manager.get("bg_dark"), corner_radius=4)
            row.pack(fill="x", padx=15, pady=2)
            
            txt_fact = ctk.CTkTextbox(row, height=24, font=("Consolas", 12), fg_color="transparent", text_color=self.theme_manager.get("text"), wrap="word")
            txt_fact.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            txt_fact.insert("0.0", fact_text)
            self._fix_scroll(txt_fact)
            
            def resize_desc(event=None):
                try:
                    w = txt_fact.winfo_width()
                    # Si el ancho es muy pequeño (no renderizado), evitar contar 1 línea por letra
                    if w < 50:
                        lines = max(1, len(txt_fact.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = txt_fact._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    txt_fact.configure(height=max(24, lines * 18))
                except: pass
            txt_fact.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc)
            
            btn_save = ctk.CTkButton(row, text=self.lang_manager.get("btn_save_short"), width=80, height=26, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: save_single_fact(uid, idx, txt_fact.get("0.0", "end").strip()))
            btn_save.pack(side="right", padx=(5, 5), pady=5)
            
            btn_del = ctk.CTkButton(row, text=self.lang_manager.get("ai_mem_btn_del"), width=80, height=26, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("red"), command=lambda: delete_single_fact(uid, idx))
            btn_del.pack(side="right", padx=(5, 0), pady=5)

        def load_memory(expand_uid=None):
            for w in scroll.winfo_children(): w.destroy()
            
            mem_data = ConfigManager.load_json(mem_path, use_lock=False)
            if not isinstance(mem_data, dict): mem_data = {}
            users_data = ConfigManager.load_json(users_path, use_lock=False)
            if not isinstance(users_data, dict): users_data = {}
            # Fusionar todos los usuarios conocidos con los que ya tienen memorias
            all_uids = list(users_data.keys())
            for uid in mem_data.keys():
                if uid not in all_uids:
                    all_uids.append(uid)

            if not all_uids:
                ctk.CTkLabel(scroll, text=self.lang_manager.get("ai_mem_msg_empty"), text_color=self.theme_manager.get("text_dim")).pack(pady=20)
                lbl_status.configure(text=self.lang_manager.get("ai_mem_msg_list_empty"), text_color=self.theme_manager.get("text_dim"))
                return

            for uid in all_uids:
                uname = users_data.get(uid, {}).get("nombre", self.lang_manager.get("msg_unknown"))
                facts = mem_data.get(uid, [])
                
                user_card = ctk.CTkFrame(scroll, fg_color=self.theme_manager.get("bg_card"), corner_radius=8)
                user_card.pack(fill="x", pady=5)
                
                header_row = ctk.CTkFrame(user_card, fg_color="transparent")
                header_row.pack(fill="x", padx=15, pady=8)
                
                ctk.CTkLabel(header_row, text=f"{uid} : {uname}", font=ctk.CTkFont(weight="bold", size=14), text_color=self.theme_manager.get("accent")).pack(side="left")
                
                btn_toggle = ctk.CTkButton(header_row, text=self.lang_manager.get("ai_mem_btn_expand"), width=100, height=28, fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"))
                btn_toggle.pack(side="right")
                
                facts_container = ctk.CTkFrame(user_card, fg_color="transparent")
                
                if expand_uid == uid:
                    facts_container.pack(fill="x", pady=(0, 5))
                    btn_toggle.configure(text=self.lang_manager.get("ai_mem_btn_collapse"))
                    
                btn_toggle.configure(command=lambda c=facts_container, b=btn_toggle: toggle_facts(c, b))
                
                for idx, fact in enumerate(facts):
                    build_fact_row(facts_container, uid, idx, fact)
                    
                add_row = ctk.CTkFrame(facts_container, fg_color="transparent")
                add_row.pack(fill="x", pady=(2, 6), padx=15)
                ctk.CTkButton(add_row, text=self.lang_manager.get("ai_mem_btn_add"), height=26, fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda u=uid: add_new_fact_ui(u)).pack(side="right")

            lbl_status.configure(text=self.lang_manager.get("ai_mem_msg_loaded"), text_color=self.theme_manager.get("text_dim"))

        ctk.CTkButton(controls, text=self.lang_manager.get("btn_reload"), command=load_memory, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)

        load_memory()
        self.ai_reload_functions["config_ai_memory"] = load_memory

    def create_ai_opinions_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_opinions"] = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_opi_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.lang_manager.get("ai_opi_desc"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=help_frame: self.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        opinions_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "opiniones.json")
        users_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "known_users.json")

        scroll_users = ctk.CTkScrollableFrame(frame, fg_color="transparent", scrollbar_button_color=self.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.theme_manager.get("bg_dark"))
        scroll_users.pack(fill="both", expand=True)

        def save_single_opinion(uid, val_afinidad, val_relacion, txt_opinion):
            try:
                op_data = ConfigManager.load_json(opinions_path, use_lock=False)
                if not isinstance(op_data, dict): op_data = {}
                
                try: aff_int = int(val_afinidad.get().strip())
                except: aff_int = 0
                
                op_data[uid] = {
                    "afinidad": aff_int,
                    "relacion": val_relacion.get().strip(),
                    "opinion": txt_opinion.get("0.0", "end").strip()
                }
                ConfigManager.save_json(opinions_path, op_data, use_lock=False)
                lbl_status.configure(text=self.lang_manager.get("ai_opi_msg_saved"), text_color=self.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        def delete_single_opinion(uid):
            try:
                op_data = ConfigManager.load_json(opinions_path, use_lock=False)
                if isinstance(op_data, dict) and uid in op_data:
                    del op_data[uid]
                    ConfigManager.save_json(opinions_path, op_data, use_lock=False)
                    load_opinions()
                    lbl_status.configure(text=self.lang_manager.get("ai_opi_msg_del"), text_color=self.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        def load_opinions():
            for w in scroll_users.winfo_children(): w.destroy()
            op_data = ConfigManager.load_json(opinions_path, use_lock=False)
            if not isinstance(op_data, dict): op_data = {}
            users_data = ConfigManager.load_json(users_path, use_lock=False)
            if not isinstance(users_data, dict): users_data = {}
                
            all_uids = list(users_data.keys())
            for uid in op_data.keys():
                if uid not in all_uids: all_uids.append(uid)
                
            if not all_uids:
                ctk.CTkLabel(scroll_users, text=self.lang_manager.get("ai_opi_msg_empty"), text_color=self.theme_manager.get("text_dim")).pack(pady=20)
            else:
                for uid in all_uids:
                    uname = users_data.get(uid, {}).get("nombre", self.lang_manager.get("msg_unknown"))
                    user_op = op_data.get(uid, {})
                    
                    card = ctk.CTkFrame(scroll_users, fg_color=self.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.theme_manager.get("border"))
                    card.pack(fill="x", pady=6, padx=5)
                    
                    top = ctk.CTkFrame(card, fg_color="transparent")
                    top.pack(fill="x", padx=15, pady=(10, 5))
                    ctk.CTkLabel(top, text=f"{uid} : {uname}", font=ctk.CTkFont(weight="bold", size=14), text_color=self.theme_manager.get("accent")).pack(side="left")
                    
                    ctk.CTkLabel(top, text=self.lang_manager.get("ai_opi_lbl_aff"), text_color=self.theme_manager.get("text_dim")).pack(side="left", padx=(20, 5))
                    ent_aff = ctk.CTkEntry(top, width=50, height=28, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"))
                    ent_aff.pack(side="left")
                    ent_aff.insert(0, str(user_op.get("afinidad", 0)))
                    
                    ctk.CTkLabel(top, text=self.lang_manager.get("ai_opi_lbl_rel"), text_color=self.theme_manager.get("text_dim")).pack(side="left", padx=(20, 5))
                    ent_rel = ctk.CTkEntry(top, width=150, height=28, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"))
                    ent_rel.pack(side="left")
                    ent_rel.insert(0, user_op.get("relacion", self.lang_manager.get("ai_opi_def_rel")))
                    
                    mid = ctk.CTkFrame(card, fg_color="transparent")
                    mid.pack(fill="x", padx=15, pady=5)
                    txt_op = ctk.CTkTextbox(mid, height=65, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
                    txt_op.pack(fill="x", expand=True)
                    txt_op.insert("0.0", user_op.get("opinion", ""))
                    self._fix_scroll(txt_op)
                    
                    def resize_desc(event=None, t=txt_op):
                        try:
                            w = t.winfo_width()
                            if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                            else:
                                dl = t._textbox.count("1.0", "end", "displaylines")
                                lines = dl[0] if dl else 1
                            t.configure(height=max(65, lines * 18))
                        except: pass
                    txt_op.bind("<KeyRelease>", resize_desc)
                    self.after(50, resize_desc)
                    
                    bot = ctk.CTkFrame(card, fg_color="transparent")
                    bot.pack(fill="x", padx=15, pady=(0, 10))
                    btn_save = ctk.CTkButton(bot, text=self.lang_manager.get("btn_save_short"), width=80, height=26, fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda u=uid, a=ent_aff, r=ent_rel, o=txt_op: save_single_opinion(u, a, r, o))
                    btn_save.pack(side="right", padx=(5, 0))
                    btn_del = ctk.CTkButton(bot, text=self.lang_manager.get("ai_mem_btn_del"), width=80, height=26, fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("red"), command=lambda u=uid: delete_single_opinion(u))
                    btn_del.pack(side="right", padx=(5, 5))

            lbl_status.configure(text=self.lang_manager.get("ai_opi_msg_loaded"), text_color=self.theme_manager.get("text_dim"))

        ctk.CTkButton(controls, text=self.lang_manager.get("btn_reload"), command=load_opinions, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        
        load_opinions()
        self.ai_reload_functions["config_ai_opinions"] = load_opinions

    def create_ai_ranges_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_ranges"] = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_rng_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.lang_manager.get("ai_rng_desc"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=help_frame: self.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        # --- LÍMITES Y BARRA VISUAL ---
        limits_frame = ctk.CTkFrame(frame, fg_color="transparent")
        limits_frame.pack(side="top", fill="x", padx=20, pady=(0, 5))
        
        ctk.CTkLabel(limits_frame, text=self.lang_manager.get("ai_rng_lbl_gmin"), text_color=self.theme_manager.get("text_dim")).pack(side="left")
        ent_gmin = ctk.CTkEntry(limits_frame, width=60, height=28, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"))
        ent_gmin.pack(side="left", padx=10)
        
        ctk.CTkLabel(limits_frame, text=self.lang_manager.get("ai_rng_lbl_gmax"), text_color=self.theme_manager.get("text_dim")).pack(side="left", padx=(20, 0))
        ent_gmax = ctk.CTkEntry(limits_frame, width=60, height=28, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"))
        ent_gmax.pack(side="left", padx=10)
        
        lbl_bar_status = ctk.CTkLabel(limits_frame, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(size=12, weight="bold"))
        lbl_bar_status.pack(side="right")

        bar_wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        bar_wrapper.pack(side="top", fill="x", padx=20, pady=(10, 10))
        
        self.range_visual_data = {}
        
        canvas = ctk.CTkCanvas(bar_wrapper, height=70, bg=self.theme_manager.get("bg_dark"), highlightthickness=0)
        canvas.pack(side="top", fill="x", expand=True)
        
        info_label = ctk.CTkLabel(bar_wrapper, text=self.lang_manager.get("ai_rng_lbl_info"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12))
        info_label.pack(side="top", pady=(5, 0))

        def update_bar(event=None):
            canvas.delete("all")
            width = canvas.winfo_width()
            if width <= 1: return # Se redibuja automáticamente al mostrarse la ventana
            
            try: g_min = int(ent_gmin.get().strip())
            except: g_min = -100
            try: g_max = int(ent_gmax.get().strip())
            except: g_max = 100
            
            if g_max <= g_min:
                lbl_bar_status.configure(text=self.lang_manager.get("ai_rng_err_glim"), text_color=self.theme_manager.get("red"))
                return
                
            span = g_max - g_min
            
            # Función para generar el gradiente de color basado en la posición global
            def get_color_gradient(val):
                p = (val - g_min) / span
                p = max(0.0, min(1.0, p))
                
                c1 = (247, 118, 142) # Rojo (Odio / Negativo)
                c2 = (224, 175, 104) # Naranja/Amarillo (Neutral)
                c3 = (158, 206, 106) # Verde (Afinidad alta)
                
                if p < 0.5:
                    p2 = p * 2.0
                    r, g_c, b = [int(c1[idx] + (c2[idx] - c1[idx]) * p2) for idx in range(3)]
                else:
                    p2 = (p - 0.5) * 2.0
                    r, g_c, b = [int(c2[idx] + (c3[idx] - c2[idx]) * p2) for idx in range(3)]
                return f"#{r:02x}{g_c:02x}{b:02x}"

            ranges = []
            
            has_error = False
            error_msg = ""
            
            for i, d in enumerate(self.ranges_entries):
                try: mn = int(d["min"].get().strip())
                except: mn = 0
                try: mx = int(d["max"].get().strip())
                except: mx = 0
                
                if mn > mx:
                    has_error = True
                    error_msg = self.lang_manager.get("ai_rng_err_inv")
                elif mn < g_min or mx > g_max:
                    has_error = True
                    error_msg = self.lang_manager.get("ai_rng_err_out").format(g_min=g_min, g_max=g_max)
                    
                mid_val = (mn + mx) / 2
                col = get_color_gradient(mid_val)
                ranges.append({"min": mn, "max": mx, "etiq": d["etiq"].get().strip(), "col": col, "id": d["id"]})
            
            ranges.sort(key=lambda x: x["min"])
            
            has_overlap = False
            for i in range(len(ranges)-1):
                if ranges[i]["max"] >= ranges[i+1]["min"]:
                    has_overlap = True
                    has_error = True
                    error_msg = self.lang_manager.get("ai_rng_err_over")
                    break
            
            if has_error: lbl_bar_status.configure(text=error_msg, text_color=self.theme_manager.get("red"))
            else: lbl_bar_status.configure(text=self.lang_manager.get("ai_rng_ok_valid"), text_color=self.theme_manager.get("green"))
            
            # Fondo base de la barra (De 45px a 70px)
            canvas.create_rectangle(0, 45, width, 70, fill=self.theme_manager.get("bg_sidebar"), outline=self.theme_manager.get("border"))
                
            # Calcular y dibujar "Zonas Muertas" (Gaps) sobre la barra
            if not has_overlap and not has_error:
                curr = g_min - 1 # Inicializamos 1 antes del límite para evaluar precisión estricta
                gaps = []
                for r in ranges:
                    if r["min"] - curr > 1: gaps.append((curr + 1, r["min"] - 1))
                    curr = max(curr, r["max"])
                if g_max - curr > 0: gaps.append((curr + 1, g_max))
                
                for i, (gap_min, gap_max) in enumerate(gaps):
                    x1 = max(0, (gap_min - g_min) / span * width)
                    x2 = min(width, (gap_max - g_min) / span * width)
                    
                    canvas.create_rectangle(x1, 45, x2, 70, fill="#331a20", outline=self.theme_manager.get("red"))
                    
                    mid_x = (x1 + x2) / 2
                    y_text = 5 if i % 2 == 0 else 22 # Alternar altura de textos para evitar choques
                    canvas.create_line(mid_x, 45, mid_x, y_text + 14, fill=self.theme_manager.get("red"))
                    canvas.create_text(mid_x, y_text, text=self.lang_manager.get("ai_rng_lbl_gap").format(gap_min=gap_min, gap_max=gap_max), fill=self.theme_manager.get("red"), anchor="n", font=("Consolas", 10, "bold"))
            
            self.range_visual_data.clear()
            
            for r in ranges:
                if r["min"] > r["max"]: continue
                draw_min = max(g_min, r["min"])
                draw_max = min(g_max, r["max"])
                if draw_max < draw_min: continue # Completamente fuera de límites
                
                rel_x = (draw_min - g_min) / span
                rel_w = (draw_max - draw_min) / span
                x1 = rel_x * width
                x2 = (rel_x + rel_w) * width
                
                if x1 == x2: x2 += 3 # Asegurar un mínimo de visibilidad visual si el rango es de un solo número
                
                tag = f"rect_{r['id']}"
                canvas.create_rectangle(x1, 45, x2, 70, fill=r["col"], outline=self.theme_manager.get("bg_dark"), tags=(tag,))
                
                hover_txt = f"[{r['min']} a {r['max']}] {r['etiq']}"
                self.range_visual_data[r['id']] = {"tag": tag, "text": hover_txt}
                
                def on_enter(e, tg=tag, txt=hover_txt):
                    info_label.configure(text=txt, text_color=self.theme_manager.get("accent"))
                    canvas.itemconfig(tg, outline="white", width=2)
                def on_leave(e, tg=tag):
                    info_label.configure(text=self.lang_manager.get("ai_rng_lbl_info"), text_color=self.theme_manager.get("text_dim"))
                    canvas.itemconfig(tg, outline=self.theme_manager.get("bg_dark"), width=1)
                    
                canvas.tag_bind(tag, "<Enter>", on_enter)
                canvas.tag_bind(tag, "<Leave>", on_leave)
                
        canvas.bind("<Configure>", update_bar)

        scroll_ranges = ctk.CTkScrollableFrame(frame, fg_color="transparent", scrollbar_button_color=self.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.theme_manager.get("bg_dark"))
        scroll_ranges.pack(fill="both", expand=True)

        ranges_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "afinidad_rangos.json")
        self.ranges_entries = []

        def sort_ranges_ui():
            def get_sort_key(d):
                try: mx = int(d["max"].get().strip())
                except: mx = -999999
                try: mn = int(d["min"].get().strip())
                except: mn = -999999
                return (mx, mn) # Ordenar por Máximo (Mayor a menor), luego por Mínimo
            
            self.ranges_entries.sort(key=get_sort_key, reverse=True)
            for d in self.ranges_entries:
                d["row"].pack_forget()
                d["row"].pack(fill="x", pady=5)

        def add_range_ui(min_v, max_v, etiq, desc):
            row = ctk.CTkFrame(scroll_ranges, fg_color=self.theme_manager.get("bg_dark"), corner_radius=8)
            row.pack(fill="x", pady=5)
            
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(10, 5))
            
            ctk.CTkLabel(top, text=self.lang_manager.get("ai_rng_lbl_min"), text_color=self.theme_manager.get("text_dim")).pack(side="left")
            ent_min = ctk.CTkEntry(top, width=50, height=28, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"))
            ent_min.pack(side="left", padx=5)
            ent_min.insert(0, str(min_v))
            
            ctk.CTkLabel(top, text=self.lang_manager.get("ai_rng_lbl_max"), text_color=self.theme_manager.get("text_dim")).pack(side="left")
            ent_max = ctk.CTkEntry(top, width=50, height=28, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"))
            ent_max.pack(side="left", padx=5)
            ent_max.insert(0, str(max_v))
            
            ctk.CTkLabel(top, text=self.lang_manager.get("ai_rng_lbl_tag"), text_color=self.theme_manager.get("text_dim")).pack(side="left", padx=(10,0))
            ent_etiq = ctk.CTkEntry(top, width=150, height=28, fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold"))
            ent_etiq.pack(side="left", fill="x", expand=True, padx=5)
            ent_etiq.insert(0, etiq)
            
            btn_del = ctk.CTkButton(top, text="🗑", width=30, height=28, fg_color="transparent", hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("text_dim"))
            btn_del.pack(side="right")
            
            bot = ctk.CTkFrame(row, fg_color="transparent")
            bot.pack(fill="x", padx=10, pady=(0, 10))
            
            txt_desc = ctk.CTkTextbox(bot, height=40, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_card"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
            txt_desc.pack(fill="x")
            txt_desc.insert("0.0", desc)
            self._fix_scroll(txt_desc)
            
            def resize_desc_r(event=None, t=txt_desc):
                try:
                    w = t.winfo_width()
                    if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = t._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    t.configure(height=max(40, lines * 18))
                except: pass
            txt_desc.bind("<KeyRelease>", resize_desc_r)
            self.after(50, resize_desc_r)
            
            row_id = str(id(row))
            entry_data = {"row": row, "min": ent_min, "max": ent_max, "etiq": ent_etiq, "desc": txt_desc, "id": row_id}
            self.ranges_entries.append(entry_data)
            
            def on_focus_in(event):
                data = self.range_visual_data.get(row_id)
                if data:
                    info_label.configure(text=data["text"], text_color=self.theme_manager.get("accent"))
                    canvas.itemconfig(data["tag"], outline="white", width=2)
            
            def delayed_sort():
                try:
                    focused = self.focus_get()
                    # Si el nuevo lugar donde hiciste clic sigue estando dentro de esta misma fila, no ordenar todavía
                    if focused and str(row) in str(focused): return
                except: pass
                sort_ranges_ui()
                
            def on_focus_out(event):
                data = self.range_visual_data.get(row_id)
                if data:
                    info_label.configure(text=self.lang_manager.get("ai_rng_lbl_info"), text_color=self.theme_manager.get("text_dim"))
                    canvas.itemconfig(data["tag"], outline=self.theme_manager.get("bg_dark"), width=1)
                self.after(200, delayed_sort)
            
            ent_min.bind("<KeyRelease>", update_bar)
            ent_max.bind("<KeyRelease>", update_bar)
            ent_min.bind("<FocusIn>", on_focus_in, add="+")
            ent_max.bind("<FocusIn>", on_focus_in, add="+")
            ent_etiq.bind("<FocusIn>", on_focus_in, add="+")
            ent_min.bind("<FocusOut>", on_focus_out, add="+")
            ent_max.bind("<FocusOut>", on_focus_out, add="+")
            ent_etiq.bind("<FocusOut>", on_focus_out, add="+")
            
            btn_del.configure(command=lambda r=row, d=entry_data: delete_range(r, d))
            self.after(50, update_bar)

        def delete_range(row, data):
            row.destroy()
            if data in self.ranges_entries:
                self.ranges_entries.remove(data)
            update_bar()

        def save_ranges():
            sort_ranges_ui() # Asegurar ordenamiento antes de guardar
            new_ranges = []
            for d in self.ranges_entries:
                try: mn = int(d["min"].get().strip())
                except: mn = 0
                try: mx = int(d["max"].get().strip())
                except: mx = 0
                new_ranges.append({
                    "min": mn, "max": mx,
                    "etiqueta": d["etiq"].get().strip(),
                    "descripcion": d["desc"].get("0.0", "end").strip()
                })
            try:
                ConfigManager.save_json(ranges_path, new_ranges, use_lock=False)
                
                # Guardar limites globales en config
                cfg = self._load_json_file("config.json")
                if "ai_config" not in cfg: cfg["ai_config"] = {}
                try: cfg["ai_config"]["aff_min"] = int(ent_gmin.get().strip())
                except: pass
                try: cfg["ai_config"]["aff_max"] = int(ent_gmax.get().strip())
                except: pass
                self._save_json_file("config.json", cfg)
                lbl_status.configure(text=self.lang_manager.get("ai_rng_msg_saved"), text_color=self.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        btns_ranges = ctk.CTkFrame(controls, fg_color="transparent")
        btns_ranges.pack(side="left")
        ctk.CTkButton(btns_ranges, text=self.lang_manager.get("btn_reload"), command=lambda: load_ranges(), fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(btns_ranges, text=self.lang_manager.get("ai_rng_btn_add"), command=lambda: (add_range_ui(0, 0, self.lang_manager.get("ai_rng_def_new"), ""), sort_ranges_ui()), fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(btns_ranges, text=self.lang_manager.get("btn_save_changes"), command=save_ranges, fg_color=self.theme_manager.get("accent"), hover_color=self.theme_manager.get("accent_dim"), text_color=self.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        def load_ranges():
            for w in scroll_ranges.winfo_children(): w.destroy()
            
            cfg = self._load_json_file("config.json").get("ai_config", {})
            ent_gmin.delete(0, "end")
            ent_gmin.insert(0, str(cfg.get("aff_min", -100)))
            ent_gmax.delete(0, "end")
            ent_gmax.insert(0, str(cfg.get("aff_max", 100)))
            
            self.ranges_entries.clear()
            
            rangos = ConfigManager.load_json(ranges_path, use_lock=False)
            if isinstance(rangos, list) and rangos:
                for r in rangos:
                    add_range_ui(r.get("min", 0), r.get("max", 0), r.get("etiqueta", ""), r.get("descripcion", ""))
            else:
                defaults = [
                    {"min": -100, "max": -50, "etiqueta": self.lang_manager.get("ai_rng_def_hate"), "descripcion": self.lang_manager.get("ai_rng_def_hate_desc")},
                    {"min": -49, "max": -11, "etiqueta": self.lang_manager.get("ai_rng_def_annoy"), "descripcion": self.lang_manager.get("ai_rng_def_annoy_desc")},
                    {"min": -10, "max": 10, "etiqueta": self.lang_manager.get("ai_rng_def_neutral"), "descripcion": self.lang_manager.get("ai_rng_def_neutral_desc")},
                    {"min": 11, "max": 49, "etiqueta": self.lang_manager.get("ai_rng_def_friend"), "descripcion": self.lang_manager.get("ai_rng_def_friend_desc")},
                    {"min": 50, "max": 100, "etiqueta": self.lang_manager.get("ai_rng_def_close"), "descripcion": self.lang_manager.get("ai_rng_def_close_desc")}
                ]
                for r in defaults:
                    add_range_ui(r["min"], r["max"], r["etiqueta"], r["descripcion"])
            
            sort_ranges_ui()
            self.after(50, update_bar)
            lbl_status.configure(text=self.lang_manager.get("ai_rng_msg_loaded"), text_color=self.theme_manager.get("text_dim"))

        load_ranges()
        ent_gmin.bind("<KeyRelease>", update_bar)
        ent_gmax.bind("<KeyRelease>", update_bar)
        self.ai_reload_functions["config_ai_ranges"] = load_ranges

    def create_ai_self_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_self"] = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_self_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.lang_manager.get("ai_self_desc"), text_color=self.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda h=help_frame: self.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        # Botones 50/50 para pestañas
        tab_container = ctk.CTkFrame(frame, fg_color="transparent")
        tab_container.pack(side="top", fill="x", pady=(0, 10))
        
        scroll_gustos = ctk.CTkScrollableFrame(frame, fg_color="transparent", scrollbar_button_color=self.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.theme_manager.get("bg_dark"))
        scroll_opiniones = ctk.CTkScrollableFrame(frame, fg_color="transparent", scrollbar_button_color=self.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.theme_manager.get("bg_dark"))

        def switch_tab(tab_name):
            if tab_name == "Gustos":
                btn_gustos.configure(fg_color=self.theme_manager.get("accent"), text_color=self.theme_manager.get("bg_dark"))
                btn_opiniones.configure(fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"))
                scroll_opiniones.pack_forget()
                scroll_gustos.pack(side="top", fill="both", expand=True)
            else:
                btn_opiniones.configure(fg_color=self.theme_manager.get("accent"), text_color=self.theme_manager.get("bg_dark"))
                btn_gustos.configure(fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"))
                scroll_gustos.pack_forget()
                scroll_opiniones.pack(side="top", fill="both", expand=True)

        btn_gustos = ctk.CTkButton(tab_container, text=self.lang_manager.get("ai_self_tab_likes"), command=lambda: switch_tab("Gustos"), fg_color=self.theme_manager.get("accent"), text_color=self.theme_manager.get("bg_dark"), height=36, corner_radius=8, font=ctk.CTkFont(weight="bold"))
        btn_gustos.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_opiniones = ctk.CTkButton(tab_container, text=self.lang_manager.get("ai_self_tab_opinions"), command=lambda: switch_tab("Opiniones"), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), hover_color=self.theme_manager.get("border"), height=36, corner_radius=8, font=ctk.CTkFont(weight="bold"))
        btn_opiniones.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Controls Bottom
        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        data_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "autoconcepto.json")
        self.gustos_entries = []
        self.opiniones_entries = []

        def add_gusto_ui(text):
            row = ctk.CTkFrame(scroll_gustos, fg_color=self.theme_manager.get("bg_card"), corner_radius=6)
            row.pack(fill="x", pady=4)
            
            txt_g = ctk.CTkTextbox(row, height=24, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
            txt_g.pack(side="left", fill="x", expand=True, padx=10, pady=5)
            txt_g.insert("0.0", text)
            self._fix_scroll(txt_g)
            
            def resize_desc(event=None, t=txt_g):
                try:
                    w = t.winfo_width()
                    if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = t._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    t.configure(height=max(24, lines * 18))
                except: pass
            txt_g.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc)
            
            entry_data = {"row": row, "txt": txt_g}
            self.gustos_entries.append(entry_data)
            
            btn_del = ctk.CTkButton(row, text="🗑", width=30, height=26, fg_color="transparent", hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("text_dim"), command=lambda r=row, d=entry_data: delete_gusto(r, d))
            btn_del.pack(side="right", padx=(5, 10), pady=5)

        def delete_gusto(row, data):
            row.destroy()
            if data in self.gustos_entries:
                self.gustos_entries.remove(data)

        def add_opinion_ui(tema, opinion):
            card = ctk.CTkFrame(scroll_opiniones, fg_color=self.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.theme_manager.get("border"))
            card.pack(fill="x", pady=6)
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(top, text=self.lang_manager.get("ai_self_lbl_topic"), text_color=self.theme_manager.get("text_dim")).pack(side="left")
            ent_tema = ctk.CTkEntry(top, width=200, height=28, fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold"))
            ent_tema.pack(side="left", fill="x", expand=True, padx=10)
            ent_tema.insert(0, tema)
            
            btn_del = ctk.CTkButton(top, text="🗑", width=30, height=28, fg_color="transparent", hover_color=self.theme_manager.get("red"), text_color=self.theme_manager.get("text_dim"))
            btn_del.pack(side="right")
            
            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(fill="x", padx=15, pady=5)
            
            txt_op = ctk.CTkTextbox(mid, height=40, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
            txt_op.pack(fill="x", expand=True, pady=(0, 10))
            txt_op.insert("0.0", opinion)
            self._fix_scroll(txt_op)
            
            def resize_desc(event=None, t=txt_op):
                try:
                    w = t.winfo_width()
                    if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = t._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    t.configure(height=max(40, lines * 18))
                except: pass
            txt_op.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc)
            
            entry_data = {"card": card, "tema": ent_tema, "opinion": txt_op}
            self.opiniones_entries.append(entry_data)
            btn_del.configure(command=lambda c=card, d=entry_data: delete_opinion(c, d))

        def delete_opinion(card, data):
            card.destroy()
            if data in self.opiniones_entries:
                self.opiniones_entries.remove(data)

        add_g_btn_frame = ctk.CTkFrame(scroll_gustos, fg_color="transparent")
        ctk.CTkButton(add_g_btn_frame, text=self.lang_manager.get("ai_self_btn_add_like"), height=28, fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: add_gusto_ui(self.lang_manager.get("ai_self_new_like"))).pack(pady=10)

        add_o_btn_frame = ctk.CTkFrame(scroll_opiniones, fg_color="transparent")
        ctk.CTkButton(add_o_btn_frame, text=self.lang_manager.get("ai_self_btn_add_opinion"), height=28, fg_color=self.theme_manager.get("bg_dark"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: add_opinion_ui(self.lang_manager.get("ai_self_new_topic"), self.lang_manager.get("ai_self_new_opinion"))).pack(pady=10)

        def load_self():
            for data in self.gustos_entries: data["row"].destroy()
            self.gustos_entries.clear()
            for data in self.opiniones_entries: data["card"].destroy()
            self.opiniones_entries.clear()
            
            add_g_btn_frame.pack_forget()
            add_o_btn_frame.pack_forget()

            data = ConfigManager.load_json(data_path, use_lock=False)
            if isinstance(data, dict):
                gustos = data.get("gustos", [])
                for g in gustos: add_gusto_ui(g)
                
                ops = data.get("opiniones", {})
                for tema, op in ops.items(): add_opinion_ui(tema, op)
                
            add_g_btn_frame.pack(fill="x")
            add_o_btn_frame.pack(fill="x")
            lbl_status.configure(text=self.lang_manager.get("ai_self_msg_loaded"), text_color=self.theme_manager.get("text_dim"))

        def save_self():
            new_gustos = []
            for d in self.gustos_entries:
                val = d["txt"].get("0.0", "end").strip()
                if val: new_gustos.append(val)
                
            new_ops = {}
            for d in self.opiniones_entries:
                tema = d["tema"].get().strip()
                op = d["opinion"].get("0.0", "end").strip()
                if tema: new_ops[tema] = op
                
            data = {"gustos": new_gustos, "opiniones": new_ops}
            try:
                ConfigManager.save_json(data_path, data, use_lock=False)
                lbl_status.configure(text=self.lang_manager.get("msg_saved_success"), text_color=self.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        btns_self = ctk.CTkFrame(controls, fg_color="transparent")
        btns_self.pack(side="left")
        ctk.CTkButton(btns_self, text=self.lang_manager.get("btn_reload"), command=load_self, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(btns_self, text=self.lang_manager.get("btn_save_changes"), command=save_self, fg_color=self.theme_manager.get("accent"), hover_color=self.theme_manager.get("accent_dim"), text_color=self.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        switch_tab("Gustos")
        load_self()
        self.ai_reload_functions["config_ai_self"] = load_self

    def create_ai_prompts_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["config_ai_prompts"] = frame

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.lang_manager.get("ai_prompts_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left")

        # Caja de advertencia de edición
        warn_box = ctk.CTkFrame(frame, fg_color="#331a20", border_color=self.theme_manager.get("red"), border_width=1, corner_radius=8)
        warn_box.pack(side="top", fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(warn_box, text=self.lang_manager.get("warn_important_title"), font=ctk.CTkFont(weight="bold"), text_color=self.theme_manager.get("red")).pack(pady=(10, 0))
        ctk.CTkLabel(warn_box, text=self.lang_manager.get("ai_prompts_warn_desc"), text_color=self.theme_manager.get("red"), justify="center").pack(pady=(5, 10))

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))

        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", scrollbar_button_color=self.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.theme_manager.get("bg_dark"))
        scroll.pack(side="top", fill="both", expand=True)

        prompts_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "prompts.json")
        self.prompt_entries = {}

        prompt_defs = [
            ("evolucion_analisis", self.lang_manager.get("ai_prompts_evo_title"), self.lang_manager.get("ai_prompts_evo_desc")),
            ("memoria_opiniones", self.lang_manager.get("ai_prompts_soc_title"), self.lang_manager.get("ai_prompts_soc_desc")),
            ("memoria_autoconcepto", self.lang_manager.get("ai_prompts_self_title"), self.lang_manager.get("ai_prompts_self_desc")),
            ("memoria_filtrado", self.lang_manager.get("ai_prompts_facts_title"), self.lang_manager.get("ai_prompts_facts_desc"))
        ]

        for key, title, desc in prompt_defs:
            card = ctk.CTkFrame(scroll, fg_color=self.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.theme_manager.get("border"))
            card.pack(fill="x", padx=20, pady=8)
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(top, text=title, font=ctk.CTkFont(weight="bold", size=14), text_color=self.theme_manager.get("accent")).pack(side="left")
            ctk.CTkLabel(top, text=f"({key})", font=ctk.CTkFont(size=12), text_color=self.theme_manager.get("text_dim")).pack(side="left", padx=10)
            ctk.CTkLabel(top, text=desc, font=ctk.CTkFont(size=12), text_color=self.theme_manager.get("text_dim")).pack(side="right")
            
            txt_box = ctk.CTkTextbox(card, height=120, font=("Consolas", 12), fg_color=self.theme_manager.get("bg_dark"), border_color=self.theme_manager.get("border"), border_width=1, text_color=self.theme_manager.get("text"), wrap="word")
            txt_box.pack(fill="x", padx=15, pady=(0, 15))
            self._fix_scroll(txt_box)
            
            def resize_desc(event=None, t=txt_box):
                try:
                    dl = t._textbox.count("1.0", "end", "displaylines")
                    lines = dl[0] if dl else 1
                    t.configure(height=max(80, lines * 18))
                except: pass
            txt_box.bind("<KeyRelease>", resize_desc)
            
            self.prompt_entries[key] = {"txt": txt_box, "resize": resize_desc}

        def load_prompts():
            data = ConfigManager.load_json(prompts_path, use_lock=False)
            if isinstance(data, dict):
                for key, entry in self.prompt_entries.items():
                    entry["txt"].delete("0.0", "end")
                    entry["txt"].insert("0.0", data.get(key, ""))
                    self.after(50, entry["resize"])

        def save_prompts():
            data = {}
            for key, entry in self.prompt_entries.items():
                data[key] = entry["txt"].get("0.0", "end").strip()
            try:
                ConfigManager.save_json(prompts_path, data, use_lock=False)
                lbl_status.configure(text=self.lang_manager.get("ai_prompts_msg_saved"), text_color=self.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e:
                lbl_status.configure(text=self.lang_manager.get("msg_err_generic").format(e=e), text_color=self.theme_manager.get("red"))

        ctk.CTkButton(controls, text=self.lang_manager.get("btn_reload"), command=load_prompts, fg_color=self.theme_manager.get("bg_card"), hover_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.lang_manager.get("ai_prompts_btn_save"), command=save_prompts, fg_color=self.theme_manager.get("accent"), hover_color=self.theme_manager.get("accent_dim"), text_color=self.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        load_prompts()
        self.ai_reload_functions["config_ai_prompts"] = load_prompts

    def create_discord_guide_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["discord_guide"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header, text=self.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: self.show_frame("config_credentials")).pack(side="left")
        ctk.CTkLabel(header, text=self.lang_manager.get("guide_discord_title"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left", padx=20)

        # Content
        text_area = ctk.CTkTextbox(frame, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), corner_radius=10, border_width=1, border_color=self.theme_manager.get("border"))
        text_area.grid(row=1, column=0, sticky="nsew")
        
        text_area.insert("0.0", self.lang_manager.get("guide_discord_text"))
        text_area.configure(state="disabled") # Read-only
        self._fix_scroll(text_area)

    def create_google_guide_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["google_guide"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header, text=self.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: self.show_frame("config_ai_engine")).pack(side="left")
        ctk.CTkLabel(header, text=self.lang_manager.get("guide_google_title"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left", padx=20)

        # Content
        text_area = ctk.CTkTextbox(frame, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), corner_radius=10, border_width=1, border_color=self.theme_manager.get("border"))
        text_area.grid(row=1, column=0, sticky="nsew")
        
        text_area.insert("0.0", self.lang_manager.get("guide_google_text"))
        text_area.configure(state="disabled")
        self._fix_scroll(text_area)

    def create_id_guide_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["id_guide"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header, text=self.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: self.show_frame("config_general")).pack(side="left")
        ctk.CTkLabel(header, text=self.lang_manager.get("guide_id_title"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left", padx=20)

        # Content
        text_area = ctk.CTkTextbox(frame, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), corner_radius=10, border_width=1, border_color=self.theme_manager.get("border"))
        text_area.grid(row=1, column=0, sticky="nsew")
        
        text_area.insert("0.0", self.lang_manager.get("guide_id_text"))
        text_area.configure(state="disabled")
        self._fix_scroll(text_area)

    def create_privacy_guide_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["privacy_guide"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header, text=self.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: self.show_frame("config_credentials")).pack(side="left")
        ctk.CTkLabel(header, text=self.lang_manager.get("guide_privacy_title"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("red")).pack(side="left", padx=20)

        # Content
        text_area = ctk.CTkTextbox(frame, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), corner_radius=10, border_width=1, border_color=self.theme_manager.get("border"), wrap="word")
        text_area.grid(row=1, column=0, sticky="nsew")
        
        text_area.insert("0.0", self.lang_manager.get("guide_privacy_text"))
        text_area.configure(state="disabled")
        self._fix_scroll(text_area)

    def create_local_guide_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["local_guide"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header, text=self.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.theme_manager.get("border"), text_color=self.theme_manager.get("text"), command=lambda: self.show_frame("config_ai_engine")).pack(side="left")
        ctk.CTkLabel(header, text=self.lang_manager.get("guide_local_title"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.theme_manager.get("accent")).pack(side="left", padx=20)

        # Content
        text_area = ctk.CTkTextbox(frame, font=("Consolas", 13), fg_color=self.theme_manager.get("bg_card"), text_color=self.theme_manager.get("text"), corner_radius=10, border_width=1, border_color=self.theme_manager.get("border"), wrap="word")
        text_area.grid(row=1, column=0, sticky="nsew")
        
        text_area.insert("0.0", self.lang_manager.get("guide_local_text"))
        text_area.configure(state="disabled")
        self._fix_scroll(text_area)

    def toggle_password(self, entry, btn):
        if entry.cget("show") == "*":
            entry.configure(show="")
            btn.configure(text_color=self.theme_manager.get("accent"))
        else:
            entry.configure(show="*")
            btn.configure(text_color=self.theme_manager.get("text_dim"))

    def toggle_help(self, widget, layout="pack", **kwargs):
        if widget.winfo_viewable():
            if layout == "grid": widget.grid_remove()
            else: widget.pack_forget()
        else:
            if layout == "grid": widget.grid(**kwargs)
            else: widget.pack(**kwargs)

    # --- LÓGICA DEL BOT ---
    def start_bot(self):
        if self.bot_process: return

        # UI Updates
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_label.configure(text=self.lang_manager.get("dash_status_starting"), text_color=self.theme_manager.get("accent"))
        self.progress_bar.pack(side="left", padx=(15, 0))
        self.progress_bar.set(0)
        
        # Limpiar consolas (Lazy Loading Safe)
        consoles_to_clean = []
        if hasattr(self, "console_main"): consoles_to_clean.append(self.console_main)
        if hasattr(self, "console_music"): consoles_to_clean.append(self.console_music)
        if hasattr(self, "console_errors"): consoles_to_clean.append(self.console_errors)
        if hasattr(self, "console_ai"): consoles_to_clean.append(self.console_ai)
        
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
        if self.bot_process:
            self.log_to_console(self.lang_manager.get("msg_sending_stop"), "main")
            self.send_to_bot("CMD_STOP")
            # El hilo de lectura detectará el cierre

    def read_output(self):
        """Lee la salida del bot, filtra y distribuye a las consolas."""
        # Prefijos de ruido que NO deben ir a la Terminal limpia
        NOISE_PREFIXES = (
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",  # logging estándar
            "asyncio", "discord.", "websocket", "heartbeat",   # internals de discord.py
            "2025", "2026",  # timestamps del logging (formato: YYYY-MM-DD HH:MM:SS)
        )
        while self.bot_process and self.bot_process.stdout:
            try:
                line = self.bot_process.stdout.readline()
                if not line: break
                
                # ═══ REGISTRO COMPLETO: recibe absolutamente todo, sin filtro ═══
                self.after(0, lambda l=line: self._write_to_widget(self.console_errors, l))

                # 0. Interceptar Progreso de Inicio (IPC interno, no va a ninguna terminal visible)
                if "IPC_PROGRESS:" in line:
                    try:
                        parts = line.split("IPC_PROGRESS:", 1)[1].strip().split(":", 1)
                        if len(parts) == 2:
                            pct = float(parts[0])
                            msg = parts[1]
                            self.after(0, lambda p=pct, m=msg: self._update_progress(p, m))
                    except: pass
                    continue  # No mostrar en ninguna consola visual

                # 1. Interceptar actualizaciones de Cola IPC
                if "IPC_QUEUE_UPDATE:" in line:
                    try:
                        json_str = line.split("IPC_QUEUE_UPDATE:", 1)[1].strip()
                        data = json.loads(json_str)
                        self.after(0, lambda d=data: self.update_queue_ui(d))
                    except: pass
                    continue  # No mostrar en consola

                # Capturar canción actual para actualizar UI (Dinámico para cualquier idioma)
                playing_prefix = self.lang_manager.get("sys_mus_playing_log").replace("{title}", "").strip()
                if playing_prefix in line:
                    title = line.split(playing_prefix, 1)[1].strip()
                    self.after(0, lambda t=title: self.lbl_now_playing.configure(text=f"{self.lang_manager.get('mus_lbl_now_playing_prefix')}{t}") if hasattr(self, "lbl_now_playing") else None)

                # ═══ TERMINAL LIMPIA: solo líneas del propio bot (con emojis) o salidas print limpias ═══
                # Regla: va a Terminal si la línea tiene un emoji propio del bot (🎵 🧠 ⚙️ 📥 📤 ✅ ❌ ⚠️ etc.)
                # o si es una salida print sin prefijos de ruido de logging/asyncio.
                line_stripped = line.strip()
                is_noise = any(line_stripped.startswith(p) for p in NOISE_PREFIXES)
                has_bot_emoji = any(e in line for e in ("🎵", "🧠", "⚙️", "📥", "📤", "✅", "❌", "⚠️", "🔥", "🔄", "💾", "🔑", "🌐", "🎙️", "📝", "✨", "💤", "📉", "🔁", "👁️", "IPC_PROGRESS", "[LAUNCHER]", "[WORKER", "[SISTEMA]", "[SHUTDOWN]", "[IPC]", "ENCENDIDO", "APAGADO", "Sesión iniciada", "Conexión con Discord", "Esperando comandos"))
                
                if not is_noise or has_bot_emoji:
                    self.after(0, lambda l=line: self.log_to_console(l, "main"))

                # Filtros por módulo (consolas específicas)
                if "🎵" in line:
                    self.after(0, lambda l=line: self.log_to_console(l, "music"))
                    
                if "🧠" in line:
                    self.after(0, lambda l=line: self.log_to_console(l, "ai"))

            except: break
        
        # Proceso terminado
        self.bot_process = None
        self.after(0, self._reset_ui_stopped)

    def _update_progress(self, pct, msg):
        self.progress_bar.set(pct)
        self.status_label.configure(text=f"{self.lang_manager.get('dash_status_prefix')} {msg}")
        if pct >= 1.0:
            self.status_label.configure(text=self.lang_manager.get("dash_status_on"), text_color=self.theme_manager.get("green"))
            self.after(1500, self.progress_bar.pack_forget) # Oculta la barra suavemente tras terminar

    def _reset_ui_stopped(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_label.configure(text=self.lang_manager.get("dash_status_off"), text_color=self.theme_manager.get("red"))
        self.progress_bar.pack_forget()
        self.log_to_console(self.lang_manager.get("msg_process_finished"), "main")
        
        # Resetear UI de música
        try: self.lbl_now_playing.configure(text=self.lang_manager.get("mus_lbl_now_playing_empty"))
        except: pass

    def log_to_console(self, text, target):
        if target == "music" and hasattr(self, "console_music"): widget = self.console_music
        elif target == "ai" and hasattr(self, "console_ai"): widget = self.console_ai
        elif target == "main" and hasattr(self, "console_main"): widget = self.console_main
        else: return
        self._write_to_widget(widget, text)

    def _write_to_widget(self, widget, text):
        try:
            widget.configure(state="normal")
            widget.insert("end", text)
            widget.see("end")
            widget.configure(state="disabled")
        except: pass

    def send_to_bot(self, text):
        if self.bot_process and self.bot_process.stdin:
            try:
                self.bot_process.stdin.write(text + "\n")
                self.bot_process.stdin.flush()
            except: pass

    # --- FUNCIONES DE MÚSICA ---
    def send_music_cmd(self, action):
        if not self.bot_process: return
        arg = ""
        if action in ["play", "next"]:
            arg = self.music_entry.get().strip()
            if not arg: return
            self.music_entry.delete(0, "end")
        
        cmd = f"CMD_MUSIC:{action}:{arg}"
        self.send_to_bot(cmd)

    def update_queue_ui(self, queue_list):
        if not hasattr(self, "queue_display"): return
        self.queue_display.configure(state="normal")
        self.queue_display.delete("0.0", "end")
        if not queue_list:
            self.queue_display.insert("end", self.lang_manager.get("mus_queue_empty"))
        else:
            for i, title in enumerate(queue_list, 1):
                self.queue_display.insert("end", f"{i}. {title}\n")
        self.queue_display.configure(state="disabled")

    # --- GESTIÓN DE MÓDULOS ---
    def update_module_state(self, module_name, button):
        try:
            data = self._load_json_file("config.json")
            is_active = data.get("modules", {}).get(module_name, False)
            if is_active:
                button.configure(text=self.lang_manager.get("mod_btn_on"), fg_color=self.theme_manager.get("accent"), text_color=self.theme_manager.get("bg_dark"))
            else:
                button.configure(text=self.lang_manager.get("mod_btn_off"), fg_color=self.theme_manager.get("bg_dark"), text_color=self.theme_manager.get("red"))
        except: pass

    def toggle_module(self, module_name, button):
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
                self.send_to_bot("CMD_RELOAD")
        except Exception as e:
            print(self.lang_manager.get("msg_err_toggle").format(e=e))

    def on_closing(self):
        if self.bot_process:
            self.stop_bot()
            try:
                self.bot_process.kill() # Ejecución Forzosa: Mata al proceso zombie al instante
            except: pass
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