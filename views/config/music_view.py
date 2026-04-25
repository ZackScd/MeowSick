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

class MusicConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text=self.controller.lang_manager.get("cfg_mus_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Playlist URL (ENV)
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_mus_pl_title"), font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        pl_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        pl_card.pack(fill="x", padx=20, pady=5)
        
        # Wrapper para Playlist
        pl_wrapper = ctk.CTkFrame(pl_card, fg_color="transparent")
        pl_wrapper.pack(fill="x", pady=10)

        pl_row = ctk.CTkFrame(pl_wrapper, fg_color="transparent")
        pl_row.pack(fill="x", padx=15)
        
        ctk.CTkLabel(pl_row, text=self.controller.lang_manager.get("cfg_mus_pl_label"), text_color=self.controller.theme_manager.get("text")).pack(side="left")
        self.entry_playlist = ctk.CTkEntry(pl_row, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), width=300)
        self.entry_playlist.pack(side="left", fill="x", expand=True, padx=(10, 10))
        
        env_data = dotenv_values(ENV_PATH)
        self.entry_playlist.insert(0, env_data.get("PLAYLIST_URL", ""))
        
        pl_help = ctk.CTkFrame(pl_wrapper, fg_color="transparent")
        ctk.CTkLabel(pl_help, text=f"ℹ {self.controller.lang_manager.get('cfg_mus_pl_help')}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
        ctk.CTkButton(pl_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=pl_help: self.controller.toggle_help(h, "pack", fill="x", padx=180)).pack(side="right")

        # Mensajes de Salida (OUTPUTS)
        ctk.CTkLabel(scroll, text=self.controller.lang_manager.get("cfg_mus_msg_title"), font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        msg_card = ctk.CTkFrame(scroll, fg_color=self.controller.theme_manager.get("bg_card"), corner_radius=10)
        msg_card.pack(fill="x", padx=20, pady=5)

        outputs_filename = f"locales/outputs_{self.controller.lang_code}.json"
        outputs_data = self.controller._load_json_file(outputs_filename) or {}
        self.music_entries = {}
        
        music_msgs = [
            ("playing_now", "[!play] playing_now ({title})", self.controller.lang_manager.get("cfg_mus_help_playing_now")),
            ("added_queue", "[!play] added_queue ({title})", self.controller.lang_manager.get("cfg_mus_help_added_queue")),
            ("play_no_args", "[!play] play_no_args", self.controller.lang_manager.get("cfg_mus_help_play_no_args")),
            ("connect_voice", "[!play] connect_voice", self.controller.lang_manager.get("cfg_mus_help_connect_voice")),
            ("playlist_added", "[!playlist] playlist_added ({count})", self.controller.lang_manager.get("cfg_mus_help_playlist_added")),
            ("playlist_no_config", "[!playlist] playlist_no_config", self.controller.lang_manager.get("cfg_mus_help_playlist_no_config")),
            ("next_added", "[!next] next_added ({title})", self.controller.lang_manager.get("cfg_mus_help_next_added")),
            ("skip_msg", "[!skip] skip_msg", self.controller.lang_manager.get("cfg_mus_help_skip_msg")),
            ("nothing_playing", "[!skip] nothing_playing", self.controller.lang_manager.get("cfg_mus_help_nothing_playing")),
            ("paused", "[!pause] paused", self.controller.lang_manager.get("cfg_mus_help_paused")),
            ("resumed", "[!resume] resumed", self.controller.lang_manager.get("cfg_mus_help_resumed")),
            ("stop_msg", "[!stop] stop_msg", self.controller.lang_manager.get("cfg_mus_help_stop_msg")),
            ("list_title", "[!list] list_title", self.controller.lang_manager.get("cfg_mus_help_list_title")),
            ("list_empty", "[!list] list_empty", self.controller.lang_manager.get("cfg_mus_help_list_empty")),
            ("shuffled", "[!shuffle] shuffled", self.controller.lang_manager.get("cfg_mus_help_shuffled")),
            ("shuffle_error", "[!shuffle] shuffle_error", self.controller.lang_manager.get("cfg_mus_help_shuffle_error")),
            ("queue_finished", "[Auto] queue_finished", self.controller.lang_manager.get("cfg_mus_help_queue_finished")),
            ("timeout_msg", "[Auto] timeout_msg", self.controller.lang_manager.get("cfg_mus_help_timeout_msg")),
            ("disconnected", "[!leave] disconnected", self.controller.lang_manager.get("cfg_mus_help_disconnected")),
            ("not_connected", "[!leave] not_connected", self.controller.lang_manager.get("cfg_mus_help_not_connected")),
            ("connect_error", "[Error] connect_error", self.controller.lang_manager.get("cfg_mus_help_connect_error")),
            ("search_error", "[Error] search_error", self.controller.lang_manager.get("cfg_mus_help_search_error")),
            ("ffmpeg_error", "[Error] ffmpeg_error", self.controller.lang_manager.get("cfg_mus_help_ffmpeg_error"))
        ]

        for key, label, help_text in music_msgs:
            wrapper = ctk.CTkFrame(msg_card, fg_color="transparent")
            wrapper.pack(fill="x", pady=0)

            row = ctk.CTkFrame(wrapper, fg_color="transparent")
            row.pack(fill="x", pady=5, padx=15)
            
            ctk.CTkLabel(row, text=label, width=200, anchor="w", text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")
            entry = ctk.CTkEntry(row, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"))
            entry.pack(side="left", fill="x", expand=True)
            entry.insert(0, outputs_data.get(key, ""))
            self.music_entries[key] = entry
            
            help_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
            ctk.CTkLabel(help_frame, text=f"ℹ {help_text}", text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
            ctk.CTkButton(row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x", padx=215)).pack(side="right", padx=(5,0))

        ctk.CTkButton(scroll, text=self.controller.lang_manager.get("btn_save"), command=self.save_music_config, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark"), height=40, corner_radius=10).pack(pady=(20, 5))
        self.lbl_status_music = ctk.CTkLabel(scroll, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_status_music.pack(pady=(0, 20))

    def save_music_config(self):
        set_key(ENV_PATH, "PLAYLIST_URL", self.entry_playlist.get().strip())

        outputs_filename = f"locales/outputs_{self.controller.lang_code}.json"
        out = self.controller._load_json_file(outputs_filename) or {}
        for key, entry in self.music_entries.items():
            out[key] = entry.get().strip()
        self.controller._save_json_file(outputs_filename, out)
        
        self.lbl_status_music.configure(text=self.controller.lang_manager.get("msg_saved_success"), text_color=self.controller.theme_manager.get("green"))
        self.after(3000, lambda: self.lbl_status_music.configure(text=""))