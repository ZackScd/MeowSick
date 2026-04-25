import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MemoryEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_mem_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.controller.lang_manager.get("ai_mem_desc"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))
        scroll.pack(side="top", fill="both", expand=True)

        mem_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "memoria.json")
        users_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "known_users.json")

        self.memory_entries = {}

        def toggle_facts(container, btn):
            if container.winfo_viewable():
                container.pack_forget()
                btn.configure(text=self.controller.lang_manager.get("ai_mem_btn_expand"))
            else:
                container.pack(fill="x", pady=(0, 5))
                btn.configure(text=self.controller.lang_manager.get("ai_mem_btn_collapse"))
                def refresh():
                    for row in container.winfo_children():
                        for widget in row.winfo_children():
                            if isinstance(widget, ctk.CTkTextbox):
                                widget.event_generate("<KeyRelease>")
                container.after(50, refresh)

        def build_fact_row(container, uid, fact_text):
            row = ctk.CTkFrame(container, fg_color=self.controller.theme_manager.get("bg_dark"), corner_radius=4)
            row.pack(fill="x", padx=15, pady=2)
            
            txt_fact = ctk.CTkTextbox(row, height=24, font=("Consolas", 12), fg_color="transparent", text_color=self.controller.theme_manager.get("text"), wrap="word")
            txt_fact.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            txt_fact.insert("0.0", fact_text)
            self.controller._fix_scroll(txt_fact)
            
            def resize_desc(event=None):
                try:
                    w = txt_fact.winfo_width()
                    if w < 50:
                        lines = max(1, len(txt_fact.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = txt_fact._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    txt_fact.configure(height=max(24, lines * 18))
                except: pass
            txt_fact.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc)
            
            entry_data = {"row": row, "txt": txt_fact}
            self.memory_entries[uid].append(entry_data)

            def delete_fact():
                row.destroy()
                if entry_data in self.memory_entries[uid]:
                    self.memory_entries[uid].remove(entry_data)
            
            btn_del = ctk.CTkButton(row, text=self.controller.lang_manager.get("ai_mem_btn_del"), width=80, height=26, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("red"), command=delete_fact)
            btn_del.pack(side="right", padx=(5, 5), pady=5)

        def add_new_fact_ui(uid, container):
            if uid not in self.memory_entries:
                self.memory_entries[uid] = []
            build_fact_row(container, uid, self.controller.lang_manager.get("ai_mem_new_fact"))

        def load_memory(expand_uid=None):
            for w in scroll.winfo_children(): w.destroy()
            self.memory_entries.clear()
            
            mem_data = ConfigManager.load_json(mem_path, use_lock=False)
            if not isinstance(mem_data, dict): mem_data = {}
            users_data = ConfigManager.load_json(users_path, use_lock=False)
            if not isinstance(users_data, dict): users_data = {}
            
            all_uids = list(users_data.keys())
            for uid in mem_data.keys():
                if uid not in all_uids:
                    all_uids.append(uid)

            if not all_uids:
                ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("ai_mem_msg_empty"), text_color=self.controller.theme_manager.get("text_dim")).pack(pady=20)
                lbl_status.configure(text=self.controller.lang_manager.get("ai_mem_msg_list_empty"), text_color=self.controller.theme_manager.get("text_dim"))
                return

            for uid in all_uids:
                uname = users_data.get(uid, {}).get("nombre", self.controller.lang_manager.get("msg_unknown"))
                facts = mem_data.get(uid, [])
                self.memory_entries[uid] = []
                
                user_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=8)
                user_card.pack(fill="x", pady=5)
                
                header_row = ctk.CTkFrame(user_card, fg_color="transparent")
                header_row.pack(fill="x", padx=15, pady=8)
                
                ctk.CTkLabel(header_row, text=f"{uid} : {uname}", font=ctk.CTkFont(weight="bold", size=14), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
                
                btn_toggle = ctk.CTkButton(header_row, text=self.controller.lang_manager.get("ai_mem_btn_expand"), width=100, height=28, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
                btn_toggle.pack(side="right")
                
                facts_container = ctk.CTkFrame(user_card, fg_color="transparent")
                
                if expand_uid == uid:
                    facts_container.pack(fill="x", pady=(0, 5))
                    btn_toggle.configure(text=self.controller.lang_manager.get("ai_mem_btn_collapse"))
                    
                btn_toggle.configure(command=lambda c=facts_container, b=btn_toggle: toggle_facts(c, b))
                
                # Lista interna para separar los hechos del botón de añadir
                facts_list_container = ctk.CTkFrame(facts_container, fg_color="transparent")
                facts_list_container.pack(fill="x")
                
                for fact in facts:
                    build_fact_row(facts_list_container, uid, fact)
                    
                add_row = ctk.CTkFrame(facts_container, fg_color="transparent")
                add_row.pack(fill="x", pady=(2, 6), padx=15)
                ctk.CTkButton(add_row, text=self.controller.lang_manager.get("ai_mem_btn_add"), height=26, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda u=uid, c=facts_list_container: add_new_fact_ui(u, c)).pack(side="right")

            lbl_status.configure(text=self.controller.lang_manager.get("ai_mem_msg_loaded"), text_color=self.controller.theme_manager.get("text_dim"))

        def save_memory():
            data = {}
            for uid, entries in self.memory_entries.items():
                facts = []
                for entry in entries:
                    val = entry["txt"].get("0.0", "end").strip()
                    if val:
                        facts.append(val)
                if facts:
                    data[uid] = facts
            
            try:
                ConfigManager.save_json(mem_path, data, use_lock=False)
                lbl_status.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e:
                lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_reload"), command=load_memory, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_save_changes"), command=save_memory, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        load_memory()
        self.controller.ai_reload_functions["config_ai_memory"] = load_memory