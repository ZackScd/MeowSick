import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PromptsEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_prompts_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")

        # Caja de advertencia de edición
        warn_box = ctk.CTkFrame(self, fg_color="#331a20", border_color=self.controller.theme_manager.get("red"), border_width=1, corner_radius=8)
        warn_box.pack(side="top", fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(warn_box, text=self.controller.lang_manager.get("warn_important_title"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("red")).pack(pady=(10, 0))
        ctk.CTkLabel(warn_box, text=self.controller.lang_manager.get("ai_prompts_warn_desc"), text_color=self.controller.theme_manager.get("red"), justify="center").pack(pady=(5, 10))

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))

        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))
        scroll.pack(side="top", fill="both", expand=True)

        prompts_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "prompts.json")
        self.prompt_entries = {}

        prompt_defs = [
            ("evolucion_analisis", self.controller.lang_manager.get("ai_prompts_evo_title"), self.controller.lang_manager.get("ai_prompts_evo_desc")),
            ("memoria_opiniones", self.controller.lang_manager.get("ai_prompts_soc_title"), self.controller.lang_manager.get("ai_prompts_soc_desc")),
            ("memoria_autoconcepto", self.controller.lang_manager.get("ai_prompts_self_title"), self.controller.lang_manager.get("ai_prompts_self_desc")),
            ("memoria_filtrado", self.controller.lang_manager.get("ai_prompts_facts_title"), self.controller.lang_manager.get("ai_prompts_facts_desc"))
        ]

        for key, title, desc in prompt_defs:
            card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.controller.theme_manager.get("border"))
            card.pack(fill="x", padx=20, pady=8)
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(top, text=title, font=ctk.CTkFont(weight="bold", size=14), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
            ctk.CTkLabel(top, text=f"({key})", font=ctk.CTkFont(size=12), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left", padx=10)
            ctk.CTkLabel(top, text=desc, font=ctk.CTkFont(size=12), text_color=self.controller.theme_manager.get("text_dim")).pack(side="right")
            
            txt_box = ctk.CTkTextbox(card, height=120, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
            txt_box.pack(fill="x", padx=15, pady=(0, 15))
            self.controller._fix_scroll(txt_box)
            
            def resize_desc(event=None, t=txt_box):
                try:
                    dl = t._textbox.count("1.0", "end", "displaylines")
                    lines = dl[0] if dl else 1
                    t.configure(height=max(80, lines * 18))
                except: pass
            txt_box.bind("<KeyRelease>", resize_desc)
            
            self.prompt_entries[key] = {"txt": txt_box, "resize": resize_desc}

        def load_prompts():
            data = ConfigManager.load_json(prompts_path, use_lock=False)
            if isinstance(data, dict):
                for key, entry in self.prompt_entries.items():
                    entry["txt"].delete("0.0", "end")
                    entry["txt"].insert("0.0", data.get(key, ""))
                    self.after(50, entry["resize"])

        def save_prompts():
            data = {}
            for key, entry in self.prompt_entries.items():
                data[key] = entry["txt"].get("0.0", "end").strip()
            try:
                ConfigManager.save_json(prompts_path, data, use_lock=False)
                lbl_status.configure(text=self.controller.lang_manager.get("ai_prompts_msg_saved"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e:
                lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_reload"), command=load_prompts, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.controller.lang_manager.get("ai_prompts_btn_save"), command=save_prompts, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        load_prompts()
        self.controller.ai_reload_functions["config_ai_prompts"] = load_prompts