import customtkinter as ctk
import os
import sys
import subprocess
import shutil
from tkinter import messagebox
from dotenv import set_key, dotenv_values

from views.guides.google_guide_view import GoogleGuideView
from views.guides.privacy_guide_view import PrivacyGuideView
from views.guides.local_guide_view import LocalGuideView

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
ENV_PATH = os.path.join(SETTINGS_DIR, ".env")

class AIEngineConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        header_bar = ctk.CTkFrame(self, fg_color="transparent")
        header_bar.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_bar, text=self.controller.lang_manager.get("cfg_eng_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        ctk.CTkButton(header_bar, text=self.controller.lang_manager.get("cfg_eng_btn_privacy"), height=28, fg_color="#331a20", hover_color=self.controller.theme_manager.get("red"), border_color=self.controller.theme_manager.get("red"), border_width=1, text_color=self.controller.theme_manager.get("red"), command=lambda: self.controller.show_frame(PrivacyGuideView)).pack(side="right", padx=20)

        master_frame = ctk.CTkFrame(self, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10, border_width=1, border_color=self.controller.theme_manager.get("border"))
        master_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(master_frame, text=self.controller.lang_manager.get("cfg_eng_active"), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=15, pady=15)
        
        self.ai_engine_var = ctk.StringVar(value="local")
        
        rb_local = ctk.CTkRadioButton(master_frame, text=self.controller.lang_manager.get("cfg_eng_rb_local"), variable=self.ai_engine_var, value="local", text_color=self.controller.theme_manager.get("text"), font=ctk.CTkFont(weight="bold"), fg_color=self.controller.theme_manager.get("accent"), command=self.switch_engine_tabs)
        rb_local.pack(side="left", padx=15)
        
        rb_cloud = ctk.CTkRadioButton(master_frame, text=self.controller.lang_manager.get("cfg_eng_rb_cloud"), variable=self.ai_engine_var, value="nube", text_color=self.controller.theme_manager.get("text"), font=ctk.CTkFont(weight="bold"), fg_color=self.controller.theme_manager.get("accent"), command=self.switch_engine_tabs)
        rb_cloud.pack(side="left", padx=15)
        
        self.tab_local = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.tab_cloud = ctk.CTkScrollableFrame(self, fg_color="transparent")
        
        self.build_local_tab()
        self.build_cloud_tab()
        
        ctk.CTkButton(self, text=self.controller.lang_manager.get("cfg_eng_btn_save"), command=self.save_ai_engine, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), height=40, corner_radius=10).pack(pady=(20, 5))
        self.lbl_status_engine = ctk.CTkLabel(self, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_status_engine.pack(pady=(0, 10))
        
        self.load_ai_engine_ui()

    def switch_engine_tabs(self):
        if self.ai_engine_var.get() == "local":
            self.tab_cloud.pack_forget()
            self.tab_local.pack(fill="both", expand=True)
        else:
            self.tab_local.pack_forget()
            self.tab_cloud.pack(fill="both", expand=True)
            
    def build_local_tab(self):
        card = ctk.CTkFrame(self.tab_local, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=16, border_width=1, border_color=self.controller.theme_manager.get("border"))
        card.pack(fill="x", padx=20, pady=10)
        
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(row1, text=self.controller.lang_manager.get("cfg_eng_local_endp"), width=150, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ollama_endpoint = ctk.CTkEntry(row1, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ollama_endpoint.pack(side="left", fill="x", expand=True, padx=(12, 0))
        
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(row2, text=self.controller.lang_manager.get("cfg_eng_local_mod"), width=150, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ollama_model = ctk.CTkEntry(row2, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ollama_model.pack(side="left", fill="x", expand=True, padx=(12, 0))
        
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(row3, text=self.controller.lang_manager.get("cfg_eng_local_fall"), width=150, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.switch_fallback = ctk.CTkSwitch(row3, text=self.controller.lang_manager.get("cfg_eng_local_fall_sw"), onvalue=True, offvalue=False, progress_color=self.controller.theme_manager.get("accent"))
        self.switch_fallback.pack(side="left", padx=12)

        install_frame = ctk.CTkFrame(self.tab_local, fg_color="transparent")
        install_frame.pack(fill="x", padx=20, pady=10)
        
        def install_local_ai():
            if shutil.which("ollama"):
                model = self.entry_ollama_model.get().strip() or "gemma3"
                try:
                    if sys.platform == "win32":
                        subprocess.Popen(["cmd", "/k", f"ollama pull {model}"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    else:
                        subprocess.Popen(["x-terminal-emulator", "-e", f"ollama pull {model}"])
                except Exception as e: messagebox.showerror(self.controller.lang_manager.get("msg_err_title"), self.controller.lang_manager.get("cfg_eng_err_term").format(e=e))
            else:
                messagebox.showwarning(self.controller.lang_manager.get("cfg_eng_warn_ollama_title"), self.controller.lang_manager.get("cfg_eng_warn_ollama_desc"))
                
        ctk.CTkButton(install_frame, text=self.controller.lang_manager.get("cfg_eng_btn_install"), height=40, font=ctk.CTkFont(weight="bold"), fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("accent"), command=install_local_ai).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(install_frame, text=self.controller.lang_manager.get("cfg_eng_btn_guide"), height=40, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda: self.controller.show_frame(LocalGuideView)).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def build_cloud_tab(self):
        card = ctk.CTkFrame(self.tab_cloud, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=16, border_width=1, border_color=self.controller.theme_manager.get("border"))
        card.pack(fill="x", padx=20, pady=10)

        self.env_entries = {}
        env_vars_config = [("GEMINI_API_KEY", self.controller.lang_manager.get("cfg_eng_key_1")), ("GEMINI_API_KEY_2", self.controller.lang_manager.get("cfg_eng_key_2"))]
        help_texts = {"GEMINI_API_KEY": self.controller.lang_manager.get("cfg_eng_key_1_desc"), "GEMINI_API_KEY_2": self.controller.lang_manager.get("cfg_eng_key_2_desc")}

        for var_key, var_label in env_vars_config:
            wrapper = ctk.CTkFrame(card, fg_color="transparent")
            wrapper.pack(fill="x", pady=0)

            row = ctk.CTkFrame(wrapper, fg_color="transparent")
            row.pack(fill="x", pady=8)

            ctk.CTkLabel(row, text=var_label, width=200, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
            
            help_msg = help_texts.get(var_key, self.controller.lang_manager.get("cfg_eng_no_desc", "Sin descripción."))
            help_lbl = ctk.CTkLabel(wrapper, text=f"ℹ {help_msg}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12, slant="italic"), anchor="w")
            
            ctk.CTkButton(row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_lbl: self.controller.toggle_help(h, "pack", fill="x", padx=(200, 0), pady=(0, 10))).pack(side="right", padx=(10, 0))

            if var_key == "GEMINI_API_KEY":
                ctk.CTkButton(row, text=self.controller.lang_manager.get("cfg_eng_btn_get_key"), width=110, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(size=11), command=lambda: self.controller.show_frame(GoogleGuideView)).pack(side="right", padx=(5, 0))

            entry = ctk.CTkEntry(row, width=350, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), show="*")
            entry.pack(side="left", fill="x", expand=True, padx=(12, 0))
            self.env_entries[var_key] = entry
            
            btn_eye = ctk.CTkButton(entry, text="👁", width=28, height=20, fg_color="transparent", hover_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text_dim"))
            btn_eye.configure(command=lambda e=entry, b=btn_eye: self.controller.toggle_password(e, b))
            btn_eye.place(relx=1.0, x=-8, rely=0.5, anchor="e")

    def load_ai_engine_ui(self):
        cfg = self.controller._load_json_file("config.json").get("ai_config", {})
        env = dotenv_values(ENV_PATH)
        
        self.ai_engine_var.set(cfg.get("ai_engine", "local"))
        self.switch_engine_tabs()
        
        self.entry_ollama_endpoint.delete(0, "end")
        self.entry_ollama_endpoint.insert(0, cfg.get("ollama_endpoint", "http://localhost:11434"))
        self.entry_ollama_model.delete(0, "end")
        self.entry_ollama_model.insert(0, cfg.get("ollama_model", "gemma3"))
        
        if cfg.get("ollama_fallback", False): self.switch_fallback.select()
        else: self.switch_fallback.deselect()
        
        for k, ent in self.env_entries.items():
            ent.delete(0, "end")
            ent.insert(0, env.get(k, ""))

    def save_ai_engine(self):
        try:
            for k, v in self.env_entries.items(): set_key(ENV_PATH, k, v.get().strip())
            cfg = self.controller._load_json_file("config.json")
            if "ai_config" not in cfg: cfg["ai_config"] = {}
            cfg["ai_config"]["ai_engine"] = self.ai_engine_var.get()
            cfg["ai_config"]["ollama_endpoint"] = self.entry_ollama_endpoint.get().strip()
            cfg["ai_config"]["ollama_model"] = self.entry_ollama_model.get().strip()
            cfg["ai_config"]["ollama_fallback"] = bool(self.switch_fallback.get())
            self.controller._save_json_file("config.json", cfg)
            self.controller.send_to_bot('IPC>>{"type": "command", "name": "reload"}')
            self.lbl_status_engine.configure(text=self.controller.lang_manager.get("cfg_eng_msg_saved"), text_color=self.controller.theme_manager.get("green"))
            self.after(3000, lambda: self.lbl_status_engine.configure(text=""))
        except Exception as e:
            self.lbl_status_engine.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))