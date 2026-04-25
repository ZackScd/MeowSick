import customtkinter as ctk
import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class IdentityEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text=self.controller.lang_manager.get("ai_id_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="top", fill="both", expand=True)
        
        # Contenedor Identity
        id_wrap = ctk.CTkFrame(content, fg_color="transparent")
        id_wrap.pack(side="top", fill="both", expand=True, pady=(0, 10))
        
        id_top = ctk.CTkFrame(id_wrap, fg_color="transparent")
        id_top.pack(fill="x")
        
        id_lbl_row = ctk.CTkFrame(id_top, fg_color="transparent")
        id_lbl_row.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(id_lbl_row, text=self.controller.lang_manager.get("ai_id_lbl_identity"), text_color=self.controller.theme_manager.get("text"), anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        id_help = ctk.CTkFrame(id_top, fg_color="transparent")
        ctk.CTkLabel(id_help, text=self.controller.lang_manager.get("ai_id_help_identity"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left")
        ctk.CTkButton(id_lbl_row, text="?", width=24, height=24, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=id_help: self.controller.toggle_help(h, "pack", fill="x", pady=(0, 5))).pack(side="left", padx=10)
        
        self.txt_identity = ctk.CTkTextbox(id_wrap, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"), border_width=1, border_color=self.controller.theme_manager.get("border"))
        self.txt_identity.pack(fill="both", expand=True)
        
        # Contenedor Guidelines
        gl_wrap = ctk.CTkFrame(content, fg_color="transparent")
        gl_wrap.pack(side="top", fill="both", expand=True)
        
        gl_top = ctk.CTkFrame(gl_wrap, fg_color="transparent")
        gl_top.pack(fill="x")
        
        gl_lbl_row = ctk.CTkFrame(gl_top, fg_color="transparent")
        gl_lbl_row.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(gl_lbl_row, text=self.controller.lang_manager.get("ai_id_lbl_guidelines"), text_color=self.controller.theme_manager.get("text"), anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        gl_help = ctk.CTkFrame(gl_top, fg_color="transparent")
        ctk.CTkLabel(gl_help, text=self.controller.lang_manager.get("ai_id_help_guidelines"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left")
        ctk.CTkButton(gl_lbl_row, text="?", width=24, height=24, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=gl_help: self.controller.toggle_help(h, "pack", fill="x", pady=(0, 5))).pack(side="left", padx=10)
        
        self.txt_guidelines = ctk.CTkTextbox(gl_wrap, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"), border_width=1, border_color=self.controller.theme_manager.get("border"))
        self.txt_guidelines.pack(fill="both", expand=True)

        self.lbl_status = ctk.CTkLabel(controls, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        self.lbl_status.pack(side="right", padx=10)

        ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_reload"), command=self.load_files, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_save_changes"), command=self.save_files, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        self.load_files()
        self.controller.ai_reload_functions["config_ai_identity"] = self.load_files

    def load_files(self):
        self.txt_identity.delete("0.0", "end")
        self.txt_guidelines.delete("0.0", "end")
        id_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "identity.txt")
        gl_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "guidelines.txt")
        
        if os.path.exists(id_path):
            with open(id_path, "r", encoding="utf-8") as f: self.txt_identity.insert("0.0", f.read())
        if os.path.exists(gl_path):
            with open(gl_path, "r", encoding="utf-8") as f: self.txt_guidelines.insert("0.0", f.read())
        self.lbl_status.configure(text=self.controller.lang_manager.get("msg_files_loaded"), text_color=self.controller.theme_manager.get("text_dim"))

    def save_files(self):
        id_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "identity.txt")
        gl_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "guidelines.txt")
        os.makedirs(os.path.dirname(id_path), exist_ok=True)
        
        with open(id_path, "w", encoding="utf-8") as f: f.write(self.txt_identity.get("0.0", "end").strip())
        with open(gl_path, "w", encoding="utf-8") as f: f.write(self.txt_guidelines.get("0.0", "end").strip())
        
        self.lbl_status.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
        self.after(3000, lambda: self.lbl_status.configure(text=""))