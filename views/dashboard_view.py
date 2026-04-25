import customtkinter as ctk

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header con controles
        header = ctk.CTkFrame(self, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=16, border_width=1, border_color=self.controller.theme_manager.get("border"))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(padx=20, pady=20, fill="x")

        self.controller.btn_start = ctk.CTkButton(controls, text=self.controller.lang_manager.get("dash_btn_start"), command=self.controller.start_bot, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), height=40, corner_radius=10, font=ctk.CTkFont(weight="bold"))
        self.controller.btn_start.pack(side="left", padx=(0, 10))
        
        self.controller.btn_stop = ctk.CTkButton(controls, text=self.controller.lang_manager.get("dash_btn_stop"), command=self.controller.stop_bot, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color="#333333", text_color=self.controller.theme_manager.get("red"), height=40, corner_radius=10, state="disabled")
        self.controller.btn_stop.pack(side="left", padx=(0, 16))
        
        self.controller.status_label = ctk.CTkLabel(controls, text=self.controller.lang_manager.get("dash_status_off"), font=ctk.CTkFont(size=13, weight="bold"), text_color=self.controller.theme_manager.get("text_dim"))
        self.controller.status_label.pack(side="left")
        
        self.controller.progress_bar = ctk.CTkProgressBar(controls, width=150, height=10, progress_color=self.controller.theme_manager.get("accent"), fg_color=self.controller.theme_manager.get("bg_dark"))
        self.controller.progress_bar.set(0)
        # Se oculta inicialmente; se empacará y mostrará dinámicamente al iniciar

        # Consolas del Dashboard
        console_area = ctk.CTkFrame(self, fg_color="transparent")
        console_area.grid(row=1, column=0, sticky="nsew")
        console_area.grid_columnconfigure(0, weight=1)
        console_area.grid_rowconfigure(1, weight=2) # Terminal limpia (arriba, más pequeña)
        console_area.grid_rowconfigure(3, weight=3) # Registro completo (abajo, más grande)

        # Terminal limpia
        ctk.CTkLabel(console_area, text=self.controller.lang_manager.get("dash_term_clean"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=5, pady=(0,2))
        self.controller.console_main = ctk.CTkTextbox(console_area, font=("Consolas", 11), fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"), border_width=1, border_color=self.controller.theme_manager.get("border"), corner_radius=8)
        self.controller.console_main.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.controller.console_main.configure(state="disabled")

        # Registro completo
        ctk.CTkLabel(console_area, text=self.controller.lang_manager.get("dash_term_full"), text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), anchor="w").grid(row=2, column=0, sticky="ew", padx=5, pady=(0,2))
        self.controller.console_errors = ctk.CTkTextbox(console_area, font=("Consolas", 10), fg_color="#090909", text_color=self.controller.theme_manager.get("green"), border_width=1, border_color=self.controller.theme_manager.get("border"), corner_radius=8)
        self.controller.console_errors.grid(row=3, column=0, sticky="nsew")
        self.controller.console_errors.configure(state="disabled")