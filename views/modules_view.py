import customtkinter as ctk

class ModulesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text=self.controller.lang_manager.get("mod_title"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.controller.theme_manager.get("text")).grid(row=0, column=0, pady=(20, 10))
        
        container = ctk.CTkFrame(self, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        container.grid(row=1, column=0, sticky="ew", padx=20)
        container.grid_columnconfigure(0, weight=1)

        # Función para crear filas de módulos
        def add_module_row(mod_key, mod_title, help_desc):
            wrapper = ctk.CTkFrame(container, fg_color="transparent")
            wrapper.pack(fill="x", pady=0)
            
            row_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
            row_frame.pack(fill="x", padx=20, pady=15)
            
            ctk.CTkLabel(row_frame, text=mod_title, font=ctk.CTkFont(size=14)).pack(side="left")
            
            help_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
            ctk.CTkLabel(help_frame, text=f"ℹ {help_desc}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), anchor="w", justify="left", wraplength=600).pack(side="left", padx=20)
            
            btn_help = ctk.CTkButton(row_frame, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x", pady=(0, 10)))
            btn_help.pack(side="right", padx=(10, 0))
            
            btn = ctk.CTkButton(row_frame, text="...", width=120, height=30)
            btn.configure(command=lambda m=mod_key, b=btn: self.controller.toggle_module(m, b))
            btn.pack(side="right")
            
            if mod_key not in self.controller.module_buttons: self.controller.module_buttons[mod_key] = []
            self.controller.module_buttons[mod_key].append(btn)
            self.controller.update_module_state(mod_key, btn)

        add_module_row("help", self.controller.lang_manager.get("mod_help_title"), self.controller.lang_manager.get("mod_help_desc"))
        add_module_row("music", self.controller.lang_manager.get("mod_music_title"), self.controller.lang_manager.get("mod_music_desc"))
        add_module_row("ia", self.controller.lang_manager.get("mod_ai_title"), self.controller.lang_manager.get("mod_ai_desc"))