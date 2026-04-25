import customtkinter as ctk
import os
import sys
from shared.config_manager import ConfigManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RangesEditor(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(0, 10))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=self.controller.lang_manager.get("ai_rng_title"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.controller.theme_manager.get("accent")).pack(side="left")
        
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctk.CTkLabel(help_frame, text=self.controller.lang_manager.get("ai_rng_desc"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12), justify="left").pack(side="left", pady=(5,0))
        
        ctk.CTkButton(title_row, text="?", width=28, height=28, fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text"), command=lambda h=help_frame: self.controller.toggle_help(h, "pack", fill="x")).pack(side="left", padx=15)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="bottom", fill="x", pady=(10, 0))
        
        lbl_status = ctk.CTkLabel(controls, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(weight="bold"))
        lbl_status.pack(side="right", padx=10)

        # --- LÍMITES Y BARRA VISUAL ---
        limits_frame = ctk.CTkFrame(self, fg_color="transparent")
        limits_frame.pack(side="top", fill="x", padx=20, pady=(0, 5))
        
        ctk.CTkLabel(limits_frame, text=self.controller.lang_manager.get("ai_rng_lbl_gmin"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")
        ent_gmin = ctk.CTkEntry(limits_frame, width=60, height=28, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"))
        ent_gmin.pack(side="left", padx=10)
        
        ctk.CTkLabel(limits_frame, text=self.controller.lang_manager.get("ai_rng_lbl_gmax"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left", padx=(20, 0))
        ent_gmax = ctk.CTkEntry(limits_frame, width=60, height=28, fg_color=self.controller.theme_manager.get("bg_dark"), border_color=self.controller.theme_manager.get("border"))
        ent_gmax.pack(side="left", padx=10)
        
        lbl_bar_status = ctk.CTkLabel(limits_frame, text="", text_color=self.controller.theme_manager.get("green"), font=ctk.CTkFont(size=12, weight="bold"))
        lbl_bar_status.pack(side="right")

        bar_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        bar_wrapper.pack(side="top", fill="x", padx=20, pady=(10, 10))
        
        self.range_visual_data = {}
        
        canvas = ctk.CTkCanvas(bar_wrapper, height=70, bg=self.controller.theme_manager.get("bg_dark"), highlightthickness=0)
        canvas.pack(side="top", fill="x", expand=True)
        
        info_label = ctk.CTkLabel(bar_wrapper, text=self.controller.lang_manager.get("ai_rng_lbl_info"), text_color=self.controller.theme_manager.get("text_dim"), font=ctk.CTkFont(size=12))
        info_label.pack(side="top", pady=(5, 0))

        def update_bar(event=None):
            canvas.delete("all")
            width = canvas.winfo_width()
            if width <= 1: return
            
            try: g_min = int(ent_gmin.get().strip())
            except: g_min = -100
            try: g_max = int(ent_gmax.get().strip())
            except: g_max = 100
            
            if g_max <= g_min:
                lbl_bar_status.configure(text=self.controller.lang_manager.get("ai_rng_err_glim"), text_color=self.controller.theme_manager.get("red"))
                return
                
            span = g_max - g_min
            
            def get_color_gradient(val):
                p = (val - g_min) / span
                p = max(0.0, min(1.0, p))
                
                c1 = (247, 118, 142)
                c2 = (224, 175, 104)
                c3 = (158, 206, 106)
                
                if p < 0.5:
                    p2 = p * 2.0
                    r, g_c, b = [int(c1[idx] + (c2[idx] - c1[idx]) * p2) for idx in range(3)]
                else:
                    p2 = (p - 0.5) * 2.0
                    r, g_c, b = [int(c2[idx] + (c3[idx] - c2[idx]) * p2) for idx in range(3)]
                return f"#{r:02x}{g_c:02x}{b:02x}"

            ranges = []
            has_error = False
            error_msg = ""
            
            for i, d in enumerate(self.ranges_entries):
                try: mn = int(d["min"].get().strip())
                except: mn = 0
                try: mx = int(d["max"].get().strip())
                except: mx = 0
                
                if mn > mx:
                    has_error = True
                    error_msg = self.controller.lang_manager.get("ai_rng_err_inv")
                elif mn < g_min or mx > g_max:
                    has_error = True
                    error_msg = self.controller.lang_manager.get("ai_rng_err_out").format(g_min=g_min, g_max=g_max)
                    
                mid_val = (mn + mx) / 2
                col = get_color_gradient(mid_val)
                ranges.append({"min": mn, "max": mx, "etiq": d["etiq"].get().strip(), "col": col, "id": d["id"]})
            
            ranges.sort(key=lambda x: x["min"])
            
            has_overlap = False
            for i in range(len(ranges)-1):
                if ranges[i]["max"] >= ranges[i+1]["min"]:
                    has_overlap = True
                    has_error = True
                    error_msg = self.controller.lang_manager.get("ai_rng_err_over")
                    break
            
            if has_error: lbl_bar_status.configure(text=error_msg, text_color=self.controller.theme_manager.get("red"))
            else: lbl_bar_status.configure(text=self.controller.lang_manager.get("ai_rng_ok_valid"), text_color=self.controller.theme_manager.get("green"))
            
            canvas.create_rectangle(0, 45, width, 70, fill=self.controller.theme_manager.get("bg_sidebar"), outline=self.controller.theme_manager.get("border"))
                
            if not has_overlap and not has_error:
                curr = g_min - 1
                gaps = []
                for r in ranges:
                    if r["min"] - curr > 1: gaps.append((curr + 1, r["min"] - 1))
                    curr = max(curr, r["max"])
                if g_max - curr > 0: gaps.append((curr + 1, g_max))
                
                for i, (gap_min, gap_max) in enumerate(gaps):
                    x1 = max(0, (gap_min - g_min) / span * width)
                    x2 = min(width, (gap_max - g_min) / span * width)
                    
                    canvas.create_rectangle(x1, 45, x2, 70, fill="#331a20", outline=self.controller.theme_manager.get("red"))
                    
                    mid_x = (x1 + x2) / 2
                    y_text = 5 if i % 2 == 0 else 22
                    canvas.create_line(mid_x, 45, mid_x, y_text + 14, fill=self.controller.theme_manager.get("red"))
                    canvas.create_text(mid_x, y_text, text=self.controller.lang_manager.get("ai_rng_lbl_gap").format(gap_min=gap_min, gap_max=gap_max), fill=self.controller.theme_manager.get("red"), anchor="n", font=("Consolas", 10, "bold"))
            
            self.range_visual_data.clear()
            
            for r in ranges:
                if r["min"] > r["max"]: continue
                draw_min = max(g_min, r["min"])
                draw_max = min(g_max, r["max"])
                if draw_max < draw_min: continue
                
                rel_x = (draw_min - g_min) / span
                rel_w = (draw_max - draw_min) / span
                x1 = rel_x * width
                x2 = (rel_x + rel_w) * width
                
                if x1 == x2: x2 += 3
                
                tag = f"rect_{r['id']}"
                canvas.create_rectangle(x1, 45, x2, 70, fill=r["col"], outline=self.controller.theme_manager.get("bg_dark"), tags=(tag,))
                
                hover_txt = f"[{r['min']} a {r['max']}] {r['etiq']}"
                self.range_visual_data[r['id']] = {"tag": tag, "text": hover_txt}
                
                def on_enter(e, tg=tag, txt=hover_txt):
                    info_label.configure(text=txt, text_color=self.controller.theme_manager.get("accent"))
                    canvas.itemconfig(tg, outline="white", width=2)
                def on_leave(e, tg=tag):
                    info_label.configure(text=self.controller.lang_manager.get("ai_rng_lbl_info"), text_color=self.controller.theme_manager.get("text_dim"))
                    canvas.itemconfig(tg, outline=self.controller.theme_manager.get("bg_dark"), width=1)
                    
                canvas.tag_bind(tag, "<Enter>", on_enter)
                canvas.tag_bind(tag, "<Leave>", on_leave)
                
        canvas.bind("<Configure>", update_bar)

        scroll_ranges = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.controller.theme_manager.get("bg_dark"), scrollbar_button_hover_color=self.controller.theme_manager.get("bg_dark"))
        scroll_ranges.pack(fill="both", expand=True)

        ranges_path = os.path.join(BASE_DIR, "cogs", "AI", "memory", "afinidad_rangos.json")
        self.ranges_entries = []

        def sort_ranges_ui():
            def get_sort_key(d):
                try: mx = int(d["max"].get().strip())
                except: mx = -999999
                try: mn = int(d["min"].get().strip())
                except: mn = -999999
                return (mx, mn)
            
            self.ranges_entries.sort(key=get_sort_key, reverse=True)
            for d in self.ranges_entries:
                d["row"].pack_forget()
                d["row"].pack(fill="x", pady=5)

        def add_range_ui(min_v, max_v, etiq, desc):
            row = ctk.CTkFrame(scroll_ranges, fg_color=self.controller.theme_manager.get("bg_dark"), corner_radius=8)
            row.pack(fill="x", pady=5)
            
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(10, 5))
            
            ctk.CTkLabel(top, text=self.controller.lang_manager.get("ai_rng_lbl_min"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")
            ent_min = ctk.CTkEntry(top, width=50, height=28, fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"))
            ent_min.pack(side="left", padx=5)
            ent_min.insert(0, str(min_v))
            
            ctk.CTkLabel(top, text=self.controller.lang_manager.get("ai_rng_lbl_max"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left")
            ent_max = ctk.CTkEntry(top, width=50, height=28, fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"))
            ent_max.pack(side="left", padx=5)
            ent_max.insert(0, str(max_v))
            
            ctk.CTkLabel(top, text=self.controller.lang_manager.get("ai_rng_lbl_tag"), text_color=self.controller.theme_manager.get("text_dim")).pack(side="left", padx=(10,0))
            ent_etiq = ctk.CTkEntry(top, width=150, height=28, fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("accent"), font=ctk.CTkFont(weight="bold"))
            ent_etiq.pack(side="left", fill="x", expand=True, padx=5)
            ent_etiq.insert(0, etiq)
            
            btn_del = ctk.CTkButton(top, text="🗑", width=30, height=28, fg_color="transparent", hover_color=self.controller.theme_manager.get("red"), text_color=self.controller.theme_manager.get("text_dim"))
            btn_del.pack(side="right")
            
            bot = ctk.CTkFrame(row, fg_color="transparent")
            bot.pack(fill="x", padx=10, pady=(0, 10))
            
            txt_desc = ctk.CTkTextbox(bot, height=40, font=("Consolas", 12), fg_color=self.controller.theme_manager.get("bg_card"), border_color=self.controller.theme_manager.get("border"), border_width=1, text_color=self.controller.theme_manager.get("text"), wrap="word")
            txt_desc.pack(fill="x")
            txt_desc.insert("0.0", desc)
            self.controller._fix_scroll(txt_desc)
            
            def resize_desc_r(event=None, t=txt_desc):
                try:
                    w = t.winfo_width()
                    if w < 50: lines = max(1, len(t.get("0.0", "end").strip()) // 60 + 1)
                    else:
                        dl = t._textbox.count("1.0", "end", "displaylines")
                        lines = dl[0] if dl else 1
                    t.configure(height=max(40, lines * 18))
                except: pass
            txt_desc.bind("<KeyRelease>", resize_desc_r)
            self.after(50, resize_desc_r)
            
            row_id = str(id(row))
            entry_data = {"row": row, "min": ent_min, "max": ent_max, "etiq": ent_etiq, "desc": txt_desc, "id": row_id}
            self.ranges_entries.append(entry_data)
            
            def on_focus_in(event):
                data = self.range_visual_data.get(row_id)
                if data:
                    info_label.configure(text=data["text"], text_color=self.controller.theme_manager.get("accent"))
                    canvas.itemconfig(data["tag"], outline="white", width=2)
            
            def delayed_sort():
                try:
                    focused = self.focus_get()
                    if focused and str(row) in str(focused): return
                except: pass
                sort_ranges_ui()
                
            def on_focus_out(event):
                data = self.range_visual_data.get(row_id)
                if data:
                    info_label.configure(text=self.controller.lang_manager.get("ai_rng_lbl_info"), text_color=self.controller.theme_manager.get("text_dim"))
                    canvas.itemconfig(data["tag"], outline=self.controller.theme_manager.get("bg_dark"), width=1)
                self.after(200, delayed_sort)
            
            ent_min.bind("<KeyRelease>", update_bar)
            ent_max.bind("<KeyRelease>", update_bar)
            ent_min.bind("<FocusIn>", on_focus_in, add="+")
            ent_max.bind("<FocusIn>", on_focus_in, add="+")
            ent_etiq.bind("<FocusIn>", on_focus_in, add="+")
            ent_min.bind("<FocusOut>", on_focus_out, add="+")
            ent_max.bind("<FocusOut>", on_focus_out, add="+")
            ent_etiq.bind("<FocusOut>", on_focus_out, add="+")
            
            btn_del.configure(command=lambda r=row, d=entry_data: delete_range(r, d))
            self.after(50, update_bar)

        def delete_range(row, data):
            row.destroy()
            if data in self.ranges_entries:
                self.ranges_entries.remove(data)
            update_bar()

        def save_ranges():
            sort_ranges_ui()
            new_ranges = []
            for d in self.ranges_entries:
                try: mn = int(d["min"].get().strip())
                except: mn = 0
                try: mx = int(d["max"].get().strip())
                except: mx = 0
                new_ranges.append({
                    "min": mn, "max": mx,
                    "etiqueta": d["etiq"].get().strip(),
                    "descripcion": d["desc"].get("0.0", "end").strip()
                })
            try:
                ConfigManager.save_json(ranges_path, new_ranges, use_lock=False)
                
                cfg = self.controller._load_json_file("config.json")
                if "ai_config" not in cfg: cfg["ai_config"] = {}
                try: cfg["ai_config"]["aff_min"] = int(ent_gmin.get().strip())
                except: pass
                try: cfg["ai_config"]["aff_max"] = int(ent_gmax.get().strip())
                except: pass
                self.controller._save_json_file("config.json", cfg)
                lbl_status.configure(text=self.controller.lang_manager.get("ai_rng_msg_saved"), text_color=self.controller.theme_manager.get("green"))
                self.after(3000, lambda: lbl_status.configure(text=""))
            except Exception as e: lbl_status.configure(text=self.controller.lang_manager.get("msg_err_generic").format(e=e), text_color=self.controller.theme_manager.get("red"))

        btns_ranges = ctk.CTkFrame(controls, fg_color="transparent")
        btns_ranges.pack(side="left")
        ctk.CTkButton(btns_ranges, text=self.controller.lang_manager.get("btn_reload"), command=lambda: load_ranges(), fg_color=self.controller.theme_manager.get("bg_card"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(btns_ranges, text=self.controller.lang_manager.get("ai_rng_btn_add"), command=lambda: (add_range_ui(0, 0, self.controller.lang_manager.get("ai_rng_def_new"), ""), sort_ranges_ui()), fg_color=self.controller.theme_manager.get("bg_dark"), hover_color=self.controller.theme_manager.get("border"), text_color=self.controller.theme_manager.get("text")).pack(side="left", padx=5)
        ctk.CTkButton(btns_ranges, text=self.controller.lang_manager.get("btn_save_changes"), command=save_ranges, fg_color=self.controller.theme_manager.get("accent"), hover_color=self.controller.theme_manager.get("accent_dim"), text_color=self.controller.theme_manager.get("bg_dark")).pack(side="left", padx=5)

        def load_ranges():
            for w in scroll_ranges.winfo_children(): w.destroy()
            
            cfg = self.controller._load_json_file("config.json").get("ai_config", {})
            ent_gmin.delete(0, "end")
            ent_gmin.insert(0, str(cfg.get("aff_min", -100)))
            ent_gmax.delete(0, "end")
            ent_gmax.insert(0, str(cfg.get("aff_max", 100)))
            
            self.ranges_entries.clear()
            
            rangos = ConfigManager.load_json(ranges_path, use_lock=False)
            if isinstance(rangos, list) and rangos:
                for r in rangos:
                    add_range_ui(r.get("min", 0), r.get("max", 0), r.get("etiqueta", ""), r.get("descripcion", ""))
            else:
                defaults = [
                    {"min": -100, "max": -50, "etiqueta": self.controller.lang_manager.get("ai_rng_def_hate"), "descripcion": self.controller.lang_manager.get("ai_rng_def_hate_desc")},
                    {"min": -49, "max": -11, "etiqueta": self.controller.lang_manager.get("ai_rng_def_annoy"), "descripcion": self.controller.lang_manager.get("ai_rng_def_annoy_desc")},
                    {"min": -10, "max": 10, "etiqueta": self.controller.lang_manager.get("ai_rng_def_neutral"), "descripcion": self.controller.lang_manager.get("ai_rng_def_neutral_desc")},
                    {"min": 11, "max": 49, "etiqueta": self.controller.lang_manager.get("ai_rng_def_friend"), "descripcion": self.controller.lang_manager.get("ai_rng_def_friend_desc")},
                    {"min": 50, "max": 100, "etiqueta": self.controller.lang_manager.get("ai_rng_def_close"), "descripcion": self.controller.lang_manager.get("ai_rng_def_close_desc")}
                ]
                for r in defaults:
                    add_range_ui(r["min"], r["max"], r["etiqueta"], r["descripcion"])
            
            sort_ranges_ui()
            self.after(50, update_bar)
            lbl_status.configure(text=self.controller.lang_manager.get("ai_rng_msg_loaded"), text_color=self.controller.theme_manager.get("text_dim"))

        load_ranges()
        ent_gmin.bind("<KeyRelease>", update_bar)
        ent_gmax.bind("<KeyRelease>", update_bar)
        self.controller.ai_reload_functions["config_ai_ranges"] = load_ranges