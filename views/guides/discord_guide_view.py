import customtkinter as ctk

class DiscordGuideView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        from views.config.general_view import GeneralConfigFrame
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Botón de volver adaptado al lazy loading
        btn_back = ctk.CTkButton(header, text=self.controller.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda: self.controller.show_frame(GeneralConfigFrame))
        btn_back.pack(side="left")
        
        lbl_title = ctk.CTkLabel(header, text=self.controller.lang_manager.get("guide_discord_title"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.controller.theme_manager.get("accent"))
        lbl_title.pack(side="left", padx=20)

        # Content
        text_area = ctk.CTkTextbox(self, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"), corner_radius=10, border_width=1, border_color=self.controller.theme_manager.get("border"))
        text_area.grid(row=1, column=0, sticky="nsew")
        
        # Inserción de texto centralizado y modo solo lectura
        text_area.insert("0.0", self.controller.lang_manager.get("guide_discord_text"))
        text_area.configure(state="disabled") 
        self.controller._fix_scroll(text_area)