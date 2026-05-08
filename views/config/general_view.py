import customtkinter as ctk
import os
import sys
import re
import json
from dotenv import set_key, dotenv_values
from tkinter import messagebox
from tkinter.colorchooser import askcolor

from views.guides.discord_guide_view import DiscordGuideView
from views.guides.id_guide_view import IdGuideView

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
ENV_PATH = os.path.join(SETTINGS_DIR, ".env")

class GeneralConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text=self.controller.lang_manager.get("cfg_gen_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=16, border_width=1, border_color=self.controller.theme_manager.get("border"))
        card.pack(fill="x", padx=20, pady=10)

        # Cargar datos actuales
        config_data = self.controller._load_json_file("config.json")
        outputs_filename = f"locales/outputs_{self.controller.lang_code}.json"
        outputs_data = self.controller._load_json_file(outputs_filename) or {}
        env_data = dotenv_values(ENV_PATH)

        self.general_entries = {}

        def add_gen_row(label, key, source, help_txt, is_password=False):
            # Wrapper: Mantiene la fila y su ayuda juntas
            wrapper = ctk.CTkFrame(card, fg_color="transparent")
            wrapper.pack(fill="x", pady=0)

            row = ctk.CTkFrame(wrapper, fg_color="transparent")
            row.pack(fill="x", pady=8, padx=15)
            ctk.CTkLabel(row, text=label, width=150, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
            
            entry = ctk.CTkEntry(row, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), show="*" if is_password else "")
            entry.pack(side="left", fill="x", expand=True, padx=(10, 10))
            
            # Valor inicial según origen
            val = ""
            if source == "config": val = config_data.get(key, "")
            elif source == "outputs": val = outputs_data.get(key, "")
            elif source == "env": val = env_data.get(key, "")
            
            entry.insert(0, str(val))
            self.general_entries[key] = (entry, source)
            
            # Contenedor de ayuda (se oculta/muestra)
            if help_txt:
                help_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
                
                ctk.CTkLabel(help_frame, text=f"ℹ {help_txt}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
                
                # Enlace a guía de IDs si corresponde
                if key in ["ADMIN_ID", "WELCOME_CHANNEL_ID", "MUSIC_CHANNEL_ID", "DISCORD_TOKEN"]:
                    guide_target = DiscordGuideView if key == "DISCORD_TOKEN" else IdGuideView
                    link_btn = ctk.CTkButton(help_frame, text=self.controller.lang_manager.get("cfg_gen_link_get_id"), width=90, height=20, fg_color="transparent", text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(size=11, underline=True), hover=False, command=lambda tgt=guide_target: self.controller.show_frame(tgt))
                    link_btn.configure(hover_color=self.controller.theme_manager.get("bg_card"))
                    link_btn.pack(side="left", padx=5)

                ctk.CTkButton(row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x", padx=165)).pack(side="right")

        def add_option_row(label, key, source, options, help_txt):
            wrapper = ctk.CTkFrame(card, fg_color="transparent")
            wrapper.pack(fill="x", pady=0)

            row = ctk.CTkFrame(wrapper, fg_color="transparent")
            row.pack(fill="x", pady=8, padx=15)
            ctk.CTkLabel(row, text=label, width=150, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
            
            combo = ctk.CTkComboBox(row, values=options, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"))
            combo.pack(side="left", fill="x", expand=True, padx=(10, 10))
            
            val = ""
            if source == "config": val = config_data.get(key, options[0])
            elif source == "outputs": val = outputs_data.get(key, options[0])
            elif source == "env": val = env_data.get(key, options[0])
            
            combo.set(str(val))
            self.general_entries[key] = (combo, source)
            
            if help_txt:
                help_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
                ctk.CTkLabel(help_frame, text=f"ℹ {help_txt}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
                ctk.CTkButton(row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x", padx=165)).pack(side="right")

        theme_dir = os.path.join(BASE_DIR, "themes")
        available_themes = [f.replace('.json', '') for f in os.listdir(theme_dir) if f.endswith('.json')]
        if "dark" not in available_themes: available_themes.insert(0, "dark")
        
        add_option_row(self.controller.lang_manager.get("cfg_gen_language", "Idioma / Language"), "language", "config", ["es", "en"], self.controller.lang_manager.get("cfg_gen_help_language"))
        
        # Fila Especial: Tema Visual y Botón Personalizar
        theme_wrapper = ctk.CTkFrame(card, fg_color="transparent")
        theme_wrapper.pack(fill="x", pady=0)

        theme_row = ctk.CTkFrame(theme_wrapper, fg_color="transparent")
        theme_row.pack(fill="x", pady=8, padx=15)
        ctk.CTkLabel(theme_row, text=self.controller.lang_manager.get("cfg_gen_theme", "Tema Visual"), width=150, anchor="w", text_color=self.controller.theme_manager.get("text")).pack(side="left")
        
        self.combo_theme = ctk.CTkComboBox(theme_row, values=available_themes, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("text"))
        self.combo_theme.pack(side="left", fill="x", expand=True, padx=(10, 10))
        
        btn_personalizar = ctk.CTkButton(theme_row, text=self.controller.lang_manager.get("cfg_gen_theme_editor", "Personalizar Tema"), width=180, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), border_width=1, border_color=self.controller.theme_manager.get("border"), command=self.open_theme_editor)
        btn_personalizar.pack(side="left")
        
        self.combo_theme.set(str(config_data.get("theme", "dark")))
        self.general_entries["theme"] = (self.combo_theme, "config")
        
        if self.controller.lang_manager.get("cfg_gen_help_theme"):
            theme_help = ctk.CTkFrame(theme_wrapper, fg_color="transparent")
            ctk.CTkLabel(theme_help, text=f"ℹ {self.controller.lang_manager.get('cfg_gen_help_theme')}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
            ctk.CTkButton(theme_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=theme_help: self.controller.toggle_help(h, "pack", fill="x", padx=165)).pack(side="right", padx=(10,0))

        add_gen_row(self.controller.lang_manager.get("cfg_gen_token"), "DISCORD_TOKEN", "env", self.controller.lang_manager.get("cfg_gen_help_token"), is_password=True)
        add_gen_row(self.controller.lang_manager.get("cfg_gen_prefix"), "prefix", "config", self.controller.lang_manager.get("cfg_gen_help_prefix"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_admin_id"), "ADMIN_ID", "env", self.controller.lang_manager.get("cfg_gen_help_admin"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_welcome_id"), "WELCOME_CHANNEL_ID", "env", self.controller.lang_manager.get("cfg_gen_help_welcome"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_music_id", "Canal Música ID"), "MUSIC_CHANNEL_ID", "env", self.controller.lang_manager.get("cfg_gen_help_music_id", "Opcional"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_welcome_msg"), "welcome_message", "outputs", self.controller.lang_manager.get("cfg_gen_help_welcome_msg"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_leave_msg"), "disconnected", "outputs", self.controller.lang_manager.get("cfg_gen_help_leave_msg"))
        add_gen_row(self.controller.lang_manager.get("cfg_gen_timeout_msg"), "timeout_msg", "outputs", self.controller.lang_manager.get("cfg_gen_help_timeout_msg"))

        ctk.CTkButton(scroll, text=self.controller.lang_manager.get("btn_save"), command=self.save_general_config, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), height=40, corner_radius=10).pack(pady=(20, 5))
        self.lbl_status_general = ctk.CTkLabel(scroll, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_status_general.pack(pady=(0, 20))

    def open_theme_editor(self):
        editor = ThemeEditorWindow(self, self.controller, self.combo_theme)
        editor.grab_set()
        editor.focus_force()

    def save_general_config(self):
        # Cargar frescos
        old_cfg = self.controller._load_json_file("config.json")
        old_lang = old_cfg.get("language", "es")
        old_theme = old_cfg.get("theme", "dark")
        
        cfg = old_cfg.copy()
        outputs_filename = f"locales/outputs_{self.controller.lang_code}.json"
        out = self.controller._load_json_file(outputs_filename) or {}

        for key, (entry, source) in self.general_entries.items():
            val = entry.get()
            if isinstance(val, str): val = val.strip()
            if source == "config": cfg[key] = val
            elif source == "outputs": out[key] = val
            elif source == "env": set_key(ENV_PATH, key, val) # Escribe directo a disco

        self.controller._save_json_file("config.json", cfg)
        self.controller._save_json_file(outputs_filename, out)
        
        if cfg.get("language", "es") != old_lang or cfg.get("theme", "dark") != old_theme:
            messagebox.showinfo(
                self.controller.lang_manager.get("msg_restart_title", "Reinicio Requerido"),
                self.controller.lang_manager.get("msg_restart_theme", "Has cambiado el idioma o el tema. Por favor, reinicia la aplicación para aplicar todos los cambios correctamente.")
            )
            
        self.lbl_status_general.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
        self.after(3000, lambda: self.lbl_status_general.configure(text=""))


class ThemeEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent, controller, combo_theme):
        super().__init__(parent)
        self.controller = controller
        self.combo_theme = combo_theme
        self.title("Creador de Tema Personalizado")
        self.geometry("1280x720")
        
        # Centrar la ventana respecto al Launcher principal
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (1280 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (720 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.current_colors = self.controller.theme_manager.colors.copy()
        self.highlight_key = None
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)
        
        self.left_panel = ctk.CTkFrame(self, fg_color=self.current_colors.get("bg_card"))
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.right_panel = ctk.CTkFrame(self, fg_color=self.current_colors.get("bg_dark"))
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.build_left_panel()
        self.build_preview_panel()
        self.update_preview()
        
    def build_left_panel(self):
        ctk.CTkLabel(self.left_panel, text="Creador de Tema", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.current_colors.get("accent")).pack(pady=(20, 10))
        
        bg_dark = self.current_colors.get("bg_dark")
        border = self.current_colors.get("border")
        text = self.current_colors.get("text")
        
        name_row = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        name_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(name_row, text="Nombre del Tema:", anchor="w").pack(side="top", fill="x")
        self.entry_name = ctk.CTkEntry(name_row, placeholder_text="ej: mi_tema", fg_color=bg_dark, border_color=border, text_color=text)
        self.entry_name.pack(side="top", fill="x", pady=5)
        
        self.scroll = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.entries = {}
        self.color_boxes = {}
        theme_keys = ["bg_dark", "bg_sidebar", "bg_card", "accent", "accent_dim", "border", "text", "text_dim", "green", "red"]
        
        for key in theme_keys:
            row = ctk.CTkFrame(self.scroll, fg_color=self.current_colors.get("bg_card"))
            row.pack(fill="x", pady=2)
            
            lbl = ctk.CTkLabel(row, text=key, width=90, anchor="w")
            lbl.pack(side="left")
            
            ent = ctk.CTkEntry(row, width=100, fg_color=bg_dark, border_color=border, text_color=text)
            ent.pack(side="left", fill="x", expand=True, padx=5)
            ent.insert(0, self.current_colors.get(key, "#000000"))
            ent.bind("<KeyRelease>", lambda e, k=key, entry=ent: self.on_color_change(k, entry.get()))
            
            self.entries[key] = ent
            
            color_box = ctk.CTkFrame(row, width=25, height=25, fg_color=self.current_colors.get(key, "#000000"), border_width=1, border_color=border)
            color_box.pack(side="left", padx=5)
            self.color_boxes[key] = color_box
            
            btn_pick = ctk.CTkButton(row, text="🎨", width=30, fg_color=bg_dark, text_color=text, hover_color=border, command=lambda k=key, entry=ent: self.pick_color(k, entry))
            btn_pick.pack(side="left")
            
            # Enlaza los eventos de Hover (Ratón encima) para el resaltado
            for widget in (row, lbl, ent, color_box, btn_pick):
                widget.bind("<Enter>", lambda e, k=key: [setattr(self, 'highlight_key', k), self.update_preview()])
                widget.bind("<Leave>", lambda e, k=key: [setattr(self, 'highlight_key', None), self.update_preview()] if getattr(self, 'highlight_key', None) == k else None)
            
        ctk.CTkButton(self.left_panel, text="💾 Guardar Tema", command=self.save_theme, fg_color=self.current_colors.get("accent"), hover_color=self.current_colors.get("accent_dim"), text_color=self.current_colors.get("bg_dark"), height=40, font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=20, fill="x")

    def pick_color(self, key, entry):
        initial = entry.get()
        color = askcolor(initialcolor=initial, title=f"Elige color para {key}", parent=self)
        if color[1]:
            entry.delete(0, 'end')
            entry.insert(0, color[1])
            self.on_color_change(key, color[1])
            
    def on_color_change(self, key, hex_val):
        if re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", hex_val):
            self.current_colors[key] = hex_val
            if key in self.color_boxes:
                self.color_boxes[key].configure(fg_color=hex_val)
            self.update_preview()
            
    def build_preview_panel(self):
        # Emulamos la estructura de la aplicación principal
        self.prev_sidebar = ctk.CTkFrame(self.right_panel, width=220, corner_radius=0)
        self.prev_sidebar.pack(side="left", fill="y")
        self.prev_sidebar.pack_propagate(False)
        
        self.prev_content = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.prev_content.pack(side="left", fill="both", expand=True, padx=30, pady=30)
        
        # --- Sidebar Preview ---
        self.prev_sb_logo = ctk.CTkLabel(self.prev_sidebar, text="🐱", font=ctk.CTkFont(size=40))
        self.prev_sb_logo.pack(pady=(30, 5))
        
        self.prev_sb_title = ctk.CTkLabel(self.prev_sidebar, text="MeowSick", font=ctk.CTkFont(size=20, weight="bold"))
        self.prev_sb_title.pack(pady=(0, 30))
        
        self.prev_sb_btn1 = ctk.CTkButton(self.prev_sidebar, text="Dashboard", height=36, corner_radius=8, anchor="w", hover=False)
        self.prev_sb_btn1.pack(pady=6, padx=16, fill="x")
        
        self.prev_sb_btn2 = ctk.CTkButton(self.prev_sidebar, text="Configuración", height=36, corner_radius=8, anchor="w", hover=False)
        self.prev_sb_btn2.pack(pady=6, padx=16, fill="x")
        
        self.prev_sb_sep = ctk.CTkFrame(self.prev_sidebar, height=2)
        self.prev_sb_sep.pack(fill="x", padx=20, pady=10)
        
        self.prev_sb_text = ctk.CTkLabel(self.prev_sidebar, text="v3.0.0 Estable", font=ctk.CTkFont(size=11))
        self.prev_sb_text.pack(side="bottom", pady=20)
        
        # --- Content Preview ---
        self.prev_title = ctk.CTkLabel(self.prev_content, text="Previsualización de Tema", font=ctk.CTkFont(size=20, weight="bold"))
        self.prev_title.pack(anchor="w", pady=(0, 15))
        
        self.prev_scroll = ctk.CTkScrollableFrame(self.prev_content, fg_color="transparent")
        self.prev_scroll.pack(fill="both", expand=True)
        
        self.prev_card = ctk.CTkFrame(self.prev_scroll, corner_radius=16, border_width=1)
        self.prev_card.pack(fill="x", pady=10)
        
        row1 = ctk.CTkFrame(self.prev_card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=15)
        self.prev_lbl_normal = ctk.CTkLabel(row1, text="Opción de Configuración Múltiple", font=ctk.CTkFont(weight="bold"))
        self.prev_lbl_normal.pack(side="left")
        
        self.prev_entry = ctk.CTkEntry(row1, placeholder_text="Caja de texto...")
        self.prev_entry.pack(side="right", fill="x", expand=True, padx=(20, 0))
        
        row2 = ctk.CTkFrame(self.prev_card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 10))
        self.prev_lbl_dim = ctk.CTkLabel(row2, text="ℹ Esta es una descripción secundaria atada a la variable (text_dim).", font=ctk.CTkFont(size=11))
        self.prev_lbl_dim.pack(side="left")
        
        row3 = ctk.CTkFrame(self.prev_card, fg_color="transparent")
        row3.pack(fill="x", padx=20, pady=(10, 15))
        self.prev_switch = ctk.CTkSwitch(row3, text="Interruptor de Módulo", onvalue=True, offvalue=False)
        self.prev_switch.pack(side="left", padx=(0, 20))
        self.prev_switch.select()
        self.prev_chk = ctk.CTkCheckBox(row3, text="Opción Peligrosa", onvalue=True, offvalue=False)
        self.prev_chk.pack(side="left")
        self.prev_chk.select()

        row4 = ctk.CTkFrame(self.prev_card, fg_color="transparent")
        row4.pack(fill="x", padx=20, pady=(0, 15))
        self.prev_combo = ctk.CTkComboBox(row4, values=["Opción Desplegable", "Segunda Opción"])
        self.prev_combo.pack(side="left", fill="x", expand=True)

        self.prev_textbox = ctk.CTkTextbox(self.prev_card, height=60, border_width=1)
        self.prev_textbox.pack(fill="x", padx=20, pady=(0, 15))
        self.prev_textbox.insert("0.0", "Esto simula los registros o la consola de texto masivo (Consolas 10).")
        self.prev_textbox.configure(state="disabled")
        
        # Botones y estados
        actions_frame = ctk.CTkFrame(self.prev_scroll, fg_color="transparent")
        actions_frame.pack(fill="x", pady=20)
        
        self.prev_btn_accent = ctk.CTkButton(actions_frame, text="Botón Principal de Acción", height=40, corner_radius=10, hover=False)
        self.prev_btn_accent.pack(side="left", padx=(0, 10))
        
        self.prev_lbl_green = ctk.CTkLabel(actions_frame, text="✓ Guardado correctamente (green)", font=ctk.CTkFont(weight="bold"))
        self.prev_lbl_green.pack(side="left", padx=10)
        
        self.prev_lbl_red = ctk.CTkLabel(actions_frame, text="⚠️ Error del sistema (red)", font=ctk.CTkFont(weight="bold"))
        self.prev_lbl_red.pack(side="left", padx=10)

    def update_preview(self):
        def c(k):
            val = str(self.current_colors.get(k, "#000000"))
            if getattr(self, 'highlight_key', None) == k:
                try:
                    h = val.lstrip('#')
                    if len(h) == 6:
                        r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                        inv_r, inv_g, inv_b = 255 - r, 255 - g, 255 - b
                        # Si es un gris medio y la inversión no genera contraste, forzar Blanco o Negro
                        if abs(r - inv_r) < 30 and abs(g - inv_g) < 30 and abs(b - inv_b) < 30:
                            return "#FFFFFF" if (r * 0.299 + g * 0.587 + b * 0.114) < 128 else "#000000"
                        return f"#{inv_r:02X}{inv_g:02X}{inv_b:02X}"
                except Exception:
                    pass
                return "#FFFFFF"
            return val
            
        try:
            self.right_panel.configure(fg_color=c("bg_dark"))
            
            # --- Simulated Sidebar Updates ---
            self.prev_sidebar.configure(fg_color=c("bg_sidebar"))
            self.prev_sb_logo.configure(text_color=c("text_dim"))
            self.prev_sb_title.configure(text_color=c("accent"))
            self.prev_sb_text.configure(text_color=c("text_dim"))
            self.prev_sb_sep.configure(fg_color=c("border"))
            
            sb_btn_args = {"fg_color": c("bg_card"), "text_color": c("text")}
            self.prev_sb_btn1.configure(**sb_btn_args)
            self.prev_sb_btn2.configure(**sb_btn_args)
            
            self.prev_title.configure(text_color=c("accent"))
            self.prev_card.configure(fg_color=c("bg_card"), border_color=c("border"))
            self.prev_lbl_normal.configure(text_color=c("text"))
            self.prev_lbl_dim.configure(text_color=c("text_dim"))
            self.prev_entry.configure(fg_color=c("bg_dark"), border_color=c("border"), text_color=c("text"))
            
            self.prev_switch.configure(progress_color=c("accent"), text_color=c("text"))
            self.prev_chk.configure(fg_color=c("red"), hover_color=c("accent_dim"), text_color=c("text"))
            self.prev_combo.configure(fg_color=c("bg_dark"), border_color=c("border"), dropdown_fg_color=c("bg_card"), text_color=c("text"), button_color=c("accent"), button_hover_color=c("accent_dim"))
            self.prev_textbox.configure(fg_color=c("bg_dark"), border_color=c("border"), text_color=c("text"))
            
            if getattr(self, 'highlight_key', None) == "accent_dim":
                self.prev_btn_accent.configure(fg_color=c("accent_dim"))
            else:
                self.prev_btn_accent.configure(fg_color=c("accent"))
                
            self.prev_btn_accent.configure(text_color=c("bg_dark"))
            self.prev_lbl_green.configure(text_color=c("green"))
            self.prev_lbl_red.configure(text_color=c("red"))
            
        except Exception: pass

    def save_theme(self):
        theme_name = self.entry_name.get().strip().lower()
        if not theme_name:
            messagebox.showerror("Error", "Debes ingresar un nombre para el tema nuevo.", parent=self)
            return
            
        valid_chars = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
        if not all(ch in valid_chars for ch in theme_name):
            messagebox.showerror("Error", "El nombre del tema solo debe contener letras, números, guiones bajos (_) o medios (-).", parent=self)
            return
            
        if theme_name in ["dark", "light", "midnight"]:
            messagebox.showerror("Error", "No puedes sobrescribir los temas base nativos.", parent=self)
            return
            
        theme_dir = os.path.join(BASE_DIR, "themes")
        theme_path = os.path.join(theme_dir, f"{theme_name}.json")
        if os.path.exists(theme_path):
            messagebox.showerror("Error", f"El tema '{theme_name}' ya existe. Por favor, elige otro nombre.", parent=self)
            return
            
        hex_pattern = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
        custom_theme_to_save = {}
        for key, entry in self.entries.items():
            val = entry.get().strip()
            if not val or not hex_pattern.match(val):
                messagebox.showerror("Error", f"Color HEX inválido para {key}: {val}", parent=self)
                return
            custom_theme_to_save[key] = val
            
        with open(theme_path, "w", encoding="utf-8") as f:
            json.dump(custom_theme_to_save, f, indent=4)
            
        available_themes = [f.replace('.json', '') for f in os.listdir(theme_dir) if f.endswith('.json')]
        if "dark" not in available_themes: available_themes.insert(0, "dark")
        self.combo_theme.configure(values=available_themes)
        self.combo_theme.set(theme_name)
        
        messagebox.showinfo("Éxito", f"Tema '{theme_name}' creado correctamente.\n\nSe ha autoseleccionado en la lista. Guarda los ajustes y reinicia la aplicación para aplicarlo a toda la interfaz.", parent=self)
        self.destroy()