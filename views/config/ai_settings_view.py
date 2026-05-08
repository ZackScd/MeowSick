import customtkinter as ctk
import os
import sys
from dotenv import set_key, dotenv_values

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
ENV_PATH = os.path.join(SETTINGS_DIR, ".env")

class AISettingsConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text=self.controller.lang_manager.get("cfg_ais_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Sección 1: Filtros
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ais_sec_filters"), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        filt_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        filt_card.pack(fill="x", padx=20, pady=5)

        f_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        f_row.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(f_row, text=self.controller.lang_manager.get("cfg_ais_wl_channels"), text_color=self.controller.theme_manager.get("text")).pack(anchor="w", pady=(0, 5))
        
        self.entry_ai_channels = ctk.CTkEntry(f_row, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), placeholder_text=self.controller.lang_manager.get("cfg_ais_wl_ph"))
        self.entry_ai_channels.pack(fill="x")
        ctk.CTkLabel(f_row, text=self.controller.lang_manager.get("cfg_ais_wl_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(anchor="w", pady=(5,0))

        cw_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        cw_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(cw_row, text=self.controller.lang_manager.get("cfg_ais_ctx"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ai_context = ctk.CTkEntry(cw_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ai_context.pack(side="left", padx=10)
        ctk.CTkLabel(cw_row, text=self.controller.lang_manager.get("cfg_ais_ctx_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        mh_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        mh_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(mh_row, text=self.controller.lang_manager.get("cfg_ais_mood_hist"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ai_mood_hist = ctk.CTkEntry(mh_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ai_mood_hist.pack(side="left", padx=10)
        ctk.CTkLabel(mh_row, text=self.controller.lang_manager.get("cfg_ais_mood_hist_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        mb_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        mb_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(mb_row, text=self.controller.lang_manager.get("cfg_ais_mem_buf"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ai_mem_buffer = ctk.CTkEntry(mb_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ai_mem_buffer.pack(side="left", padx=10)
        ctk.CTkLabel(mb_row, text=self.controller.lang_manager.get("cfg_ais_mem_buf_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        il_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        il_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(il_row, text=self.controller.lang_manager.get("cfg_ais_img_limit"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ai_image_limit = ctk.CTkEntry(il_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ai_image_limit.pack(side="left", padx=10)
        ctk.CTkLabel(il_row, text=self.controller.lang_manager.get("cfg_ais_img_limit_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        vl_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        vl_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(vl_row, text=self.controller.lang_manager.get("cfg_ais_vis_look"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ai_vision_lookback = ctk.CTkEntry(vl_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ai_vision_lookback.pack(side="left", padx=10)
        ctk.CTkLabel(vl_row, text=self.controller.lang_manager.get("cfg_ais_vis_look_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        eb_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        eb_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(eb_row, text=self.controller.lang_manager.get("cfg_ais_mood_buf"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ai_mood_buffer = ctk.CTkEntry(eb_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ai_mood_buffer.pack(side="left", padx=10)
        ctk.CTkLabel(eb_row, text=self.controller.lang_manager.get("cfg_ais_mood_buf_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        dh_row = ctk.CTkFrame(filt_card, fg_color="transparent")
        dh_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(dh_row, text=self.controller.lang_manager.get("cfg_ais_decay"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_ai_decay_hours = ctk.CTkEntry(dh_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_ai_decay_hours.pack(side="left", padx=10)
        ctk.CTkLabel(dh_row, text=self.controller.lang_manager.get("cfg_ais_decay_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        # Sección 2: Módulo de Voz (TTS)
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ais_sec_tts"), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        tts_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        tts_card.pack(fill="x", padx=20, pady=5)

        te_row = ctk.CTkFrame(tts_card, fg_color="transparent")
        te_row.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(te_row, text=self.controller.lang_manager.get("cfg_ais_tts_engine"), text_color=self.controller.theme_manager.get("text"), width=130, anchor="w").pack(side="left")
        self.combo_ai_tts_engine = ctk.CTkComboBox(te_row, width=220, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"), values=["nube_edge", "local_piper"])
        self.combo_ai_tts_engine.pack(side="left", padx=10)
        
        help_tts = ctk.CTkFrame(tts_card, fg_color="transparent")
        ctk.CTkLabel(help_tts, text=f"ℹ {self.controller.lang_manager.get('cfg_ais_tts_engine_desc')}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), justify="left").pack(side="left")
        ctk.CTkButton(te_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_tts: self.controller.toggle_help(h, "pack", fill="x", padx=15, pady=(0, 10))).pack(side="right")

        tv_voice = ctk.CTkFrame(tts_card, fg_color="transparent")
        tv_voice.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(tv_voice, text=self.controller.lang_manager.get("cfg_ais_tts_voice"), text_color=self.controller.theme_manager.get("text"), width=130, anchor="w").pack(side="left")
        self.combo_ai_tts_voice = ctk.CTkComboBox(tv_voice, width=220, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"), values=["es-MX-DaliaNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural", "es-ES-ElviraNeural"])
        self.combo_ai_tts_voice.pack(side="left", padx=10)
        ctk.CTkLabel(tv_voice, text=self.controller.lang_manager.get("cfg_ais_tts_voice_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        rvc_row = ctk.CTkFrame(tts_card, fg_color="transparent")
        rvc_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(rvc_row, text=self.controller.lang_manager.get("cfg_ais_tts_rvc"), text_color=self.controller.theme_manager.get("text"), width=130, anchor="w").pack(side="left")
        self.switch_tts_rvc = ctk.CTkSwitch(rvc_row, text=self.controller.lang_manager.get("cfg_ais_tts_rvc_sw"), font=ctk.CTkFont(size=11), onvalue=True, offvalue=False, progress_color=self.controller.theme_manager.get("accent"))
        self.switch_tts_rvc.pack(side="left", padx=10)
        
        help_rvc = ctk.CTkFrame(tts_card, fg_color="transparent")
        ctk.CTkLabel(help_rvc, text=f"ℹ {self.controller.lang_manager.get('cfg_ais_tts_rvc_desc')}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), justify="left").pack(side="left")
        ctk.CTkButton(rvc_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_rvc: self.controller.toggle_help(h, "pack", fill="x", padx=15, pady=(0, 10))).pack(side="right")

        st_row = ctk.CTkFrame(tts_card, fg_color="transparent")
        st_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(st_row, text=self.controller.lang_manager.get("cfg_ais_tts_text"), text_color=self.controller.theme_manager.get("text"), width=130, anchor="w").pack(side="left")
        self.switch_tts_text = ctk.CTkSwitch(st_row, text=self.controller.lang_manager.get("cfg_ais_tts_text_sw"), font=ctk.CTkFont(size=11), onvalue=True, offvalue=False, progress_color=self.controller.theme_manager.get("accent"))
        self.switch_tts_text.pack(side="left", padx=10)

        # Sección 3: Búsqueda Web
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ais_sec_web"), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x", padx=20, pady=(15, 5))
        web_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        web_card.pack(fill="x", padx=20, pady=5)

        wm_row = ctk.CTkFrame(web_card, fg_color="transparent")
        wm_row.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(wm_row, text=self.controller.lang_manager.get("cfg_ais_web_engine"), text_color=self.controller.theme_manager.get("text"), width=130, anchor="w").pack(side="left")
        self.combo_web_method = ctk.CTkComboBox(wm_row, width=220, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), dropdown_fg_color=self.controller.theme_manager.get("bg_card"), values=["google", "ddg"])
        self.combo_web_method.pack(side="left", padx=10)
        
        help_web = ctk.CTkFrame(web_card, fg_color="transparent")
        ctk.CTkLabel(help_web, text=f"ℹ {self.controller.lang_manager.get('cfg_ais_web_engine_desc')}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), justify="left").pack(side="left")
        ctk.CTkButton(wm_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_web: self.controller.toggle_help(h, "pack", fill="x", padx=15, pady=(0, 10))).pack(side="right")
        
        aw_row = ctk.CTkFrame(web_card, fg_color="transparent")
        aw_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(aw_row, text=self.controller.lang_manager.get("cfg_ais_web_auto"), text_color=self.controller.theme_manager.get("text"), width=130, anchor="w").pack(side="left")
        self.switch_auto_web = ctk.CTkSwitch(aw_row, text=self.controller.lang_manager.get("cfg_ais_web_auto_sw"), font=ctk.CTkFont(size=11), onvalue=True, offvalue=False, progress_color=self.controller.theme_manager.get("accent"))
        self.switch_auto_web.pack(side="left", padx=10)

        wr_row = ctk.CTkFrame(web_card, fg_color="transparent")
        wr_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(wr_row, text=self.controller.lang_manager.get("cfg_ais_web_ddg"), text_color=self.controller.theme_manager.get("text"), width=130, anchor="w").pack(side="left")
        self.entry_web_results = ctk.CTkEntry(wr_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_web_results.pack(side="left", padx=10)
        ctk.CTkLabel(wr_row, text=self.controller.lang_manager.get("cfg_ais_web_ddg_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        # --- AÑADIDO: VALORES MÁGICOS (AVANZADO) ---
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ais_sec_adv"), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x", padx=20, pady=(15, 5))
        adv_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        adv_card.pack(fill="x", padx=20, pady=5)
        
        sp_row = ctk.CTkFrame(adv_card, fg_color="transparent")
        sp_row.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(sp_row, text=self.controller.lang_manager.get("cfg_ais_adv_spont"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_spontaneous_prob = ctk.CTkEntry(sp_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_spontaneous_prob.pack(side="left", padx=10)
        ctk.CTkLabel(sp_row, text=self.controller.lang_manager.get("cfg_ais_adv_spont_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")
        
        cd_row = ctk.CTkFrame(adv_card, fg_color="transparent")
        cd_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(cd_row, text=self.controller.lang_manager.get("cfg_ais_adv_cool"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_cooldown = ctk.CTkEntry(cd_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_cooldown.pack(side="left", padx=10)
        ctk.CTkLabel(cd_row, text=self.controller.lang_manager.get("cfg_ais_adv_cool_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        gl_row = ctk.CTkFrame(adv_card, fg_color="transparent")
        gl_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(gl_row, text=self.controller.lang_manager.get("cfg_ais_adv_gamer"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_gamer_limit = ctk.CTkEntry(gl_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_gamer_limit.pack(side="left", padx=10)
        ctk.CTkLabel(gl_row, text=self.controller.lang_manager.get("cfg_ais_adv_gamer_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        rp_row = ctk.CTkFrame(adv_card, fg_color="transparent")
        rp_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(rp_row, text=self.controller.lang_manager.get("cfg_ais_adv_rep"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_repeat_penalty = ctk.CTkEntry(rp_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_repeat_penalty.pack(side="left", padx=10)
        ctk.CTkLabel(rp_row, text=self.controller.lang_manager.get("cfg_ais_adv_rep_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        ct_row = ctk.CTkFrame(adv_card, fg_color="transparent")
        ct_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(ct_row, text=self.controller.lang_manager.get("cfg_ais_adv_timeout"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_client_timeout = ctk.CTkEntry(ct_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_client_timeout.pack(side="left", padx=10)
        ctk.CTkLabel(ct_row, text=self.controller.lang_manager.get("cfg_ais_adv_timeout_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        # Sección 4: Almacenamiento en disco
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_ais_sec_disk"), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        store_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        store_card.pack(fill="x", padx=20, pady=5)

        limit_row = ctk.CTkFrame(store_card, fg_color="transparent")
        limit_row.pack(fill="x", padx=15, pady=15)
        
        info_frame = ctk.CTkFrame(limit_row, fg_color="transparent")
        info_frame.pack(side="left", fill="both")
        ctk.CTkLabel(info_frame, text=self.controller.lang_manager.get("cfg_ais_disk_lim_title"), font=ctk.CTkFont(weight="bold"), text_color=self.controller.theme_manager.get("text"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=self.controller.lang_manager.get("cfg_ais_disk_lim_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim"), anchor="w").pack(anchor="w")

        self.switch_history_limit = ctk.CTkSwitch(limit_row, text="", onvalue=True, offvalue=False, progress_color=self.controller.theme_manager.get("accent"), command=self.toggle_history_limit_entry)
        self.switch_history_limit.pack(side="right")

        self.hl_entry_row = ctk.CTkFrame(store_card, fg_color="transparent")
        self.hl_entry_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(self.hl_entry_row, text=self.controller.lang_manager.get("cfg_ais_disk_max"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_history_limit_max = ctk.CTkEntry(self.hl_entry_row, width=60, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
        self.entry_history_limit_max.pack(side="left", padx=10)
        ctk.CTkLabel(self.hl_entry_row, text=self.controller.lang_manager.get("cfg_ais_disk_max_desc"), font=ctk.CTkFont(size=11), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")

        self.load_ai_settings_ui()

        bot_controls = ctk.CTkFrame(scroll, fg_color="transparent")
        bot_controls.pack(pady=(20, 5))
        ctk.CTkButton(bot_controls, text=self.controller.lang_manager.get("cfg_ais_btn_reset"), command=self.reset_ai_settings, fg_color="#331a20", hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("red"), height=40, corner_radius=10).pack(side="left", padx=10)
        ctk.CTkButton(bot_controls, text=self.controller.lang_manager.get("btn_save"), command=self.save_ai_settings, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), height=40, corner_radius=10).pack(side="left", padx=10)
        
        self.lbl_status_ai_settings = ctk.CTkLabel(scroll, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_status_ai_settings.pack(pady=(0, 20))

    def load_ai_settings_ui(self):
        cfg = self.controller._load_json_file("config.json")
        ai_cfg = cfg.get("ai_config", {})
        
        env = dotenv_values(ENV_PATH)
        self.entry_ai_channels.delete(0, "end")
        self.entry_ai_channels.insert(0, env.get("AI_TARGET_CHANNELS", ""))
        
        self.entry_ai_context.delete(0, "end")
        self.entry_ai_context.insert(0, str(ai_cfg.get("context_window", 15)))
        
        self.entry_ai_mood_hist.delete(0, "end")
        self.entry_ai_mood_hist.insert(0, str(ai_cfg.get("mood_history_limit", 10)))

        self.entry_ai_mem_buffer.delete(0, "end")
        self.entry_ai_mem_buffer.insert(0, str(ai_cfg.get("memory_buffer_limit", 5)))
        
        self.entry_ai_image_limit.delete(0, "end")
        self.entry_ai_image_limit.insert(0, str(ai_cfg.get("image_size_limit_mb", 8.0)))

        self.entry_ai_vision_lookback.delete(0, "end")
        self.entry_ai_vision_lookback.insert(0, str(ai_cfg.get("vision_lookback_limit", 10)))

        self.combo_ai_tts_voice.set(ai_cfg.get("tts_voice", "es-MX-DaliaNeural"))
        self.combo_ai_tts_engine.set(ai_cfg.get("tts_engine", "nube_edge"))
        
        if ai_cfg.get("tts_rvc", False): self.switch_tts_rvc.select()
        else: self.switch_tts_rvc.deselect()

        if ai_cfg.get("tts_send_text", True): self.switch_tts_text.select()
        else: self.switch_tts_text.deselect()

        self.combo_web_method.set(ai_cfg.get("web_search_method", "google"))
        
        if ai_cfg.get("auto_web_search", True): self.switch_auto_web.select()
        else: self.switch_auto_web.deselect()
        
        self.entry_web_results.delete(0, "end")
        self.entry_web_results.insert(0, str(ai_cfg.get("web_search_max_results", 3)))

        self.entry_spontaneous_prob.delete(0, "end")
        self.entry_spontaneous_prob.insert(0, str(ai_cfg.get("spontaneous_prob", 0.05)))
        
        self.entry_cooldown.delete(0, "end")
        self.entry_cooldown.insert(0, str(ai_cfg.get("cooldown", 3.0)))
        
        self.entry_gamer_limit.delete(0, "end")
        self.entry_gamer_limit.insert(0, str(ai_cfg.get("gamer_limit", 5)))
        
        self.entry_repeat_penalty.delete(0, "end")
        self.entry_repeat_penalty.insert(0, str(ai_cfg.get("repeat_penalty", 1.1)))
        
        self.entry_client_timeout.delete(0, "end")
        self.entry_client_timeout.insert(0, str(ai_cfg.get("client_timeout", 180)))

        self.entry_ai_mood_buffer.delete(0, "end")
        self.entry_ai_mood_buffer.insert(0, str(ai_cfg.get("mood_buffer_limit", 5)))
        
        self.entry_ai_decay_hours.delete(0, "end")
        self.entry_ai_decay_hours.insert(0, str(ai_cfg.get("mood_decay_hours", 2.0)))

        enable_limit = ai_cfg.get("enable_history_limit", True)
        if enable_limit: self.switch_history_limit.select()
        else: self.switch_history_limit.deselect()

        self.entry_history_limit_max.delete(0, "end")
        self.entry_history_limit_max.insert(0, str(ai_cfg.get("history_save_limit", 50)))
        self.toggle_history_limit_entry()

    def toggle_history_limit_entry(self):
        if self.switch_history_limit.get():
            self.entry_history_limit_max.configure(state="normal")
        else:
            self.entry_history_limit_max.configure(state="disabled")

    def save_ai_settings(self):
        cfg = self.controller._load_json_file("config.json")
        if "ai_config" not in cfg: cfg["ai_config"] = {}
        
        set_key(ENV_PATH, "AI_TARGET_CHANNELS", self.entry_ai_channels.get().strip())
        
        try: cfg["ai_config"]["spontaneous_prob"] = float(self.entry_spontaneous_prob.get().strip())
        except ValueError: cfg["ai_config"]["spontaneous_prob"] = 0.05
        
        try: cfg["ai_config"]["cooldown"] = float(self.entry_cooldown.get().strip())
        except ValueError: cfg["ai_config"]["cooldown"] = 3.0
        
        try: cfg["ai_config"]["gamer_limit"] = int(self.entry_gamer_limit.get().strip())
        except ValueError: cfg["ai_config"]["gamer_limit"] = 5
        
        try: cfg["ai_config"]["repeat_penalty"] = float(self.entry_repeat_penalty.get().strip())
        except ValueError: cfg["ai_config"]["repeat_penalty"] = 1.1
        
        try: cfg["ai_config"]["client_timeout"] = int(self.entry_client_timeout.get().strip())
        except ValueError: cfg["ai_config"]["client_timeout"] = 180

        try:
            cw_val = int(self.entry_ai_context.get().strip())
        except ValueError:
            cw_val = 15
        cfg["ai_config"]["context_window"] = cw_val
        
        try:
            mh_val = int(self.entry_ai_mood_hist.get().strip())
        except ValueError:
            mh_val = 10
        cfg["ai_config"]["mood_history_limit"] = mh_val

        try:
            mb_val = int(self.entry_ai_mem_buffer.get().strip())
        except ValueError:
            mb_val = 5
        cfg["ai_config"]["memory_buffer_limit"] = mb_val
        
        try:
            il_val = float(self.entry_ai_image_limit.get().strip())
        except ValueError:
            il_val = 8.0
        cfg["ai_config"]["image_size_limit_mb"] = il_val

        try:
            vl_val = int(self.entry_ai_vision_lookback.get().strip())
        except ValueError:
            vl_val = 10
        cfg["ai_config"]["vision_lookback_limit"] = vl_val
        
        cfg["ai_config"]["tts_voice"] = self.combo_ai_tts_voice.get().strip() or "es-MX-DaliaNeural"
        cfg["ai_config"]["tts_engine"] = self.combo_ai_tts_engine.get().strip()
        cfg["ai_config"]["tts_rvc"] = bool(self.switch_tts_rvc.get())
        cfg["ai_config"]["tts_send_text"] = bool(self.switch_tts_text.get())
        
        cfg["ai_config"]["web_search_method"] = self.combo_web_method.get()
        cfg["ai_config"]["auto_web_search"] = bool(self.switch_auto_web.get())
        
        try:
            wrm_val = int(self.entry_web_results.get().strip())
        except ValueError:
            wrm_val = 3
        cfg["ai_config"]["web_search_max_results"] = wrm_val
        
        try:
            eb_val = int(self.entry_ai_mood_buffer.get().strip())
        except ValueError:
            eb_val = 5
        cfg["ai_config"]["mood_buffer_limit"] = eb_val

        try:
            dh_val = float(self.entry_ai_decay_hours.get().strip())
        except ValueError:
            dh_val = 2.0
        cfg["ai_config"]["mood_decay_hours"] = dh_val

        cfg["ai_config"]["enable_history_limit"] = bool(self.switch_history_limit.get())
        try:
            sh_val = int(self.entry_history_limit_max.get().strip())
        except ValueError:
            sh_val = 50
        cfg["ai_config"]["history_save_limit"] = sh_val
        
        if "target_channels" in cfg["ai_config"]:
            cfg["ai_config"]["target_channels"] = []
        
        self.controller._save_json_file("config.json", cfg)
        self.lbl_status_ai_settings.configure(text=self.controller.lang_manager.get("cfg_ais_msg_reload"), text_color=self.controller.theme_manager.get("green"))
        self.controller.send_to_bot('IPC>>{"type": "command", "name": "reload"}')
        self.after(3000, lambda: self.lbl_status_ai_settings.configure(text=""))

    def reset_ai_settings(self):
        cfg = self.controller._load_json_file("config.json")
        if "ai_config" not in cfg: cfg["ai_config"] = {}
        defaults = {
            "image_size_limit_mb": 8.0,
            "tts_send_text": True,
            "auto_web_search": True,
            "web_search_method": "google",
            "web_search_max_results": 3,
            "tts_engine": "nube_edge",
            "tts_voice": "es-MX-DaliaNeural",
            "tts_rvc": False,
            "vision_lookback_limit": 10,
            "context_window": 15,
            "mood_history_limit": 10,
            "memory_buffer_limit": 5,
            "mood_buffer_limit": 5,
            "mood_decay_hours": 2.0,
            "enable_history_limit": True,
            "history_save_limit": 50,
            "spontaneous_prob": 0.05,
            "cooldown": 3.0,
            "gamer_limit": 5,
            "repeat_penalty": 1.1,
            "client_timeout": 180
        }
        for k, v in defaults.items(): cfg["ai_config"][k] = v
        self.controller._save_json_file("config.json", cfg)
        self.load_ai_settings_ui()
        self.lbl_status_ai_settings.configure(text=self.controller.lang_manager.get("cfg_ais_msg_reset"), text_color=self.controller.theme_manager.get("accent"))
        self.after(3000, lambda: self.lbl_status_ai_settings.configure(text=""))