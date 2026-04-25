import customtkinter as ctk

class AIGeneralConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # 1. Header y Toggle Principal
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text=self.controller.lang_manager.get("cfg_ai_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        self.controller.btn_ai_toggle = ctk.CTkButton(header, text="...", width=120, height=30, command=lambda: self.controller.toggle_module("ia", self.controller.btn_ai_toggle))
        self.controller.btn_ai_toggle.pack(side="right")
        
        btn_ai_config = ctk.CTkButton(header, text="⚙", width=30, height=30, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=self.controller.open_config_ai_menu)
        btn_ai_config.pack(side="right", padx=(0, 10))
        
        if "ia" not in self.controller.module_buttons: self.controller.module_buttons["ia"] = []
        self.controller.module_buttons["ia"].append(self.controller.btn_ai_toggle)
        self.controller.update_module_state("ia", self.controller.btn_ai_toggle)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))
        scroll.pack(side="top", fill="both", expand=True)

        # 2. Consola de IA (Dentro del scroll, alineado con las tarjetas)
        console_area = ctk.CTkFrame(scroll, fg_color="transparent")
        console_area.pack(side="top", fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(console_area, text=self.controller.lang_manager.get("cfg_ai_term_title"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(family="Consolas", size=11), anchor="w").pack(fill="x", padx=5)
        self.controller.console_ai = ctk.CTkTextbox(console_area, font=("Consolas", 10), height=150, fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("accent"), border_width=1, border_color=self.controller.theme_manager.get("border"), corner_radius=8)
        self.controller.console_ai.pack(fill="x", pady=(0, 5))
        self.controller.console_ai.configure(state="disabled")

        # Sección 1: Subprocesos (Switches)
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ai_sub_title"), font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        proc_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        proc_card.pack(fill="x", padx=20, pady=5)

        self.ai_switches = {}
        
        def add_switch(key, title, desc):
            row = ctk.CTkFrame(proc_card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=10)
            
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both")
            ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=desc, font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim"), anchor="w").pack(anchor="w")
            
            switch = ctk.CTkSwitch(row, text="", onvalue=True, offvalue=False, progress_color=self.controller.theme_manager.get("accent"), command=self.save_ai_switches_instant)
            switch.pack(side="right")
            self.ai_switches[key] = switch

        add_switch("enable_chat", self.controller.lang_manager.get("cfg_ai_sw_chat"), self.controller.lang_manager.get("cfg_ai_sw_chat_desc"))
        add_switch("enable_mood_analysis", self.controller.lang_manager.get("cfg_ai_sw_mood"), self.controller.lang_manager.get("cfg_ai_sw_mood_desc"))
        add_switch("enable_memory_learning", self.controller.lang_manager.get("cfg_ai_sw_mem"), self.controller.lang_manager.get("cfg_ai_sw_mem_desc"))
        add_switch("listen_to_bots", self.controller.lang_manager.get("cfg_ai_sw_bots"), self.controller.lang_manager.get("cfg_ai_sw_bots_desc"))
        add_switch("enable_vision", self.controller.lang_manager.get("cfg_ai_sw_vision"), self.controller.lang_manager.get("cfg_ai_sw_vision_desc"))
        add_switch("enable_tts", self.controller.lang_manager.get("cfg_ai_sw_tts"), self.controller.lang_manager.get("cfg_ai_sw_tts_desc"))
        add_switch("enable_stt", self.controller.lang_manager.get("cfg_ai_sw_stt"), self.controller.lang_manager.get("cfg_ai_sw_stt_desc"))
        add_switch("enable_web_search", self.controller.lang_manager.get("cfg_ai_sw_web"), self.controller.lang_manager.get("cfg_ai_sw_web_desc"))
        add_switch("gamer_mode", self.controller.lang_manager.get("cfg_ai_sw_gamer"), self.controller.lang_manager.get("cfg_ai_sw_gamer_desc"))
        add_switch("enable_safety_filters", self.controller.lang_manager.get("cfg_ai_sw_safety"), self.controller.lang_manager.get("cfg_ai_sw_safety_desc"))

        self.load_ai_switches()

    def load_ai_switches(self):
        cfg = self.controller._load_json_file("config.json")
        ai_cfg = cfg.get("ai_config", {})
        
        for key, switch in self.ai_switches.items():
            val = ai_cfg.get(key, False)
            if key == "enable_chat" and key not in ai_cfg: val = True # Default True
            if val: switch.select()
            else: switch.deselect()

    def save_ai_switches_instant(self):
        cfg = self.controller._load_json_file("config.json")
        if "ai_config" not in cfg: cfg["ai_config"] = {}
        for key, switch in self.ai_switches.items():
            cfg["ai_config"][key] = bool(switch.get())
        self.controller._save_json_file("config.json", cfg)
        if self.controller.bot_process:
            self.controller.send_to_bot("CMD_RELOAD")