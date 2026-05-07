import os
import sys
import customtkinter as ctk
from tkinter import messagebox
from shared.config_manager import ConfigManager
from shared.presets import AI_PRESETS

class AIAmnesiaConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        if getattr(sys, 'frozen', False):
            self.mem_dir = os.path.join(os.path.dirname(sys.executable), "cogs", "AI", "memory")
        else:
            self.mem_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cogs", "AI", "memory")

        # Header
        ctk.CTkLabel(self, text=self.controller.lang_manager.get("nav_ai_amnesia", "🎭 Personalidad y Reseteo"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(0, 15))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ==========================================
        # SECCIÓN 1: PERSONALIDADES PREFABRICADAS
        # ==========================================
        preset_title = ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ai_presets_title", "Personalidades Prefabricadas"), font=ctk.CTkFont(size=16, weight="bold"), text_color=self.controller.theme_manager.get("text"))
        preset_title.pack(anchor="w", padx=20, pady=(10, 5))

        # Selector
        selector_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        selector_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(selector_frame, text=self.controller.lang_manager.get("cfg_ai_presets_sel", "Seleccionar Personalidad:"), text_color=self.controller.theme_manager.get("text"), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=15)
        
        self.preset_map = {p_data["name"]: p_key for p_key, p_data in AI_PRESETS.items()}
        preset_names = list(self.preset_map.keys())
        
        self.preset_var = ctk.StringVar(value=preset_names[0])
        self.combo_preset = ctk.CTkComboBox(selector_frame, variable=self.preset_var, values=preset_names, width=300, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"), command=self.on_preset_change)
        self.combo_preset.pack(side="left", padx=10, pady=15)

        # Panel Informativo
        info_frame = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(info_frame, text=self.controller.lang_manager.get("ai_wiz_summary", "Resumen:"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=15, pady=(15, 0))
        self.txt_summary = ctk.CTkTextbox(info_frame, height=80, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1)
        self.txt_summary.pack(fill="x", padx=15, pady=(5, 10))
        self.controller._fix_scroll(self.txt_summary)
        
        self.chk_id = ctk.CTkCheckBox(info_frame, text=self.controller.lang_manager.get("ai_id_lbl_identity", "Identidad (System Prompt Base)"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("accent"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20)
        self.chk_id.pack(anchor="w", padx=15, pady=(10, 0))
        self.chk_id.select()
        self.txt_identity = ctk.CTkTextbox(info_frame, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1)
        self.txt_identity.pack(fill="x", padx=15, pady=(5, 10))
        self.controller._fix_scroll(self.txt_identity)

        self.chk_guide = ctk.CTkCheckBox(info_frame, text=self.controller.lang_manager.get("ai_id_lbl_guidelines", "Guidelines (Reglas de Comportamiento)"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("accent"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20)
        self.chk_guide.pack(anchor="w", padx=15, pady=(10, 0))
        self.chk_guide.select()
        self.txt_guidelines = ctk.CTkTextbox(info_frame, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1)
        self.txt_guidelines.pack(fill="x", padx=15, pady=(5, 10))
        self.controller._fix_scroll(self.txt_guidelines)
        
        self.chk_moods = ctk.CTkCheckBox(info_frame, text="Estados de Ánimo Posibles", font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("accent"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20)
        self.chk_moods.pack(anchor="w", padx=15, pady=(10, 0))
        self.chk_moods.select()
        self.txt_moods = ctk.CTkTextbox(info_frame, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1)
        self.txt_moods.pack(fill="x", padx=15, pady=(5, 10))
        self.controller._fix_scroll(self.txt_moods)

        self.chk_aff = ctk.CTkCheckBox(info_frame, text="Rangos de Afinidad", font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("accent"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20)
        self.chk_aff.pack(anchor="w", padx=15, pady=(10, 0))
        self.chk_aff.select()
        self.txt_aff = ctk.CTkTextbox(info_frame, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1)
        self.txt_aff.pack(fill="x", padx=15, pady=(5, 10))
        self.controller._fix_scroll(self.txt_aff)

        self.chk_self = ctk.CTkCheckBox(info_frame, text="Autoconcepto (Gustos predefinidos)", font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("accent"), onvalue=True, offvalue=False, checkbox_height=20, checkbox_width=20)
        self.chk_self.pack(anchor="w", padx=15, pady=(10, 0))
        self.chk_self.select()
        self.txt_self = ctk.CTkTextbox(info_frame, height=80, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1)
        self.txt_self.pack(fill="x", padx=15, pady=(5, 15))
        self.controller._fix_scroll(self.txt_self)
        
        self.on_preset_change(preset_names[0])

        # Botón Aplicar Preset
        btn_pre_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_pre_frame.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkButton(btn_pre_frame, text=self.controller.lang_manager.get("cfg_ai_presets_btn_apply", "Aplicar Personalidad"), fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b", text_color=self.controller.theme_manager.get("bg_dark"), font=ctk.CTkFont(weight="bold"), height=40, command=self.apply_preset).pack(side="right")
        
        self.lbl_status = ctk.CTkLabel(btn_pre_frame, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        self.lbl_status.pack(side="right", padx=15)

        # ==========================================
        # SECCIÓN 2: BORRADO MODULAR (AMNESIA)
        # ==========================================
        ctk.CTkFrame(scroll, height=2, fg_color=self.controller.theme_manager.get("border")).pack(fill="x", padx=20, pady=15)
        
        amnesia_title = ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("dlg_amnesia_header", "⚠️ Borrar Memoria de la IA"), font=ctk.CTkFont(size=16, weight="bold"), text_color=self.controller.theme_manager.get("red"))
        amnesia_title.pack(anchor="w", padx=20, pady=(5, 5))

        warn_lbl = ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("dlg_amnesia_desc", "Selecciona qué archivos deseas devolver a su\nestado de fábrica original. ¡Esto no se puede deshacer!"), text_color=self.controller.theme_manager.get("text_dim"), justify="left")
        warn_lbl.pack(anchor="w", padx=20, pady=(0, 15))

        mem_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        mem_card.pack(fill="x", padx=20, pady=(0, 10))

        self.chk_vars = {}

        self._add_check(mem_card, "users", self.controller.lang_manager.get("dlg_amnesia_opt_users", "Registro de Usuarios Conocidos"))
        self._add_check(mem_card, "opinions", self.controller.lang_manager.get("dlg_amnesia_opt_opi", "Opiniones Sociales y Afinidad"))
        self._add_check(mem_card, "memory", self.controller.lang_manager.get("dlg_amnesia_opt_mem", "Hechos y Recuerdos (Biografías)"))
        self._add_check(mem_card, "history", self.controller.lang_manager.get("dlg_amnesia_opt_history", "Historial de Estados de Ánimo"))
        
        # Autoconcepto Granular
        self.chk_vars["self_gustos"] = ctk.BooleanVar(value=False)
        self.chk_vars["self_opiniones"] = ctk.BooleanVar(value=False)
        
        auto_frame = ctk.CTkFrame(mem_card, fg_color="transparent")
        auto_frame.pack(fill="x", pady=(5, 5))
        ctk.CTkLabel(auto_frame, text=self.controller.lang_manager.get("dlg_amnesia_opt_self", "Autoconcepto y Gustos") + ":", font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=15)
        
        ctk.CTkCheckBox(auto_frame, text=self.controller.lang_manager.get("reset_self_likes", "Borrar Gustos"), variable=self.chk_vars["self_gustos"], fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b").pack(anchor="w", padx=30, pady=5)
        ctk.CTkCheckBox(auto_frame, text=self.controller.lang_manager.get("reset_self_ops", "Borrar Opiniones Propias"), variable=self.chk_vars["self_opiniones"], fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b").pack(anchor="w", padx=30, pady=(5, 15))

        # Botón Aplicar Borrado Modular
        btn_del_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_del_frame.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkButton(btn_del_frame, text=self.controller.lang_manager.get("dlg_amnesia_btn_del", "¡Borrar Seleccionados!"), fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b", font=ctk.CTkFont(weight="bold"), height=40, command=self.apply_reset).pack(side="right")

    def _add_check(self, parent, key, text):
        var = ctk.BooleanVar(value=False)
        self.chk_vars[key] = var
        ctk.CTkCheckBox(parent, text=text, variable=var, fg_color=self.controller.theme_manager.get("red"), hover_color="#c5536b").pack(anchor="w", padx=15, pady=8)

    def on_preset_change(self, choice):
        p_key = self.preset_map.get(choice)
        preset = AI_PRESETS.get(p_key, {})
        
        self.txt_summary.configure(state="normal")
        self.txt_summary.delete("0.0", "end")
        self.txt_summary.insert("0.0", preset.get("summary", ""))
        self.txt_summary.configure(state="disabled")
        
        self.txt_identity.configure(state="normal")
        self.txt_identity.delete("0.0", "end")
        self.txt_identity.insert("0.0", preset.get("identity", ""))
        self.txt_identity.configure(state="disabled")
        
        self.txt_guidelines.configure(state="normal")
        self.txt_guidelines.delete("0.0", "end")
        self.txt_guidelines.insert("0.0", preset.get("guidelines", ""))
        self.txt_guidelines.configure(state="disabled")
        
        self.txt_moods.configure(state="normal")
        self.txt_moods.delete("0.0", "end")
        self.txt_moods.insert("0.0", "\n".join(preset.get("estados_posibles", [])))
        self.txt_moods.configure(state="disabled")

        self.txt_aff.configure(state="normal")
        self.txt_aff.delete("0.0", "end")
        aff_text = "\n".join([f"[{r['min']} a {r['max']}] {r['etiqueta']}: {r['descripcion']}" for r in preset.get("afinidad_rangos", [])])
        self.txt_aff.insert("0.0", aff_text)
        self.txt_aff.configure(state="disabled")

        self.txt_self.configure(state="normal")
        self.txt_self.delete("0.0", "end")
        auto = preset.get("autoconcepto", {})
        gustos = ", ".join(auto.get("gustos", []))
        self.txt_self.insert("0.0", f"Gustos: {gustos}\nOpiniones: {len(auto.get('opiniones', {}))} registradas.")
        self.txt_self.configure(state="disabled")

    def apply_preset(self):
        p_key = self.preset_map.get(self.preset_var.get())
        preset = AI_PRESETS.get(p_key)
        if not preset: return
        
        try:
            if self.chk_id.get():
                with open(os.path.join(self.mem_dir, "identity.txt"), "w", encoding="utf-8") as f: f.write(preset["identity"])
            if self.chk_guide.get():
                with open(os.path.join(self.mem_dir, "guidelines.txt"), "w", encoding="utf-8") as f: f.write(preset["guidelines"])
            if self.chk_aff.get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "afinidad_rangos.json"), preset["afinidad_rangos"], use_lock=False)
            
            if self.chk_moods.get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "estados_posibles.json"), preset["estados_posibles"], use_lock=False)
            
            if self.chk_self.get():
                auto_path = os.path.join(self.mem_dir, "autoconcepto.json")
                curr_auto = ConfigManager.load_json(auto_path, use_lock=False) or {"gustos": [], "opiniones": {}}
                curr_auto["gustos"] = preset.get("autoconcepto", {}).get("gustos", [])
                curr_auto["opiniones"] = preset.get("autoconcepto", {}).get("opiniones", {})
                ConfigManager.save_json(auto_path, curr_auto, use_lock=False)
                
            self.controller.reload_all_ai_files()
            self.controller.send_to_bot('IPC>>{"type": "command", "name": "reload"}')
            
            self.lbl_status.configure(text=self.controller.lang_manager.get("cfg_ai_presets_applied", "¡Personalidad Aplicada!"), text_color=self.controller.theme_manager.get("green"))
        except Exception as e:
            self.lbl_status.configure(text=f"Error: {e}", text_color=self.controller.theme_manager.get("red"))
            
        self.after(3000, lambda: self.lbl_status.configure(text=""))

    def apply_reset(self):
        try:
            if self.chk_vars["users"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "known_users.json"), {}, use_lock=False)
            if self.chk_vars["opinions"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "opiniones.json"), {}, use_lock=False)
            if self.chk_vars["memory"].get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "memoria.json"), {}, use_lock=False)
            if self.chk_vars.get("history", ctk.BooleanVar(value=False)).get():
                ConfigManager.save_json(os.path.join(self.mem_dir, "historial_estados.json"), [], use_lock=False)
            
            # Granular Autoconcepto
            if self.chk_vars["self_gustos"].get() or self.chk_vars["self_opiniones"].get():
                auto_path = os.path.join(self.mem_dir, "autoconcepto.json")
                curr_auto = ConfigManager.load_json(auto_path, use_lock=False) or {"gustos": [], "opiniones": {}}
                if self.chk_vars["self_gustos"].get(): curr_auto["gustos"] = []
                if self.chk_vars["self_opiniones"].get(): curr_auto["opiniones"] = {}
                ConfigManager.save_json(auto_path, curr_auto, use_lock=False)

            self.controller.reload_all_ai_files()
            self.controller.send_to_bot('IPC>>{"type": "command", "name": "reload"}')
            messagebox.showinfo(self.controller.lang_manager.get("dlg_amnesia_msg_ok_title", "Éxito"), self.controller.lang_manager.get("dlg_amnesia_msg_ok", "Archivos restablecidos a fábrica correctamente."))
        except Exception as e:
            messagebox.showerror(self.controller.lang_manager.get("dlg_amnesia_msg_err_title", "Error"), self.controller.lang_manager.get("dlg_amnesia_msg_err", "Fallo al restablecer: {e}").format(e=e))