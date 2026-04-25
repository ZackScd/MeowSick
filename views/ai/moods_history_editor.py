import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager
from views.ai.moods_editor import MoodsEditor

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MoodsHistoryEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        ctk.CTkButton(header, text=self.controller.lang_manager.get("btn_back"), width=80, height=30, fg_color="transparent", border_width=1, border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda: self.controller.show_frame(MoodsEditor)).pack(side="left")
        ctk.CTkLabel(header, text=self.controller.lang_manager.get("ai_mh_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left", padx=20)
        
        txt_history = ctk.CTkTextbox(self, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
        txt_history.pack(side="top", fill="both", expand=True)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        def clear_history():
            hist_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "historial_estados.json")
            ConfigManager.save_json(hist_path, [], use_lock=False)
            load_history()
            
        ctk.CTkButton(controls, text=self.controller.lang_manager.get("ai_mh_btn_reload"), command=lambda: load_history(), fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        ctk.CTkButton(controls, text=self.controller.lang_manager.get("ai_mh_btn_clear"), command=clear_history, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("red")).pack(side="right")

        def load_history():
            txt_history.configure(state="normal")
            txt_history.delete("0.0", "end")
            hist_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "historial_estados.json")
            if os.path.exists(hist_path):
                data = ConfigManager.load_json(hist_path, use_lock=False)
                if isinstance(data, list):
                    if data:
                        for entry in reversed(data): # Del más reciente al más antiguo
                            if isinstance(entry, dict):
                                ts = entry.get("timestamp", "").split(".")[0]
                                mood = entry.get("estado_animo", "")
                                txt_history.insert("end", f"[{ts}]\n{mood}\n\n")
                    else:
                        txt_history.insert("end", self.controller.lang_manager.get("ai_mh_msg_empty"))
                else:
                    txt_history.insert("end", self.controller.lang_manager.get("ai_mh_msg_err_fmt"))
            else:
                txt_history.insert("end", self.controller.lang_manager.get("ai_mh_msg_no_hist"))
            txt_history.configure(state="disabled")

        load_history()
        self.controller.ai_reload_functions["config_ai_moods_history"] = load_history