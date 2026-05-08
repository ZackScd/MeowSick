import customtkinter as ctk
import os
import sys
from dotenv import set_key

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
ENV_PATH = os.path.join(SETTINGS_DIR, ".env")

class WizardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        # Contenedor centralizado para la tarjeta
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.card = ctk.CTkFrame(self, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=15, width=650, height=450)
        self.card.grid(row=0, column=0)
        self.card.grid_propagate(False) # Forzar tamaño estricto
        
        self.lbl_title = ctk.CTkLabel(self.card, text=self.controller.lang_manager.get("wizard_title"), font=ctk.CTkFont(size=24, weight="bold"), text_color=self.controller.theme_manager.get("accent"))
        self.lbl_title.pack(pady=(40, 10))
        
        self.lbl_desc = ctk.CTkLabel(self.card, text=self.controller.lang_manager.get("wizard_welcome_msg"), font=ctk.CTkFont(size=13), text_color=self.controller.theme_manager.get("text_dim"), wraplength=550)
        self.lbl_desc.pack(pady=(0, 30))
        
        # Capas de las distintas fases
        self.step1_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.step2_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        
        self.build_step1()
        self.build_step2()
        
        self.step1_frame.pack(fill="both", expand=True, padx=50)
        
        # Botones del Footer
        self.footer = ctk.CTkFrame(self.card, fg_color="transparent")
        self.footer.pack(fill="x", side="bottom", pady=40, padx=50)
        
        self.btn_back = ctk.CTkButton(self.footer, text=self.controller.lang_manager.get("wizard_btn_back"), width=120, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("border"), command=self.show_step1)
        
        self.btn_next = ctk.CTkButton(self.footer, text=self.controller.lang_manager.get("wizard_btn_next"), width=120, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), font=ctk.CTkFont(weight="bold"), command=self.show_step2)
        self.btn_next.pack(side="right")
        
        self.lbl_error = ctk.CTkLabel(self.footer, text="", text_color=self.controller.theme_manager.get("red"), font=ctk.CTkFont(size=12))
        
    def build_step1(self):
        ctk.CTkLabel(self.step1_frame, text=self.controller.lang_manager.get("wizard_step_1"), font=ctk.CTkFont(size=16, weight="bold"), text_color=self.controller.theme_manager.get("text")).pack(anchor="w", pady=(0, 20))
        
        row_lang = ctk.CTkFrame(self.step1_frame, fg_color="transparent")
        row_lang.pack(fill="x", pady=10)
        ctk.CTkLabel(row_lang, text=self.controller.lang_manager.get("wizard_language"), width=150, anchor="w").pack(side="left")
        self.combo_lang = ctk.CTkComboBox(row_lang, values=["es", "en"], fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"))
        self.combo_lang.pack(side="left", fill="x", expand=True)
        self.combo_lang.set(self.controller.lang_code)
        
        row_theme = ctk.CTkFrame(self.step1_frame, fg_color="transparent")
        row_theme.pack(fill="x", pady=10)
        ctk.CTkLabel(row_theme, text=self.controller.lang_manager.get("wizard_theme"), width=150, anchor="w").pack(side="left")
        
        theme_dir = os.path.join(BASE_DIR, "themes")
        available_themes = [f.replace('.json', '') for f in os.listdir(theme_dir) if f.endswith('.json')]
        if "dark" not in available_themes: available_themes.insert(0, "dark")
        
        self.combo_theme = ctk.CTkComboBox(row_theme, values=available_themes, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"))
        self.combo_theme.pack(side="left", fill="x", expand=True)
        
        default_theme = self.controller._load_json_file("config.json").get("theme", "dark")
        self.combo_theme.set(default_theme if default_theme in available_themes else "dark")
        
    def build_step2(self):
        ctk.CTkLabel(self.step2_frame, text=self.controller.lang_manager.get("wizard_step_2"), font=ctk.CTkFont(size=16, weight="bold"), text_color=self.controller.theme_manager.get("text")).pack(anchor="w", pady=(0, 20))
        
        row_token = ctk.CTkFrame(self.step2_frame, fg_color="transparent")
        row_token.pack(fill="x", pady=10)
        ctk.CTkLabel(row_token, text=self.controller.lang_manager.get("wizard_token"), width=150, anchor="w").pack(side="left")
        self.entry_token = ctk.CTkEntry(row_token, show="*", fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"))
        self.entry_token.pack(side="left", fill="x", expand=True)
        
        row_admin = ctk.CTkFrame(self.step2_frame, fg_color="transparent")
        row_admin.pack(fill="x", pady=10)
        ctk.CTkLabel(row_admin, text=self.controller.lang_manager.get("wizard_admin"), width=150, anchor="w").pack(side="left")
        self.entry_admin = ctk.CTkEntry(row_admin, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), placeholder_text="Opcional")
        self.entry_admin.pack(side="left", fill="x", expand=True)
        
    def show_step1(self):
        self.step2_frame.pack_forget()
        self.btn_back.pack_forget()
        self.lbl_error.pack_forget()
        self.step1_frame.pack(fill="both", expand=True, padx=50)
        self.btn_next.configure(text=self.controller.lang_manager.get("wizard_btn_next"), command=self.show_step2)
        
    def show_step2(self):
        self.step1_frame.pack_forget()
        self.lbl_error.pack_forget()
        self.step2_frame.pack(fill="both", expand=True, padx=50)
        self.btn_back.pack(side="left")
        self.btn_next.configure(text=self.controller.lang_manager.get("wizard_finish"), command=self.finish)
        
    def finish(self):
        token = self.entry_token.get().strip()
        if not token:
            self.lbl_error.configure(text=self.controller.lang_manager.get("wizard_err_token"))
            self.lbl_error.pack(side="left", padx=15)
            return
            
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        if not os.path.exists(ENV_PATH):
            with open(ENV_PATH, 'w') as f: pass
            
        set_key(ENV_PATH, "DISCORD_TOKEN", token)
        admin_id = self.entry_admin.get().strip()
        if admin_id: set_key(ENV_PATH, "ADMIN_ID", admin_id)
            
        cfg = self.controller._load_json_file("config.json") or {}
        cfg["language"] = self.combo_lang.get()
        cfg["theme"] = self.combo_theme.get()
        self.controller._save_json_file("config.json", cfg)
        
        self.controller.finish_wizard()