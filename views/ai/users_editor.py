import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class UsersEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_users_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.controller.lang_manager.get("ai_users_desc"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        # Controls (Bottom)
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        # Table Header (Cabeceras de Columnas)
        table_header = ctk.CTkFrame(self, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=6)
        table_header.pack(side="top", fill="x", padx=(10, 16), pady=(0, 2))
        
        ctk.CTkLabel(table_header, text=self.controller.lang_manager.get("ai_users_col_id"), width=150, anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.controller.theme_manager.get("accent")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(table_header, text=self.controller.lang_manager.get("ai_users_col_name"), width=150, anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.controller.theme_manager.get("accent")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(table_header, text=self.controller.lang_manager.get("ai_users_col_role"), width=150, anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.controller.theme_manager.get("accent")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(table_header, text=self.controller.lang_manager.get("ai_users_col_rel"), anchor="w", font=ctk.CTkFont(weight="bold", size=13), text_color=self.controller.theme_manager.get("accent")).pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Scrollable Content (Filas)
        scroll = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            scrollbar_button_color=self.controller.theme_manager.get("bg_dark"),
            scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark")
        )
        scroll.pack(side="top", fill="both", expand=True)

        self.users_entries_data = []
        file_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "known_users.json")

        def delete_user_record(uid_to_delete):
            try:
                data = ConfigManager.load_json(file_path, use_lock=False)
                if isinstance(data, dict) and uid_to_delete in data:
                    del data[uid_to_delete]
                    ConfigManager.save_json(file_path, data, use_lock=False)
                    load_users()
                    lbl_status.configure(text=self.controller.lang_manager.get("ai_users_msg_del"), text_color=self.controller.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e:
                lbl_status.configure(text=self.controller.lang_manager.get("ai_users_msg_err_del").format(e=e), text_color=self.controller.theme_manager.get("red"))
                self.after(3000, lambda: lbl_status.configure(text=""))

        def load_users():
            for widget in scroll.winfo_children():
                widget.destroy()
            self.users_entries_data.clear()
            
            data = ConfigManager.load_json(file_path, use_lock=False)
            if isinstance(data, dict) and data:
                try:
                    for uid, info in data.items():
                        row = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=8)
                        row.pack(fill="x", pady=4)
                        
                        btn_del = ctk.CTkButton(row, text="🗑", width=30, height=46, fg_color="transparent", hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("text_dim"))
                        btn_del.pack(side="right", padx=10, pady=10)
                        
                        # ID (Solo texto, seleccionable pero no editable)
                        id_entry = ctk.CTkEntry(row, width=150, height=46, fg_color="transparent", border_width=0, text_color=self.controller.theme_manager.get("text_dim"))
                        id_entry.pack(side="left", padx=5, pady=10)
                        id_entry.insert(0, uid)
                        id_entry.configure(state="readonly")
                        
                        name_entry = ctk.CTkEntry(row, width=150, height=46, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
                        name_entry.pack(side="left", padx=5, pady=10)
                        name_entry.insert(0, info.get("nombre", ""))
                        
                        role_entry = ctk.CTkEntry(row, width=150, height=46, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
                        role_entry.pack(side="left", padx=5, pady=10)
                        role_entry.insert(0, info.get("rol_base", ""))
                        
                        rel_txt = ctk.CTkTextbox(row, height=46, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
                        rel_txt.pack(side="left", fill="x", expand=True, padx=(5, 10), pady=10)
                        rel_txt.insert("0.0", info.get("relacion", ""))
                        self.controller._fix_scroll(rel_txt)
                        
                        self.users_entries_data.append({
                            "uid": uid, "nombre": name_entry, "rol_base": role_entry, "relacion": rel_txt
                        })
                        
                        btn_del.configure(command=lambda u=uid: delete_user_record(u))
                        
                    lbl_status.configure(text=self.controller.lang_manager.get("ai_users_msg_loaded"), text_color=self.controller.theme_manager.get("text_dim"))
                except Exception as e:
                    lbl_status.configure(text=self.controller.lang_manager.get("ai_users_msg_err_load"), text_color=self.controller.theme_manager.get("red"))
            else:
                lbl_status.configure(text=self.controller.lang_manager.get("ai_users_msg_empty"), text_color=self.controller.theme_manager.get("text_dim"))

        def save_users():
            data = {item["uid"]: {"nombre": item["nombre"].get().strip(), "rol_base": item["rol_base"].get().strip(), "relacion": item["relacion"].get("0.0", "end").strip()} for item in self.users_entries_data}
            try:
                ConfigManager.save_json(file_path, data, use_lock=False)
                lbl_status.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e:
                lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        def open_new_user_dialog():
            dialog = ctk.CTkToplevel(self)
            dialog.title(self.controller.lang_manager.get("ai_users_dlg_title"))
            dialog.geometry("450x550")
            dialog.configure(fg_color=self.controller.theme_manager.get("bg_dark"))
            dialog.transient(self) # Mantener la ventana por encima del launcher
            dialog.grab_set() # Bloquear interacción con la ventana principal
            
            ctk.CTkLabel(dialog, text=self.controller.lang_manager.get("ai_users_dlg_header"), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(20, 10))
            
            form = ctk.CTkFrame(dialog, fg_color="transparent")
            form.pack(fill="both", expand=True, padx=20)
            
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_users_dlg_lbl_id"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_id = ctk.CTkEntry(form, fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
            entry_id.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_users_dlg_lbl_name"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_name = ctk.CTkEntry(form, fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
            entry_name.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_users_dlg_lbl_role"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x")
            entry_role = ctk.CTkEntry(form, fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
            entry_role.pack(fill="x", pady=(0, 10))
            entry_role.insert(0, self.controller.lang_manager.get("ai_users_def_role")) # Valor por defecto
            
            ctk.CTkLabel(form, text=self.controller.lang_manager.get("ai_users_dlg_lbl_rel"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x")
            txt_rel = ctk.CTkTextbox(form, height=100, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
            txt_rel.pack(fill="x", pady=(0, 10))
            
            lbl_err = ctk.CTkLabel(dialog, text="", text_color=self.controller.theme_manager.get("red"), font=ctk.CTkFont(size=12))
            lbl_err.pack(pady=(5, 5))
            
            def save_new():
                uid = entry_id.get().strip()
                name = entry_name.get().strip()
                role = entry_role.get().strip()
                rel = txt_rel.get("0.0", "end").strip()
                
                if not uid: return lbl_err.configure(text=self.controller.lang_manager.get("ai_users_dlg_err_id_req"))
                if not uid.isdigit(): return lbl_err.configure(text=self.controller.lang_manager.get("ai_users_dlg_err_id_num"))
                if not name: return lbl_err.configure(text=self.controller.lang_manager.get("ai_users_dlg_err_name_req"))
                
                try:
                    data = ConfigManager.load_json(file_path, use_lock=False)
                    if not isinstance(data, dict): data = {}
                    if uid in data: return lbl_err.configure(text=self.controller.lang_manager.get("ai_users_dlg_err_exists"))
                        
                    data[uid] = {"nombre": name, "rol_base": role, "relacion": rel}
                    ConfigManager.save_json(file_path, data, use_lock=False)
                    
                    dialog.destroy()
                    load_users()
                    lbl_status.configure(text=self.controller.lang_manager.get("ai_users_dlg_msg_success"), text_color=self.controller.theme_manager.get("green"))
                    self.after(3000, lambda: lbl_status.configure(text=""))
                except Exception as e: lbl_err.configure(text=self.controller.lang_manager.get("msg_err_saving").format(e=e))

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=(0, 20))
            
            ctk.CTkButton(btn_frame, text=self.controller.lang_manager.get("btn_cancel"), width=100, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=dialog.destroy).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text=self.controller.lang_manager.get("btn_save_short"), width=100, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), command=save_new).pack(side="left", padx=10)

        ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_reload"), command=load_users, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.controller.lang_manager.get("ai_users_btn_new"), command=open_new_user_dialog, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(controls, text=self.controller.lang_manager.get("btn_save_changes"), command=save_users, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        load_users()
        self.controller.ai_reload_functions["config_ai_users"] = load_users