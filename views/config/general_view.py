import customtkinter as ctk
import os
import sys
from dotenv import set_key, dotenv_values

from views.guides.discord_guide_view import DiscordGuideView
from views.guides.id_guide_view import IdGuideView

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
ENV_PATH = os.path.join(SETTINGS_DIR, ".env")

class GeneralConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text=self.controller.lang_manager.get("cfg_gen_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=16, border_width=1, border_color=self.controller.theme_manager.get("border"))
        card.pack(fill="x", padx=20, pady=10)

        # Cargar datos actuales
        config_data = self.controller._load_json_file("config.json")
        outputs_filename = f"locales/outputs_{self.controller.lang_code}.json"
        outputs_data = self.controller._load_json_file(outputs_filename) or {}
        env_data = dotenv_values(ENV_PATH)

        self.general_entries = {}

        def add_gen_row(label, key, source, help_txt, is_password=False):
            # Wrapper: Mantiene la fila y su ayuda juntas
            wrapper = ctk.CTkFrame(card, fg_color="transparent")
            wrapper.pack(fill="x", pady=0)

            row = ctk.CTkFrame(wrapper, fg_color="transparent")
            row.pack(fill="x", pady=8, padx=15)
            ctk.CTkLabel(row, text=label, width=150, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
            
            entry = ctk.CTkEntry(row, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), show="*" if is_password else "")
            entry.pack(side="left", fill="x", expand=True, padx=(10, 10))
            
            # Valor inicial según origen
            val = ""
            if source == "config": val = config_data.get(key, "")
            elif source == "outputs": val = outputs_data.get(key, "")
            elif source == "env": val = env_data.get(key, "")
            
            entry.insert(0, str(val))
            self.general_entries[key] = (entry, source)
            
            # Contenedor de ayuda (se oculta/muestra)
            if help_txt:
                help_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
                
                ctk.CTkLabel(help_frame, text=f"ℹ {help_txt}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
                
                # Enlace a guía de IDs si corresponde
                if key in ["ADMIN_ID", "WELCOME_CHANNEL_ID", "DISCORD_TOKEN"]:
                    guide_target = DiscordGuideView if key == "DISCORD_TOKEN" else IdGuideView
                    link_btn = ctk.CTkButton(help_frame, text=self.controller.lang_manager.get("cfg_gen_link_get_id"), width=90, height=20, fg_color="transparent", text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(size=11, underline=True), hover=False, command=lambda tgt=guide_target: self.controller.show_frame(tgt))
                    link_btn.configure(hover_color=self.controller.theme_manager.get("bg_card"))
                    link_btn.pack(side="left", padx=5)

                ctk.CTkButton(row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x", padx=165)).pack(side="right")

        add_gen_row(self.controller.lang_manager.get("cfg_gen_token"), "DISCORD_TOKEN", "env", self.controller.lang_manager.get("cfg_gen_help_token"), is_password=True)
        add_gen_row(self.controller.lang_manager.get("cfg_gen_prefix"), "prefix", "config", self.controller.lang_manager.get("cfg_gen_help_prefix"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_admin_id"), "ADMIN_ID", "env", self.controller.lang_manager.get("cfg_gen_help_admin"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_welcome_id"), "WELCOME_CHANNEL_ID", "env", self.controller.lang_manager.get("cfg_gen_help_welcome"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_welcome_msg"), "welcome_message", "outputs", self.controller.lang_manager.get("cfg_gen_help_welcome_msg"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_leave_msg"), "disconnected", "outputs", self.controller.lang_manager.get("cfg_gen_help_leave_msg"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_timeout_msg"), "timeout_msg", "outputs", self.controller.lang_manager.get("cfg_gen_help_timeout_msg"))

        ctk.CTkButton(scroll, text=self.controller.lang_manager.get("btn_save"), command=self.save_general_config, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), height=40, corner_radius=10).pack(pady=(20, 5))
        self.lbl_status_general = ctk.CTkLabel(scroll, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_status_general.pack(pady=(0, 20))

    def save_general_config(self):
        # Cargar frescos
        cfg = self.controller._load_json_file("config.json")
        outputs_filename = f"locales/outputs_{self.controller.lang_code}.json"
        out = self.controller._load_json_file(outputs_filename) or {}

        for key, (entry, source) in self.general_entries.items():
            val = entry.get().strip()
            if source == "config": cfg[key] = val
            elif source == "outputs": out[key] = val
            elif source == "env": set_key(ENV_PATH, key, val) # Escribe directo a disco

        self.controller._save_json_file("config.json", cfg)
        self.controller._save_json_file(outputs_filename, out)
        self.lbl_status_general.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
        self.after(3000, lambda: self.lbl_status_general.configure(text=""))