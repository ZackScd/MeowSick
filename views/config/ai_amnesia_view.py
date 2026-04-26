import os
import sys
import customtkinter as ctk
from tkinter import messagebox
from shared.config_manager import ConfigManager

try:
    import build
except ImportError:
    build = None

class AIAmnesiaConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        if getattr(sys, 'frozen', False):
            self.mem_dir = os.path.join(os.path.dirname(sys.executable), "cogs", "AI", "memory")
        else:
            self.mem_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cogs", "AI", "memory")

        # Header
        ctk.CTkLabel(self, text=self.controller.lang_manager.get("nav_ai_amnesia", "🎭 Personalidad y Reseteo"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(0, 15))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ==========================================
        # SECCIÓN 1: PERSONALIDADES PREFABRICADAS
        # ==========================================
        preset_title = ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ai_presets_title", "Personalidades Prefabricadas"), font=ctk.CTkFont(size=16, weight="bold"), text_color=self.controller.theme_manager.get("text"))
        preset_title.pack(anchor="w", padx=20, pady=(10, 5))

        # Selector
        selector_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        selector_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(selector_frame, text=self.controller.lang_manager.get("cfg_ai_presets_sel", "Seleccionar Personalidad:"), text_color=self.controller.theme_manager.get("text"), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=15)
        self.preset_var = ctk.StringVar(value="Por Defecto (Asistente Neutral)")
        self.combo_preset = ctk.CTkComboBox(selector_frame, variable=self.preset_var, values=["Por Defecto (Asistente Neutral)"], width=300, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.combo_preset.pack(side="left", padx=10, pady=15)

        # Panel Informativo
        info_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=self.controller.lang_manager.get("cfg_ai_presets_det", "ℹ️ Detalles de la Personalidad:"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.info_text = ctk.CTkTextbox(info_frame, height=80, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), text_color=self.controller.theme_manager.get("text"), border_width=1, border_color=self.controller.theme_manager.get("border"))
        self.info_text.pack(fill="x", padx=15, pady=(0, 15))
        self.info_text.insert("0.0", "Personalidad base del sistema.\nComportamiento neutral, servicial y directo.\nSin gustos predefinidos ni historial emocional.")
        self.info_text.configure(state="disabled")

        # Opciones de Importación
        opts_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        opts_frame.pack(fill="x", padx=20, pady=5)
        
        self.chk_id = ctk.CTkCheckBox(opts_frame, text="Sobrescribir Identidad y Reglas", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("accent"))
        self.chk_id.pack(anchor="w", padx=15, pady=(15,5))
        self.chk_id.select()

        self.chk_moods = ctk.CTkCheckBox(opts_frame, text="Sobrescribir Estados de Ánimo posibles", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("accent"))
        self.chk_moods.pack(anchor="w", padx=15, pady=5)
        self.chk_moods.select()

        self.chk_self = ctk.CTkCheckBox(opts_frame, text="Limpiar Autoconcepto (Gustos y Opiniones)", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("accent"))
        self.chk_self.pack(anchor="w", padx=15, pady=5)
        self.chk_self.select()

        self.chk_users = ctk.CTkCheckBox(opts_frame, text="Borrar memoria de Usuarios y Relaciones", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b")
        self.chk_users.pack(anchor="w", padx=15, pady=(5, 15))

        # Botón Aplicar Preset
        btn_pre_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_pre_frame.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkButton(btn_pre_frame, text=self.controller.lang_manager.get("cfg_ai_presets_btn_apply", "Aplicar Personalidad"), fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b", text_color=self.controller.theme_manager.get("bg_dark"), font=ctk.CTkFont(weight="bold"), height=40, command=self.apply_preset).pack(side="right")
        
        self.lbl_status = ctk.CTkLabel(btn_pre_frame, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        self.lbl_status.pack(side="right", padx=15)

        # ==========================================
        # SECCIÓN 2: BORRADO MODULAR (AMNESIA)
        # ==========================================
        ctk.CTkFrame(scroll, height=2, fg_color=self.controller.theme_manager.get("border")).pack(fill="x", padx=20, pady=20)
        
        amnesia_title = ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("dlg_amnesia_title", "Restablecer a Fábrica (Borrado Modular)"), font=ctk.CTkFont(size=16, weight="bold"), text_color=self.controller.theme_manager.get("red"))
        amnesia_title.pack(anchor="w", padx=20, pady=(0, 5))

        warn_lbl = ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("dlg_amnesia_desc", "⚠️ Selecciona qué archivos deseas devolver a su estado original. No se puede deshacer."), text_color=self.controller.theme_manager.get("red"))
        warn_lbl.pack(anchor="w", padx=20, pady=(0, 10))

        # Tabs
        self.tabview = ctk.CTkTabview(scroll, fg_color=self.controller.theme_manager.get("bg_card"))
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.tab_mem = self.tabview.add(self.controller.lang_manager.get("tab_reset_mem", "Memoria y Usuarios"))
        self.tab_cfg = self.tabview.add(self.controller.lang_manager.get("tab_reset_cfg", "Personalidad y Reglas"))

        self.chk_vars = {}

        # --- TAB 1: Memoria y Usuarios ---
        self._add_check(self.tab_mem, "users", self.controller.lang_manager.get("dlg_amnesia_opt_users", "Registro de Usuarios Conocidos"))
        self._add_check(self.tab_mem, "opinions", self.controller.lang_manager.get("dlg_amnesia_opt_opi", "Opiniones Sociales y Afinidad"))
        self._add_check(self.tab_mem, "memory", self.controller.lang_manager.get("dlg_amnesia_opt_mem", "Hechos y Recuerdos (Biografías)"))
        
        # Autoconcepto Granular
        self.chk_vars["self_gustos"] = ctk.BooleanVar(value=False)
        self.chk_vars["self_opiniones"] = ctk.BooleanVar(value=False)
        
        auto_frame = ctk.CTkFrame(self.tab_mem, fg_color="transparent")
        auto_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(auto_frame, text=self.controller.lang_manager.get("dlg_amnesia_opt_self", "Autoconcepto y Gustos") + ":", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        ctk.CTkCheckBox(auto_frame, text=self.controller.lang_manager.get("reset_self_likes", "Borrar Gustos"), variable=self.chk_vars["self_gustos"], fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b").pack(anchor="w", padx=20, pady=5)
        ctk.CTkCheckBox(auto_frame, text=self.controller.lang_manager.get("reset_self_ops", "Borrar Opiniones Propias"), variable=self.chk_vars["self_opiniones"], fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b").pack(anchor="w", padx=20, pady=5)

        # --- TAB 2: Personalidad y Reglas ---
        self._add_check(self.tab_cfg, "identity", self.controller.lang_manager.get("dlg_amnesia_opt_id", "Identidad Base y Reglas"))
        self._add_check(self.tab_cfg, "ranges", self.controller.lang_manager.get("nav_ai_affinity_ranges", "Rangos de Afinidad"))
        self._add_check(self.tab_cfg, "moods", self.controller.lang_manager.get("dlg_amnesia_opt_moods", "Estados de Ánimo y Posibles"))
        self._add_check(self.tab_cfg, "prompts", self.controller.lang_manager.get("nav_ai_internal_prompts", "Prompts del Sistema"))

        # Botón Aplicar Borrado Modular
        btn_del_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_del_frame.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkButton(btn_del_frame, text=self.controller.lang_manager.get("dlg_amnesia_btn_del", "¡Borrar Seleccionados!"), fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b", font=ctk.CTkFont(weight="bold"), height=40, command=self.apply_reset).pack(side="right")

    def _add_check(self, parent, key, text):
        var = ctk.BooleanVar(value=False)
        self.chk_vars[key] = var
        ctk.CTkCheckBox(parent, text=text, variable=var, fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b").pack(anchor="w", pady=8)

    def apply_preset(self):
        # Simularemos el guardado por ahora
        self.lbl_status.configure(text=self.controller.lang_manager.get("cfg_ai_presets_applied", "Preset aplicado (Simulación)"), text_color=self.controller.theme_manager.get("green"))
        self.after(3000, lambda: self.lbl_status.configure(text=""))

    def apply_reset(self):
        if not build:
            messagebox.showerror("Error", "El módulo build no está disponible para leer los valores por defecto.")
            return

        try:
            if self.chk_vars["identity"].get():
                with open(os.path.join(self.mem_dir, "identity.txt"), "w", encoding="utf-8") as f: f.write(build.DEFAULT_IDENTITY)
                with open(os.path.join(self.mem_dir, "guidelines.txt"), "w", encoding="utf-8") as f: f.write(build.DEFAULT_GUIDELINES)
            if self.chk_vars["ranges"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "afinidad_rangos.json"), build.DEFAULT_RANGES, use_lock=False)
            if self.chk_vars["prompts"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "prompts.json"), build.DEFAULT_PROMPTS, use_lock=False)
            if self.chk_vars["users"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "known_users.json"), {}, use_lock=False)
            if self.chk_vars["opinions"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "opiniones.json"), {}, use_lock=False)
            if self.chk_vars["memory"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "memoria.json"), {}, use_lock=False)
            if self.chk_vars["moods"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "estado_animo.json"), {"estado_animo": "Neutral: Comportamiento por defecto."}, use_lock=False)
                ConfigManager.save_json(os.path.join(self.mem_dir, "historial_estados.json"), [], use_lock=False)
                ConfigManager.save_json(os.path.join(self.mem_dir, "estados_posibles.json"), build.DEFAULT_MOODS, use_lock=False)
            
            # Granular Autoconcepto
            if self.chk_vars["self_gustos"].get() or self.chk_vars["self_opiniones"].get():
                auto_path = os.path.join(self.mem_dir, "autoconcepto.json")
                curr_auto = ConfigManager.load_json(auto_path, use_lock=False) or {"gustos": [], "opiniones": {}}
                if self.chk_vars["self_gustos"].get(): curr_auto["gustos"] = []
                if self.chk_vars["self_opiniones"].get(): curr_auto["opiniones"] = {}
                ConfigManager.save_json(auto_path, curr_auto, use_lock=False)

            self.controller.reload_all_ai_files()
            messagebox.showinfo(self.controller.lang_manager.get("dlg_amnesia_msg_ok_title", "Éxito"), self.controller.lang_manager.get("dlg_amnesia_msg_ok", "Archivos restablecidos a fábrica correctamente."))
        except Exception as e:
            messagebox.showerror(self.controller.lang_manager.get("dlg_amnesia_msg_err_title", "Error"), self.controller.lang_manager.get("dlg_amnesia_msg_err", "Fallo al restablecer: {e}").format(e=e))