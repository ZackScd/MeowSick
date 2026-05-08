import customtkinter as ctk
import os
import sys
from shared.presets import AI_PRESETS
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MEM_DIR = os.path.join(BASE_DIR, "cogs", "AI", "memory")

class AIWizardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.card = ctk.CTkFrame(self, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=15)
        self.card.grid(row=0, column=0, pady=20, padx=20, sticky="nsew")
        
        self.lbl_title = ctk.CTkLabel(self.card, text=self.controller.lang_manager.get("ai_wiz_title", "✨ Inicialización del Núcleo de IA"), font=ctk.CTkFont(size=24, weight="bold"), text_color=self.controller.theme_manager.get("accent"))
        self.lbl_title.pack(pady=(30, 5))
        
        self.lbl_desc = ctk.CTkLabel(self.card, text=self.controller.lang_manager.get("ai_wiz_desc", "Antes de encender el cerebro, elige su personalidad base."), font=ctk.CTkFont(size=13), text_color=self.controller.theme_manager.get("text_dim"), wraplength=700)
        self.lbl_desc.pack(pady=(0, 15))

        self.scroll = ctk.CTkScrollableFrame(self.card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=5)

        self.preset_map = {p_data["name"]: p_key for p_key, p_data in AI_PRESETS.items()}
        preset_names = list(self.preset_map.keys())

        row_sel = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row_sel.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(row_sel, text=self.controller.lang_manager.get("ai_wiz_sel", "Selecciona un Perfil:"), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        
        self.combo_preset = ctk.CTkComboBox(row_sel, values=preset_names, width=400, command=self.on_preset_change, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"))
        self.combo_preset.pack(side="right")
        
        ctk.CTkFrame(self.scroll, height=2, fg_color=self.controller.theme_manager.get("border")).pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(self.scroll, text=self.controller.lang_manager.get("ai_wiz_summary", "Resumen:"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=30, pady=(5, 0))
        self.txt_summary = ctk.CTkTextbox(self.scroll, height=100, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"))
        self.txt_summary.pack(fill="x", padx=30, pady=(5, 10))
        self.controller._fix_scroll(self.txt_summary)
        
        ctk.CTkLabel(self.scroll, text=self.controller.lang_manager.get("ai_id_lbl_identity", "Identidad (System Prompt Base):"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=30, pady=(10, 0))
        self.txt_identity = ctk.CTkTextbox(self.scroll, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"))
        self.txt_identity.pack(fill="x", padx=30, pady=(5, 10))
        self.controller._fix_scroll(self.txt_identity)

        ctk.CTkLabel(self.scroll, text=self.controller.lang_manager.get("ai_id_lbl_guidelines", "Guidelines (Reglas de Comportamiento):"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=30, pady=(10, 0))
        self.txt_guidelines = ctk.CTkTextbox(self.scroll, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"))
        self.txt_guidelines.pack(fill="x", padx=30, pady=(5, 10))
        self.controller._fix_scroll(self.txt_guidelines)
        
        ctk.CTkLabel(self.scroll, text="Estados de Ánimo Posibles:", font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=30, pady=(10, 0))
        self.txt_moods = ctk.CTkTextbox(self.scroll, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"))
        self.txt_moods.pack(fill="x", padx=30, pady=(5, 10))
        self.controller._fix_scroll(self.txt_moods)

        ctk.CTkLabel(self.scroll, text="Rangos de Afinidad:", font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=30, pady=(10, 0))
        self.txt_aff = ctk.CTkTextbox(self.scroll, height=120, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"))
        self.txt_aff.pack(fill="x", padx=30, pady=(5, 10))
        self.controller._fix_scroll(self.txt_aff)

        ctk.CTkLabel(self.scroll, text="Autoconcepto (Gustos predefinidos):", font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", padx=30, pady=(10, 0))
        self.txt_self = ctk.CTkTextbox(self.scroll, height=80, font=("Consolas", 13), fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"))
        self.txt_self.pack(fill="x", padx=30, pady=(5, 15))
        self.controller._fix_scroll(self.txt_self)

        self.combo_preset.set(preset_names[0])
        self.on_preset_change(preset_names[0])

        self.btn_apply = ctk.CTkButton(self.scroll, text=self.controller.lang_manager.get("ai_wiz_btn_start", "🚀 Aplicar e Iniciar"), font=ctk.CTkFont(size=14, weight="bold"), fg_color=self.controller.theme_manager.get("accent"), text_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("accent_dim"), height=45, width=250, command=self.apply_preset)
        self.btn_apply.pack(pady=30)

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
        p_key = self.preset_map.get(self.combo_preset.get())
        preset = AI_PRESETS.get(p_key)
        if not preset: return
        
        # Guardamos la personalidad directamente en los archivos
        os.makedirs(MEM_DIR, exist_ok=True)
        with open(os.path.join(MEM_DIR, "identity.txt"), "w", encoding="utf-8") as f: f.write(preset["identity"])
        with open(os.path.join(MEM_DIR, "guidelines.txt"), "w", encoding="utf-8") as f: f.write(preset["guidelines"])
        ConfigManager.save_json(os.path.join(MEM_DIR, "afinidad_rangos.json"), preset["afinidad_rangos"], use_lock=False)
        ConfigManager.save_json(os.path.join(MEM_DIR, "estados_posibles.json"), preset["estados_posibles"], use_lock=False)
        
        auto_path = os.path.join(MEM_DIR, "autoconcepto.json")
        curr_auto = ConfigManager.load_json(auto_path, use_lock=False) or {"gustos": [], "opiniones": {}}
        curr_auto["gustos"] = preset.get("autoconcepto", {}).get("gustos", [])
        curr_auto["opiniones"] = preset.get("autoconcepto", {}).get("opiniones", {})
        ConfigManager.save_json(auto_path, curr_auto, use_lock=False)

        cfg = self.controller._load_json_file("config.json")
        if "ai_config" not in cfg: cfg["ai_config"] = {}
        cfg["ai_config"]["ai_first_run"] = False
        self.controller._save_json_file("config.json", cfg)
        
        self.controller.reload_all_ai_files()
        self.controller.send_to_bot('IPC>>{"type": "command", "name": "reload"}')
        self.controller.open_ai_menu()