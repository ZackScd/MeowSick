import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SelfEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_self_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.controller.lang_manager.get("ai_self_desc"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        # Botones 50/50 para pestañas
        tab_container = ctk.CTkFrame(self, fg_color="transparent")
        tab_container.pack(side="top", fill="x", pady=(0, 10))
        
        scroll_gustos = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))
        scroll_opiniones = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))

        def switch_tab(tab_name):
            if tab_name == "Gustos":
                btn_gustos.configure(fg_color=self.controller.theme_manager.get("accent"), text_color=self.controller.theme_manager.get("bg_dark"))
                btn_opiniones.configure(fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"))
                scroll_opiniones.pack_forget()
                scroll_gustos.pack(side="top", fill="both", expand=True)
            else:
                btn_opiniones.configure(fg_color=self.controller.theme_manager.get("accent"), text_color=self.controller.theme_manager.get("bg_dark"))
                btn_gustos.configure(fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"))
                scroll_gustos.pack_forget()
                scroll_opiniones.pack(side="top", fill="both", expand=True)

        btn_gustos = ctk.CTkButton(tab_container, text=self.controller.lang_manager.get("ai_self_tab_likes"), command=lambda: switch_tab("Gustos"), fg_color=self.controller.theme_manager.get("accent"), text_color=self.controller.theme_manager.get("bg_dark"), height=36, corner_radius=8, font=ctk.CTkFont(weight="bold"))
        btn_gustos.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_opiniones = ctk.CTkButton(tab_container, text=self.controller.lang_manager.get("ai_self_tab_opinions"), command=lambda: switch_tab("Opiniones"), fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"), hover_color=self.controller.theme_manager.get("border"), height=36, corner_radius=8, font=ctk.CTkFont(weight="bold"))
        btn_opiniones.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Controls Bottom
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        data_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "autoconcepto.json")
        self.gustos_entries = []
        self.opiniones_entries = []

        def add_gusto_ui(text):
            row = ctk.CTkFrame(scroll_gustos, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=6)
            row.pack(fill="x", pady=4)
            
            txt_g = ctk.CTkTextbox(row, height=24, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
            txt_g.pack(side="left", fill="x", expand=True, padx=10, pady=5)
            txt_g.insert("0.0", text)
            self.controller._fix_scroll(txt_g)
            
            def resize_desc(event=None, t=txt_g):
                try:
                    w = t.winfo_width()
                    if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = t._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    t.configure(height=max(24, lines * 18))
                except: pass
            txt_g.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc)
            
            entry_data = {"row": row, "txt": txt_g}
            self.gustos_entries.append(entry_data)
            
            btn_del = ctk.CTkButton(row, text="🗑", width=30, height=26, fg_color="transparent", hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("text_dim"), command=lambda r=row, d=entry_data: delete_gusto(r, d))
            btn_del.pack(side="right", padx=(5, 10), pady=5)

        def delete_gusto(row, data):
            row.destroy()
            if data in self.gustos_entries:
                self.gustos_entries.remove(data)

        def add_opinion_ui(tema, opinion):
            card = ctk.CTkFrame(scroll_opiniones, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.controller.theme_manager.get("border"))
            card.pack(fill="x", pady=6)
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(top, text=self.controller.lang_manager.get("ai_self_lbl_topic"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")
            ent_tema = ctk.CTkEntry(top, width=200, height=28, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold"))
            ent_tema.pack(side="left", fill="x", expand=True, padx=10)
            ent_tema.insert(0, tema)
            
            btn_del = ctk.CTkButton(top, text="🗑", width=30, height=28, fg_color="transparent", hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("text_dim"))
            btn_del.pack(side="right")
            
            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(fill="x", padx=15, pady=5)
            
            txt_op = ctk.CTkTextbox(mid, height=40, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
            txt_op.pack(fill="x", expand=True, pady=(0, 10))
            txt_op.insert("0.0", opinion)
            self.controller._fix_scroll(txt_op)
            
            def resize_desc(event=None, t=txt_op):
                try:
                    w = t.winfo_width()
                    if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = t._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    t.configure(height=max(40, lines * 18))
                except: pass
            txt_op.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc)
            
            entry_data = {"card": card, "tema": ent_tema, "opinion": txt_op}
            self.opiniones_entries.append(entry_data)
            btn_del.configure(command=lambda c=card, d=entry_data: delete_opinion(c, d))

        def delete_opinion(card, data):
            card.destroy()
            if data in self.opiniones_entries:
                self.opiniones_entries.remove(data)

        add_g_btn_frame = ctk.CTkFrame(scroll_gustos, fg_color="transparent")
        ctk.CTkButton(add_g_btn_frame, text=self.controller.lang_manager.get("ai_self_btn_add_like"), height=28, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda: add_gusto_ui(self.controller.lang_manager.get("ai_self_new_like"))).pack(pady=10)

        add_o_btn_frame = ctk.CTkFrame(scroll_opiniones, fg_color="transparent")
        ctk.CTkButton(add_o_btn_frame, text=self.controller.lang_manager.get("ai_self_btn_add_opinion"), height=28, fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda: add_opinion_ui(self.controller.lang_manager.get("ai_self_new_topic"), self.controller.lang_manager.get("ai_self_new_opinion"))).pack(pady=10)

        def load_self():
            for data in self.gustos_entries: data["row"].destroy()
            self.gustos_entries.clear()
            for data in self.opiniones_entries: data["card"].destroy()
            self.opiniones_entries.clear()
            
            add_g_btn_frame.pack_forget()
            add_o_btn_frame.pack_forget()

            data = ConfigManager.load_json(data_path, use_lock=False)
            if isinstance(data, dict):
                gustos = data.get("gustos", [])
                for g in gustos: add_gusto_ui(g)
                
                ops = data.get("opiniones", {})
                for tema, op in ops.items(): add_opinion_ui(tema, op)
                
            add_g_btn_frame.pack(fill="x")
            add_o_btn_frame.pack(fill="x")
            lbl_status.configure(text=self.controller.lang_manager.get("ai_self_msg_loaded"), text_color=self.controller.theme_manager.get("text_dim"))

        def save_self():
            new_gustos = []
            for d in self.gustos_entries:
                val = d["txt"].get("0.0", "end").strip()
                if val: new_gustos.append(val)
                
            new_ops = {}
            for d in self.opiniones_entries:
                tema = d["tema"].get().strip()
                op = d["opinion"].get("0.0", "end").strip()
                if tema: new_ops[tema] = op
                
            data = {"gustos": new_gustos, "opiniones": new_ops}
            try:
                ConfigManager.save_json(data_path, data, use_lock=False)
                lbl_status.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        btns_self = ctk.CTkFrame(controls, fg_color="transparent")
        btns_self.pack(side="left")
        ctk.CTkButton(btns_self, text=self.controller.lang_manager.get("btn_reload"), command=load_self, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(btns_self, text=self.controller.lang_manager.get("btn_save_changes"), command=save_self, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        switch_tab("Gustos")
        load_self()
        self.controller.ai_reload_functions["config_ai_self"] = load_self