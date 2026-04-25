import customtkinter as ctk

class AIPresetsConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        ctk.CTkLabel(self, text=self.controller.lang_manager.get("cfg_ai_presets_title", "🎭 Personalidades Prefabricadas"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # 1. Selector de Personalidad
        selector_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        selector_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(selector_frame, text=self.controller.lang_manager.get("cfg_ai_presets_sel", "Seleccionar Personalidad:"), text_color=self.controller.theme_manager.get("text"), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=15)
        self.preset_var = ctk.StringVar(value="Por Defecto (Asistente Neutral)")
        self.combo_preset = ctk.CTkComboBox(selector_frame, variable=self.preset_var, values=["Por Defecto (Asistente Neutral)"], width=300, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.combo_preset.pack(side="left", padx=10, pady=15)

        # 2. Panel Informativo
        info_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(info_frame, text=self.controller.lang_manager.get("cfg_ai_presets_det", "ℹ️ Detalles de la Personalidad:"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.info_text = ctk.CTkTextbox(info_frame, height=80, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), text_color=self.controller.theme_manager.get("text"), border_width=1, border_color=self.controller.theme_manager.get("border"))
        self.info_text.pack(fill="x", padx=15, pady=(0, 15))
        self.info_text.insert("0.0", "Personalidad base del sistema.\nComportamiento neutral, servicial y directo.\nSin gustos predefinidos ni historial emocional.")
        self.info_text.configure(state="disabled")

        # 3. Opciones de Importación
        opts_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        opts_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(opts_frame, text=self.controller.lang_manager.get("cfg_ai_presets_opts", "Opciones de Importación:"), text_color=self.controller.theme_manager.get("text"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.chk_id = ctk.CTkCheckBox(opts_frame, text="Sobrescribir Identidad y Reglas", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("accent"))
        self.chk_id.pack(anchor="w", padx=15, pady=5)
        self.chk_id.select()

        self.chk_moods = ctk.CTkCheckBox(opts_frame, text="Sobrescribir Estados de Ánimo posibles", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("accent"))
        self.chk_moods.pack(anchor="w", padx=15, pady=5)
        self.chk_moods.select()

        self.chk_self = ctk.CTkCheckBox(opts_frame, text="Limpiar Autoconcepto (Gustos y Opiniones)", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("accent"))
        self.chk_self.pack(anchor="w", padx=15, pady=5)
        self.chk_self.select()

        self.chk_users = ctk.CTkCheckBox(opts_frame, text="Borrar memoria de Usuarios y Relaciones", text_color=self.controller.theme_manager.get("text"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20, fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b")
        self.chk_users.pack(anchor="w", padx=15, pady=(5, 15))

        # 4. Warn Box (Advertencia)
        warn_box = ctk.CTkFrame(scroll, fg_color="#331a20", border_color=self.controller.theme_manager.get("red"), border_width=1, corner_radius=8)
        warn_box.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(warn_box, text=self.controller.lang_manager.get("warn_important_title", "⚠️ ADVERTENCIA IMPORTANTE"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("red")).pack(pady=(10, 0))
        ctk.CTkLabel(warn_box, text=self.controller.lang_manager.get("cfg_ai_presets_warn", "Aplicar un preset sobreescribirá los archivos de memoria seleccionados.\nAsegúrate de que el bot esté apagado antes de aplicar."), text_color=self.controller.theme_manager.get("red"), justify="center").pack(pady=(5, 10))

        # 5. Botón de Aplicar
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_frame, text=self.controller.lang_manager.get("cfg_ai_presets_btn_apply", "Aplicar Personalidad"), fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b", text_color=self.controller.theme_manager.get("bg_dark"), font=ctk.CTkFont(weight="bold"), height=40, command=self.apply_preset).pack(side="right")

        self.lbl_status = ctk.CTkLabel(btn_frame, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        self.lbl_status.pack(side="right", padx=15)

    def apply_preset(self):
        # Simularemos el guardado por ahora ya que la lógica real se implementará en la fase de amnesia / reseteo unificado.
        self.lbl_status.configure(text=self.controller.lang_manager.get("cfg_ai_presets_applied", "Preset aplicado (Simulación)"), text_color=self.controller.theme_manager.get("green"))
        self.after(3000, lambda: self.lbl_status.configure(text=""))