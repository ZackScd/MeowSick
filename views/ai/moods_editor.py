import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MoodsEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_moods_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_moods_desc"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=(5,0))
        
        lbl_status = ctk.CTkLabel(title_row, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=15)

        # Controles inferiores (Recargar e Historial)
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))

        btn_reload = ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_reload"), width=120, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        btn_reload.pack(side="left")
        
        def open_history():
            from views.ai.moods_history_editor import MoodsHistoryEditor
            self.controller.show_frame(MoodsHistoryEditor)
            
        btn_history = ctk.CTkButton(controls, text=self.controller.lang_manager.get("ai_moods_btn_history"), fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=open_history)
        btn_history.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Scroll principal
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))
        scroll.pack(side="top", fill="both", expand=True)

        # 1. ESTADO ACTUAL
        curr_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        curr_frame.pack(fill="x", pady=(5, 10))
        
        # Wrapper para mantener el título y la ayuda juntos
        curr_header_wrap = ctk.CTkFrame(curr_frame, fg_color="transparent")
        curr_header_wrap.pack(fill="x")
        
        curr_lbl_row = ctk.CTkFrame(curr_header_wrap, fg_color="transparent")
        curr_lbl_row.pack(fill="x")
        ctk.CTkLabel(curr_lbl_row, text=self.controller.lang_manager.get("ai_moods_lbl_current"), font=ctk.CTkFont(weight="bold", size=13), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        
        curr_help = ctk.CTkFrame(curr_header_wrap, fg_color="transparent")
        ctk.CTkLabel(curr_help, text=self.controller.lang_manager.get("ai_moods_help_current"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        ctk.CTkButton(curr_lbl_row, text="?", width=24, height=24, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=curr_help: self.controller.toggle_help(h, "pack", fill="x")).pack(side="left", padx=10)
        
        btn_save_curr = ctk.CTkButton(curr_lbl_row, text=self.controller.lang_manager.get("ai_moods_btn_save_current"), width=120, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        btn_save_curr.pack(side="right")
        
        # Título editable del estado
        entry_mood_name = ctk.CTkEntry(curr_frame, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold", size=14))
        entry_mood_name.pack(fill="x", pady=(5, 5))
        
        # Contenedor visible para la descripción
        desc_container = ctk.CTkFrame(curr_frame, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=8, border_width=1, border_color=self.controller.theme_manager.get("border"))
        desc_container.pack(fill="x")
        
        entry_mood_desc = ctk.CTkTextbox(desc_container, height=60, font=("Consolas", 13), fg_color="transparent", border_width=0, text_color=self.controller.theme_manager.get("text"), wrap="word")
        entry_mood_desc.pack(fill="x", padx=10, pady=10)
        self.controller._fix_scroll(entry_mood_desc)

        def resize_desc_current(event=None):
            try:
                dl = entry_mood_desc._textbox.count("1.0", "end", "displaylines")
                lines = dl[0] if dl else 1
                entry_mood_desc.configure(height=max(60, lines * 22))
            except: pass
        entry_mood_desc.bind("<KeyRelease>", resize_desc_current)

        # 2. ESTADOS POSIBLES
        poss_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        poss_frame.pack(fill="x", pady=(5, 15))
        
        poss_header_wrap = ctk.CTkFrame(poss_frame, fg_color="transparent")
        poss_header_wrap.pack(fill="x")
        
        poss_lbl_row = ctk.CTkFrame(poss_header_wrap, fg_color="transparent")
        poss_lbl_row.pack(fill="x")
        ctk.CTkLabel(poss_lbl_row, text=self.controller.lang_manager.get("ai_moods_lbl_possible"), font=ctk.CTkFont(weight="bold", size=13), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        
        poss_help = ctk.CTkFrame(poss_header_wrap, fg_color="transparent")
        ctk.CTkLabel(poss_help, text=self.controller.lang_manager.get("ai_moods_help_possible"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        ctk.CTkButton(poss_lbl_row, text="?", width=24, height=24, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=poss_help: self.controller.toggle_help(h, "pack", fill="x")).pack(side="left", padx=10)

        btn_save_poss = ctk.CTkButton(poss_lbl_row, text=self.controller.lang_manager.get("ai_moods_btn_save_list"), width=120, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        btn_save_poss.pack(side="right")
        
        btn_add_poss = ctk.CTkButton(poss_lbl_row, text=self.controller.lang_manager.get("btn_add"), width=80, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        btn_add_poss.pack(side="right", padx=(0, 5))

        poss_list_container = ctk.CTkFrame(poss_frame, fg_color="transparent")
        poss_list_container.pack(fill="x", pady=(5, 0))

        self.poss_moods_entries = []

        def add_possible_mood(name_val, desc_val):
            row = ctk.CTkFrame(poss_list_container, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=8)
            row.pack(fill="x", pady=4)
            
            btn_del = ctk.CTkButton(row, text="🗑", width=30, height=30, fg_color="transparent", hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("text_dim"))
            btn_del.pack(side="right", padx=10)
            
            content = ctk.CTkFrame(row, fg_color="transparent")
            content.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            
            name_entry = ctk.CTkEntry(content, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold"))
            name_entry.pack(fill="x", pady=(0, 5))
            name_entry.insert(0, name_val)
            
            desc_txt = ctk.CTkTextbox(content, height=46, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), wrap="word")
            desc_txt.pack(fill="x")
            desc_txt.insert("0.0", desc_val)
            self.controller._fix_scroll(desc_txt)
            
            def resize_desc(event=None):
                try:
                    dl = desc_txt._textbox.count("1.0", "end", "displaylines")
                    lines = dl[0] if dl else 1
                    desc_txt.configure(height=max(46, lines * 20))
                except: pass
            desc_txt.bind("<KeyRelease>", resize_desc)
            self.after(50, resize_desc)
            
            entry_data = {"row": row, "name": name_entry, "desc": desc_txt}
            self.poss_moods_entries.append(entry_data)
            
            btn_del.configure(command=lambda r=row, d=entry_data: delete_possible_mood(r, d))

        def delete_possible_mood(row, data):
            row.destroy()
            if data in self.poss_moods_entries:
                self.poss_moods_entries.remove(data)

        def open_new_mood_dialog():
            dialog = ctk.CTkToplevel(self)
            dialog.title(self.controller.lang_manager.get("ai_moods_dlg_title"))
            dialog.geometry("450x400")
            dialog.configure(fg_color=self.controller.theme_manager.get("bg_dark"))
            dialog.transient(self)
            dialog.grab_set()
            
            ctk.CTkLabel(dialog, text=self.controller.lang_manager.get("ai_moods_dlg_header"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(20, 10))
            
            form = ctk.CTkFrame(dialog, fg_color="transparent")
            form.pack(fill="both", expand=True, padx=20)
            
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_moods_dlg_name"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_name = ctk.CTkEntry(form, fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), font=ctk.CTkFont(weight="bold"))
            entry_name.pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_moods_dlg_name_ph"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_moods_dlg_desc"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x")
            txt_desc = ctk.CTkTextbox(form, height=80, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
            txt_desc.pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_moods_dlg_desc_ph"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", pady=(0, 10))
            
            lbl_err = ctk.CTkLabel(dialog, text="", text_color=self.controller.theme_manager.get("red"), font=ctk.CTkFont(size=12))
            lbl_err.pack(pady=(5, 5))
            
            def save_new():
                name_val = entry_name.get().strip()
                desc_val = txt_desc.get("0.0", "end").strip()
                if not name_val:
                    return lbl_err.configure(text=self.controller.lang_manager.get("ai_moods_err_name"))
                add_possible_mood(name_val, desc_val)
                dialog.destroy()

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=(0, 20))
            ctk.CTkButton(btn_frame, text=self.controller.lang_manager.get("btn_cancel"), width=100, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=dialog.destroy).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text=self.controller.lang_manager.get("btn_save_short"), width=100, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), command=save_new).pack(side="left", padx=10)

        btn_add_poss.configure(command=open_new_mood_dialog)

        curr_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "estado_animo.json")
        poss_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "estados_posibles.json")

        def load_moods():
            entry_mood_name.delete(0, "end")
            entry_mood_desc.delete("0.0", "end")
            for w in poss_list_container.winfo_children(): w.destroy()
            self.poss_moods_entries.clear()
            curr_data = ConfigManager.load_json(curr_path, use_lock=False)
            if curr_data:
                val = curr_data.get("estado_animo", "")
                if ":" in val:
                    name, desc = val.split(":", 1)
                    entry_mood_name.insert(0, name.strip())
                    entry_mood_desc.insert("0.0", desc.strip())
                else: entry_mood_name.insert(0, val.strip())
                self.after(50, resize_desc_current)
                
            poss_data = ConfigManager.load_json(poss_path, use_lock=False)
            if isinstance(poss_data, list) and poss_data:
                for val in poss_data:
                    if ":" in val:
                        name, desc = val.split(":", 1)
                        add_possible_mood(name.strip(), desc.strip())
                    else: add_possible_mood(val.strip(), "")
            if not self.poss_moods_entries:
                add_possible_mood("Neutral", self.controller.lang_manager.get("ai_moods_def_neutral"))
            lbl_status.configure(text=self.controller.lang_manager.get("msg_files_loaded"), text_color=self.controller.theme_manager.get("text_dim"))

        def save_current_mood():
            try:
                name = entry_mood_name.get().strip()
                desc = entry_mood_desc.get("0.0", "end").strip()
                full_val = f"{name}: {desc}" if desc else name
                ConfigManager.save_json(curr_path, {"estado_animo": full_val}, use_lock=False)
                lbl_status.configure(text=self.controller.lang_manager.get("ai_moods_msg_saved_curr"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))
            
        def save_possible_moods():
            try:
                poss_list = []
                for item in self.poss_moods_entries:
                    name = item["name"].get().strip()
                    desc = item["desc"].get("0.0", "end").strip()
                    if name:
                        full_val = f"{name}: {desc}" if desc else name
                        poss_list.append(full_val)
                ConfigManager.save_json(poss_path, poss_list, use_lock=False)
                lbl_status.configure(text=self.controller.lang_manager.get("ai_moods_msg_saved_list"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        btn_save_curr.configure(command=save_current_mood)
        btn_save_poss.configure(command=save_possible_moods)
        btn_reload.configure(command=load_moods)

        load_moods()
        self.controller.ai_reload_functions["config_ai_moods"] = load_moods