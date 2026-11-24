import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry


def get_dynamic_colors(cell_id, raw_data, colors):
    if not raw_data or not raw_data.get('grade_name'):
        return colors["card_bg"], colors["fg"]

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    curr_t = now.strftime("%H:%M")
    cell_date_str = cell_id.split('_')[0]
    cell_date_obj = datetime.strptime(cell_date_str, "%Y-%m-%d")
    start_of_current_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        time_range = raw_data.get('time', "00:00-00:00")
        start_t, end_t = time_range.split("-")

        # SĂPTĂMÂNI TRECUTE COMPLET
        if cell_date_obj < start_of_current_week:
            return colors.get("schedule_past_bg", "#2C2C2C"), colors.get("schedule_past_fg", "#777777")

        # ȘEDINȚE TERMINATE (Azi sau în sapt. curentă)
        if cell_date_str < today_str or (cell_date_str == today_str and curr_t > end_t):
            return colors.get("schedule_past_bg", "#1B3D2F"), colors.get("schedule_past_fg", "#A5D6A7")

        # ȘEDINȚA ACTIVĂ CHIAR ACUM
        if cell_date_str == today_str and start_t <= curr_t <= end_t:
            return colors["accent"], "white"

        # ȘEDINȚE CARE URMEAZĂ AZI
        if cell_date_str == today_str and curr_t < start_t:
            return colors.get("schedule_upcoming_today_bg", "#D35400"), "white"

        # ȘEDINȚE DIN ZILELE VIITOARE ALE SĂPTĂMÂNII
        return colors.get("schedule_future_bg", "#3D3A1B"), colors.get("schedule_future_fg", "#FFF59D")

    except Exception as e:
        print(f"Eroare culori: {e}")

    return colors["card_bg"], colors["fg"]


class ScheduleView:
    def __init__(self, parent_frame, controller):
        self.parent = parent_frame
        self.master = controller
        self.table_container = None
        self.canvas = None
        self.cal_select = None

        self.cell_widgets = {}
        self._last_grid_info = ""

        # --- LOGICĂ ZILE SELECTATE (PERSISTENTĂ) ---
        uid = self.master.user.get_id_entity()
        user_settings = self.master.settings_service.get_user_settings(uid)
        saved_days = user_settings.get("active_days", [0, 1, 2, 3, 4, 5])

        ls = self.master.language_service
        self.days_map = [
            ls.get_text(uid, "day_mon"),
            ls.get_text(uid, "day_tue"),
            ls.get_text(uid, "day_wed"),
            ls.get_text(uid, "day_thu"),
            ls.get_text(uid, "day_fri"),
            ls.get_text(uid, "day_sat"),
            ls.get_text(uid, "day_sun")
        ]
        self.selected_days = [tk.BooleanVar(value=(i in saved_days)) for i in range(7)]

        initial_rows = user_settings.get("schedule_rows", user_settings.get("rows_count", 5))
        self.rows_var = getattr(self.master, "rows_var", None)
        if self.rows_var is None:
            self.rows_var = tk.IntVar(value=initial_rows)
        else:
            self.rows_var.set(initial_rows)

        self.row_height = user_settings.get("schedule_row_height", 110)
        self.col_minwidth = user_settings.get("schedule_col_minwidth", 180)

    def _get_cell_data(self, uid, cell_id):
        """Preia sigur datele unei celule, indiferent dacă schedule_data e dict sau list."""
        schedule_data = self.master.schedule_service.get_schedule_data()

        if isinstance(schedule_data, dict):
            return schedule_data.get(f"{uid}_{cell_id}_raw", {})

        if isinstance(schedule_data, list):
            for item in schedule_data:
                if isinstance(item, dict) and item.get("cell_id") == cell_id and item.get("user_id") == uid:
                    return item

        return {}

    def render(self):
        """Metoda de randare principală cu suport multilingv."""
        self.master.clear_content()
        uid = self.master.user.get_id_entity()
        ls = self.master.language_service

        self.days_map = [
            ls.get_text(uid, "day_mon"),
            ls.get_text(uid, "day_tue"),
            ls.get_text(uid, "day_wed"),
            ls.get_text(uid, "day_thu"),
            ls.get_text(uid, "day_fri"),
            ls.get_text(uid, "day_sat"),
            ls.get_text(uid, "day_sun")
        ]
        self.master.colors = self.master.settings_service.get_colors(uid)
        colors = self.master.colors

        # --- Top Bar Stilizat ---
        header_frame = tk.Frame(self.parent, bg=colors["bg"], pady=15)
        header_frame.pack(fill="x")

        nav_frame = tk.Frame(header_frame, bg=colors["bg"])
        nav_frame.pack(side="left", padx=20)

        today_btn_text = ls.get_text(uid, "btn_today")
        for btn_text, cmd in [("◀", self.master.prev_week), (f"📅 {today_btn_text}", self.master.go_to_today),
                              ("▶", self.master.next_week)]:
            tk.Button(nav_frame, text=btn_text, command=cmd,
                      bg=colors["card_bg"], fg=colors["accent"], font=("Segoe UI", 10, "bold"),
                      relief="flat", padx=15, pady=8, cursor="hand2").pack(side="left", padx=3)

        user_lang = self.master.settings_service.get_user_settings(uid).get("language", "ro")
        cal_locale = 'ro_RO' if user_lang == 'ro' else 'en_US'

        self.cal_select = DateEntry(nav_frame, width=14, background=colors["accent"],
                                    foreground='white', font=("Segoe UI", 11),
                                    date_pattern='dd.mm.yyyy', locale=cal_locale)
        self.cal_select.set_date(self.master.current_date)
        self.cal_select.pack(side="left", padx=15)
        self.cal_select.bind("<<DateEntrySelected>>", self.master.on_date_selected)

        actions_frame = tk.Frame(header_frame, bg=colors["bg"])
        actions_frame.pack(side="right", padx=20)

        # Control număr rânduri (- / +)
        rows_ctrl = tk.Frame(actions_frame, bg=colors["card_bg"], padx=6, pady=4)
        rows_ctrl.pack(side="left", padx=(0, 8))

        tk.Label(rows_ctrl, text="Rânduri:", font=("Segoe UI", 9, "bold"),
                 bg=colors["card_bg"], fg=colors.get("schedule_text", colors["fg"])).pack(side="left", padx=(0, 4))

        tk.Button(rows_ctrl, text="-", command=lambda: self._change_rows(-1),
                  bg=colors["input_bg"], fg=colors["fg"], font=("Segoe UI", 9, "bold"),
                  relief="flat", width=2, cursor="hand2").pack(side="left", padx=1)

        current_rows = self.rows_var.get() if self.rows_var else 5
        self.rows_lbl = tk.Label(rows_ctrl, text=str(current_rows), font=("Segoe UI", 10, "bold"),
                                 bg=colors["card_bg"], fg=colors["accent"], width=3)
        self.rows_lbl.pack(side="left", padx=2)

        tk.Button(rows_ctrl, text="+", command=lambda: self._change_rows(1),
                  bg=colors["input_bg"], fg=colors["fg"], font=("Segoe UI", 9, "bold"),
                  relief="flat", width=2, cursor="hand2").pack(side="left", padx=1)

        # Control dimensiuni celule
        tk.Button(actions_frame, text="📐 Dimensiuni",
                  command=self.open_cell_dimensions_modal,
                  bg=colors["card_bg"], fg=colors["fg"], relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=8, cursor="hand2").pack(side="left", padx=5)

        tk.Button(actions_frame, text=f"💾 {ls.get_text(uid, 'btn_save_preset')}", command=self.master.save_as_preset,
                  bg=colors.get("success", "#27AE60"), fg="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=15, pady=8, cursor="hand2").pack(side="left", padx=5)

        tk.Button(actions_frame, text=f"📋 {ls.get_text(uid, 'btn_apply_preset')}",
                  command=self.master.open_presets_manager,
                  bg="#8E44AD", fg="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=15, pady=8, cursor="hand2").pack(side="left", padx=5)

        # --- Panou Selecție Zile ---
        days_selection_frame = tk.Frame(self.parent, bg=colors["bg"], pady=10)
        days_selection_frame.pack(fill="x")

        days_inner = tk.Frame(days_selection_frame, bg=colors["bg"])
        days_inner.pack(anchor="center")

        tk.Label(days_inner, text=f"{ls.get_text(uid, 'label_active_days')}:", font=("Segoe UI", 9, "bold"),
                 bg=colors["bg"], fg=colors.get("sub", "#888")).pack(side="left", padx=10)

        for i, day_name in enumerate(self.days_map):
            cb = tk.Checkbutton(days_inner, text=day_name, variable=self.selected_days[i],
                                bg=colors["bg"], fg=colors["fg"], selectcolor=colors["card_bg"],
                                activebackground=colors["bg"], font=("Segoe UI", 10),
                                command=self.update_days_persistence)
            cb.pack(side="left", padx=10)

        # --- Grid Container ---
        grid_outer_container = tk.Frame(self.parent, bg=colors["bg"])
        grid_outer_container.pack(fill="both", expand=True, padx=25, pady=(10, 20))

        self.canvas = tk.Canvas(grid_outer_container, bg=colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(grid_outer_container, orient="vertical", command=self.canvas.yview)

        self.table_container = tk.Frame(self.canvas, bg=colors["grid_line"])
        self.canvas.create_window((0, 0), window=self.table_container, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.table_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.draw_grid()
        self.schedule_auto_refresh()

    def update_days_persistence(self):
        uid = self.master.user.get_id_entity()
        active_indices = [i for i, var in enumerate(self.selected_days) if var.get()]
        self.master.settings_service.save_active_days(uid, active_indices)
        self.draw_grid()

    def _change_rows(self, delta):
        uid = self.master.user.get_id_entity()
        new_val = max(1, min(15, self.rows_var.get() + delta))
        self.rows_var.set(new_val)
        if hasattr(self, "rows_lbl") and self.rows_lbl.winfo_exists():
            self.rows_lbl.config(text=str(new_val))
        if hasattr(self.master, "rows_var"):
            self.master.rows_var = self.rows_var
        self.master.settings_service.save_user_setting(uid, "schedule_rows", new_val)
        self.draw_grid()

    def open_cell_dimensions_modal(self):
        uid = self.master.user.get_id_entity()
        colors = self.master.colors
        txt_color = colors.get("schedule_text", colors["fg"])

        modal = tk.Toplevel(self.parent)
        modal.title("Dimensiuni celule")
        modal.configure(bg=colors["bg"], padx=22, pady=18)
        modal.grab_set()
        modal.geometry("310x220")

        tk.Label(modal, text="Înălțime rând (px):", font=("Segoe UI", 9, "bold"),
                 bg=colors["bg"], fg=txt_color).pack(anchor="w")
        h_var = tk.StringVar(value=str(self.row_height))
        tk.Entry(modal, textvariable=h_var, font=("Segoe UI", 11),
                 bg=colors["input_bg"], fg=txt_color, relief="flat").pack(fill="x", pady=(4, 12), ipady=4)

        tk.Label(modal, text="Lățime minimă coloană (px):", font=("Segoe UI", 9, "bold"),
                 bg=colors["bg"], fg=txt_color).pack(anchor="w")
        w_var = tk.StringVar(value=str(self.col_minwidth))
        tk.Entry(modal, textvariable=w_var, font=("Segoe UI", 11),
                 bg=colors["input_bg"], fg=txt_color, relief="flat").pack(fill="x", pady=(4, 16), ipady=4)

        def apply_dims(event=None):
            try:
                new_h = max(60, min(400, int(h_var.get().strip())))
                new_w = max(100, min(500, int(w_var.get().strip())))
            except ValueError:
                messagebox.showwarning("Atenție", "Introdu valori numerice valide.", parent=modal)
                return

            self.row_height = new_h
            self.col_minwidth = new_w
            self.master.settings_service.save_user_setting(uid, "schedule_row_height", new_h)
            self.master.settings_service.save_user_setting(uid, "schedule_col_minwidth", new_w)
            modal.destroy()
            self.draw_grid()

        modal.bind("<Return>", apply_dims)

        tk.Button(modal, text="Salvează", command=apply_dims,
                  bg=colors.get("success", "#27AE60"), fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=8, cursor="hand2").pack(fill="x")

    def draw_grid(self):
        """Desenează grid-ul orarului."""
        colors = self.master.colors
        now = datetime.now()
        start_of_displayed_week = self.master.current_date - timedelta(days=self.master.current_date.weekday())
        start_of_current_real_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0,
                                                                                   microsecond=0)

        num_rows = self.rows_var.get() if self.rows_var else 5
        active_days_indices = [i for i, var in enumerate(self.selected_days) if var.get()]

        if not active_days_indices:
            return

        self.cell_widgets = {}
        for widget in self.table_container.winfo_children():
            widget.destroy()

        for col_idx in range(len(active_days_indices)):
            self.table_container.grid_columnconfigure(col_idx, weight=1, minsize=self.col_minwidth)

        # 1. Randare Headere
        for col_idx, day_idx in enumerate(active_days_indices):
            data_zi = start_of_displayed_week + timedelta(days=day_idx)
            data_zi_dt = datetime.combine(data_zi, datetime.min.time())
            data_str = data_zi.strftime('%Y-%m-%d')

            is_past_week = data_zi_dt < start_of_current_real_week
            if is_past_week:
                header_bg, header_fg = colors.get("grid_line", "#333333"), colors.get("sub", "#888888")
            elif data_str == now.strftime('%Y-%m-%d'):
                header_bg, header_fg = "#CD5C5C", "white"
            else:
                header_bg, header_fg = colors["accent"], "white"

            h_frame = tk.Frame(self.table_container, bg=header_bg, pady=15)
            h_frame.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
            tk.Label(h_frame, text=self.days_map[day_idx].upper(), font=("Segoe UI", 8, "bold"), bg=header_bg,
                     fg=header_fg).pack()
            tk.Label(h_frame, text=data_zi.strftime('%d.%m.%Y'), font=("Segoe UI", 12, "bold"), bg=header_bg,
                     fg=header_fg).pack(pady=3)

        # 2. Randare Celule
        for row in range(1, num_rows + 1):
            self.table_container.grid_rowconfigure(row, weight=0, minsize=self.row_height)
            for col_idx, day_idx in enumerate(active_days_indices):
                data_zi = start_of_displayed_week + timedelta(days=day_idx)
                cell_id = f"{data_zi.strftime('%Y-%m-%d')}_R{row}"
                self.render_cell(row, col_idx, cell_id)

    def schedule_auto_refresh(self):
        """Actualizează culorile celulelor dacă s-a schimbat starea orei."""
        if self.table_container is None or not self.table_container.winfo_exists():
            return

        if not self.parent.winfo_exists():
            return

        uid = self.master.user.get_id_entity()
        colors = self.master.colors
        needs_refresh = False

        for cid, widgets in list(self.cell_widgets.items()):
            try:
                if widgets['frame'].winfo_exists():
                    raw_data = self._get_cell_data(uid, cid)
                    if raw_data.get('grade_name'):
                        expected_bg, _ = get_dynamic_colors(cid, raw_data, colors)
                        current_bg = widgets['frame'].cget('bg')

                        if expected_bg.lower() != current_bg.lower():
                            needs_refresh = True
                            break
                else:
                    self.cell_widgets.pop(cid, None)
            except (tk.TclError, KeyError):
                continue

        if needs_refresh:
            self.draw_grid()

        self.parent.after(3000, self.schedule_auto_refresh)

    def render_cell(self, row, col, cell_id):
        """Randare celulă doar cu interval orar și numele clasei (fără studenți/absențe)."""
        uid = self.master.user.get_id_entity()
        raw_data = self._get_cell_data(uid, cell_id)
        colors = self.master.colors
        bg_color, text_color = get_dynamic_colors(cell_id, raw_data, colors)

        cell_frame = tk.Frame(self.table_container, bg=bg_color)
        cell_frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)

        self.cell_widgets[cell_id] = {'frame': cell_frame}

        inner_content = tk.Frame(cell_frame, bg=bg_color, cursor="hand2")
        inner_content.pack(fill="both", expand=True, padx=12, pady=12)

        for w in [cell_frame, inner_content]:
            w.bind("<Button-1>", lambda e, cid=cell_id: self.master.open_grade_assignment_modal(cid))

        if raw_data.get('grade_name'):
            time_lbl = tk.Label(inner_content, text=raw_data.get('time', ""), font=("Segoe UI", 9, "bold"),
                                bg=bg_color, fg=text_color)
            time_lbl.pack(anchor="nw")

            class_lbl = tk.Label(inner_content, text=raw_data.get('grade_name'), font=("Segoe UI", 12, "bold"),
                                 bg=bg_color, fg=text_color)
            class_lbl.pack(anchor="nw", pady=(6, 0))

            for lbl in [time_lbl, class_lbl]:
                lbl.bind("<Button-1>", lambda e, cid=cell_id: self.master.open_grade_assignment_modal(cid))

    def _on_mousewheel(self, event):
        try:
            if self.canvas and self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass