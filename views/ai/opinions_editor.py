import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class OpinionsEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_opi_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.controller.lang_manager.get("ai_opi_desc"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        # Controls Bottom
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        opinions_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "opiniones.json")
        users_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "known_users.json")

        scroll_users = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))
        scroll_users.pack(fill="both", expand=True)

        self.opiniones_entries_data = []

        def delete_single_opinion(uid):
            try:
                op_data = ConfigManager.load_json(opinions_path, use_lock=False)
                if isinstance(op_data, dict) and uid in op_data:
                    del op_data[uid]
                    ConfigManager.save_json(opinions_path, op_data, use_lock=False)
                    load_opinions()
                    lbl_status.configure(text=self.controller.lang_manager.get("ai_opi_msg_del"), text_color=self.controller.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        def load_opinions():
            for w in scroll_users.winfo_children(): w.destroy()
            self.opiniones_entries_data.clear()
            
            op_data = ConfigManager.load_json(opinions_path, use_lock=False)
            if not isinstance(op_data, dict): op_data = {}
            users_data = ConfigManager.load_json(users_path, use_lock=False)
            if not isinstance(users_data, dict): users_data = {}
                
            all_uids = list(users_data.keys())
            for uid in op_data.keys():
                if uid not in all_uids: all_uids.append(uid)
                
            if not all_uids:
                ctk.CTkLabel(scroll_users, text=self.controller.lang_manager.get("ai_opi_msg_empty"), text_color=self.controller.theme_manager.get("text_dim")).pack(pady=20)
            else:
                for uid in all_uids:
                    uname = users_data.get(uid, {}).get("nombre", self.controller.lang_manager.get("msg_unknown"))
                    user_op = op_data.get(uid, {})
                    
                    card = ctk.CTkFrame(scroll_users, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.controller.theme_manager.get("border"))
                    card.pack(fill="x", pady=6, padx=5)
                    
                    top = ctk.CTkFrame(card, fg_color="transparent")
                    top.pack(fill="x", padx=15, pady=(10, 5))
                    ctk.CTkLabel(top, text=f"{uid} : {uname}", font=ctk.CTkFont(weight="bold", size=14), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
                    
                    ctk.CTkLabel(top, text=self.controller.lang_manager.get("ai_opi_lbl_aff"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left", padx=(20, 5))
                    ent_aff = ctk.CTkEntry(top, width=50, height=28, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"))
                    ent_aff.pack(side="left")
                    ent_aff.insert(0, str(user_op.get("afinidad", 0)))
                    
                    ctk.CTkLabel(top, text=self.controller.lang_manager.get("ai_opi_lbl_rel"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left", padx=(20, 5))
                    ent_rel = ctk.CTkEntry(top, width=150, height=28, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"))
                    ent_rel.pack(side="left")
                    ent_rel.insert(0, user_op.get("relacion", self.controller.lang_manager.get("ai_opi_def_rel")))
                    
                    mid = ctk.CTkFrame(card, fg_color="transparent")
                    mid.pack(fill="x", padx=15, pady=5)
                    txt_op = ctk.CTkTextbox(mid, height=65, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
                    txt_op.pack(fill="x", expand=True)
                    txt_op.insert("0.0", user_op.get("opinion", ""))
                    self.controller._fix_scroll(txt_op)
                    
                    def resize_desc(event=None, t=txt_op):
                        try:
                            w = t.winfo_width()
                            if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                            else:
                                dl = t._textbox.count("1.0", "end", "displaylines")
                                lines = dl[0] if dl else 1
                            t.configure(height=max(65, lines * 18))
                        except: pass
                    txt_op.bind("<KeyRelease>", resize_desc)
                    self.after(50, resize_desc)
                    
                    bot = ctk.CTkFrame(card, fg_color="transparent")
                    bot.pack(fill="x", padx=15, pady=(0, 10))
                    
                    btn_del = ctk.CTkButton(bot, text=self.controller.lang_manager.get("ai_mem_btn_del"), width=80, height=26, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("red"), command=lambda u=uid: delete_single_opinion(u))
                    btn_del.pack(side="right", padx=(5, 5))

                    self.opiniones_entries_data.append({
                        "uid": uid, "aff": ent_aff, "rel": ent_rel, "op": txt_op
                    })

            lbl_status.configure(text=self.controller.lang_manager.get("ai_opi_msg_loaded"), text_color=self.controller.theme_manager.get("text_dim"))

        def save_all_opinions():
            try:
                op_data = ConfigManager.load_json(opinions_path, use_lock=False)
                if not isinstance(op_data, dict): op_data = {}
                
                for entry in self.opiniones_entries_data:
                    uid = entry["uid"]
                    try: aff_int = int(entry["aff"].get().strip())
                    except ValueError: aff_int = 0
                    
                    rel = entry["rel"].get().strip()
                    op = entry["op"].get("0.0", "end").strip()
                    
                    if aff_int != 0 or rel != self.controller.lang_manager.get("ai_opi_def_rel") or op != "" or uid in op_data:
                        op_data[uid] = {"afinidad": aff_int, "relacion": rel, "opinion": op}

                ConfigManager.save_json(opinions_path, op_data, use_lock=False)
                lbl_status.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: 
                lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        btn_container = ctk.CTkFrame(controls, fg_color="transparent")
        btn_container.pack(side="left")
        
        ctk.CTkButton(btn_container, text=self.controller.lang_manager.get("btn_reload"), command=load_opinions, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(btn_container, text=self.controller.lang_manager.get("btn_save_changes"), command=save_all_opinions, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        load_opinions()
        self.controller.ai_reload_functions["config_ai_opinions"] = load_opinions