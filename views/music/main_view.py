import customtkinter as ctk
from views.config.music_view import MusicConfigFrame

class MusicFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        # Ajuste de pesos: La cola (row 5) se expande, la consola (row 7) se queda fija
        self.grid_rowconfigure(5, weight=1) 

        # 1. Header y Toggle
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(header, text=self.controller.lang_manager.get("mus_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        # Botón para activar/desactivar módulo (Sincronizado)
        self.controller.btn_music_toggle = ctk.CTkButton(header, text="...", width=120, height=30, command=lambda: self.controller.toggle_module("music", self.controller.btn_music_toggle))
        self.controller.btn_music_toggle.pack(side="right")
        
        btn_music_config = ctk.CTkButton(header, text="⚙", width=30, height=30, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda: (self.controller.open_config_menu(), self.controller.show_frame(MusicConfigFrame)))
        btn_music_config.pack(side="right", padx=(0, 10))
        
        if "music" not in self.controller.module_buttons: self.controller.module_buttons["music"] = []
        self.controller.module_buttons["music"].append(self.controller.btn_music_toggle)
        self.controller.update_module_state("music", self.controller.btn_music_toggle)

        # 2. Área de Input
        input_frame = ctk.CTkFrame(self, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.controller.music_entry = ctk.CTkEntry(input_frame, placeholder_text=self.controller.lang_manager.get("mus_entry_placeholder"), height=35)
        self.controller.music_entry.pack(side="left", fill="x", expand=True, padx=15, pady=15)
        
        ctk.CTkButton(input_frame, text=self.controller.lang_manager.get("mus_btn_play"), width=100, height=35, fg_color=self.controller.theme_manager.get("green"), text_color=self.controller.theme_manager.get("bg_dark"), hover_color="#89b458", command=lambda: self.controller.send_music_cmd("play")).pack(side="right", padx=15)

        # 3. Botones de Control (Cuadrícula completa)
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        
        def mk_btn(parent, txt, cmd, col=None, txt_col=None, hover=None):
            col = col or self.controller.theme_manager.get("bg_card")
            txt_col = txt_col or self.controller.theme_manager.get("text")
            hover = hover or self.controller.theme_manager.get("border")
            # Se usa c=cmd en el lambda para capturar el valor actual (late binding fix)
            return ctk.CTkButton(parent, text=txt, command=lambda c=cmd: self.controller.send_music_cmd(c), fg_color=col, text_color=txt_col, hover_color=hover, width=80, height=30)

        # Fila 1
        r1 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        r1.pack(fill="x", pady=3)
        mk_btn(r1, self.controller.lang_manager.get("mus_btn_pause"), "pause").pack(side="left", padx=(0, 5), expand=True, fill="x")
        mk_btn(r1, self.controller.lang_manager.get("mus_btn_resume"), "resume").pack(side="left", padx=(0, 5), expand=True, fill="x")
        mk_btn(r1, self.controller.lang_manager.get("mus_btn_stop"), "stop", col=self.controller.theme_manager.get("bg_dark"), txt_col=self.controller.theme_manager.get("red"), hover="#333333").pack(side="left", padx=(0, 5), expand=True, fill="x")
        mk_btn(r1, self.controller.lang_manager.get("mus_btn_leave"), "leave", col=self.controller.theme_manager.get("bg_dark"), txt_col=self.controller.theme_manager.get("red"), hover="#333333").pack(side="left", expand=True, fill="x")

        # Fila 2
        r2 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        r2.pack(fill="x", pady=3)
        mk_btn(r2, self.controller.lang_manager.get("mus_btn_skip"), "skip").pack(side="left", padx=(0, 5), expand=True, fill="x")
        mk_btn(r2, self.controller.lang_manager.get("mus_btn_next"), "next").pack(side="left", padx=(0, 5), expand=True, fill="x")
        mk_btn(r2, self.controller.lang_manager.get("mus_btn_shuffle"), "shuffle").pack(side="left", padx=(0, 5), expand=True, fill="x")
        mk_btn(r2, self.controller.lang_manager.get("mus_btn_playlist"), "pls").pack(side="left", expand=True, fill="x")

        # 4. Now Playing (Actualizado dinámicamente)
        self.controller.lbl_now_playing = ctk.CTkLabel(self, text=self.controller.lang_manager.get("mus_lbl_now_playing_empty"), font=ctk.CTkFont(size=13, weight="bold"), text_color=self.controller.theme_manager.get("accent"), anchor="w")
        self.controller.lbl_now_playing.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 5))

        # 5. Lista de Cola (Expandida)
        ctk.CTkLabel(self, text=self.controller.lang_manager.get("mus_lbl_queue"), text_color=self.controller.theme_manager.get("text_dim"), anchor="w", font=ctk.CTkFont(size=12, weight="bold")).grid(row=4, column=0, sticky="ew", padx=5, pady=(5, 2))
        
        self.controller.queue_display = ctk.CTkTextbox(self, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_sidebar"), text_color=self.controller.theme_manager.get("text"), corner_radius=8, border_width=1, border_color=self.controller.theme_manager.get("border"))
        self.controller.queue_display.grid(row=5, column=0, sticky="nsew", pady=(0, 10))
        self.controller.queue_display.configure(state="disabled")

        # 6. Consola Filtrada (Pequeña abajo)
        ctk.CTkLabel(self, text=self.controller.lang_manager.get("mus_term_title"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(family="Consolas", size=11), anchor="w").grid(row=6, column=0, sticky="ew", padx=5, pady=(0,2))
        self.controller.console_music = ctk.CTkTextbox(self, font=("Consolas", 10), height=80, fg_color=self.controller.theme_manager.get("bg_card"), text_color=self.controller.theme_manager.get("accent"), border_width=1, border_color=self.controller.theme_manager.get("border"), corner_radius=8)
        self.controller.console_music.grid(row=7, column=0, sticky="ew", pady=(0, 5))
        self.controller.console_music.configure(state="disabled")