import tkinter as tk
from Internal.ui.GradeEditUi import GradeEditUi
from Internal.ui.GradeCatalogUi import GradeCatalogUi


class GradesView:
    def __init__(self, parent_frame, controller):
        self.parent = parent_frame
        self.master = controller
        self.user_id = self.master.user.get_id_entity()
        self.colors = self.master.settings_service.get_colors(self.user_id)

    def render(self):
        """Randarea tabelului de gestionare clase cu suport multilingv."""
        self.master.clear_content()
        uid = self.user_id
        ls = self.master.language_service
        colors = self.master.settings_service.get_colors(uid)
        txt_color = colors.get("schedule_text", colors["fg"])

        # 1. Header principal
        header_frame = tk.Frame(self.parent, bg=colors["bg"])
        header_frame.pack(fill="x", pady=(0, 25))

        tk.Label(header_frame, text=f"🏫 {ls.get_text(uid, 'menu_grades')}", font=("Segoe UI", 26, "bold"),
                 bg=colors["bg"], fg=colors["fg"]).pack(side="left")

        tk.Button(header_frame, text=ls.get_text(uid, 'btn_add_grade'), command=self.master.open_add_grade_modal,
                  bg="#9B59B6", fg="white", font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=25, pady=12, cursor="hand2").pack(side="right")

        # 2. Container Scrollbar
        canvas_container = tk.Frame(self.parent, bg=colors["bg"])
        canvas_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_container, bg=colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        table_inner = tk.Frame(canvas, bg=colors["bg"])
        canvas_window = canvas.create_window((0, 0), window=table_inner, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Destroy>", lambda _: canvas.unbind_all("<MouseWheel>"))

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        table_inner.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # --- Header Tabel ---
        header_table = tk.Frame(table_inner, bg=colors["input_bg"])
        header_table.pack(fill="x", pady=(0, 4))

        headers = [
            ls.get_text(uid, "col_grade_name"),
            "Nr. studenți",
            ls.get_text(uid, "col_actions")
        ]
        widths = [35, 25, 40]

        for i, h in enumerate(headers):
            tk.Label(header_table, text=h.upper(), font=("Segoe UI", 10, "bold"),
                     bg=colors["input_bg"], fg=txt_color, pady=20, width=widths[i]).pack(side="left", fill="x",
                                                                                         expand=True)

        # 3. Populare rânduri (mai înalte și clickabile)
        grades = sorted(self.master.grade_service.get_grades_for_teacher(uid),
                        key=lambda grade: grade.get_grade_name())

        for idx, g in enumerate(grades):
            bg_row = colors["card_bg"] if idx % 2 == 0 else colors["input_bg"]
            row_frame = tk.Frame(table_inner, bg=bg_row, pady=12)
            row_frame.pack(fill="x", pady=3)

            # Clasa (clickabilă -> deschide catalogul)
            name_lbl = tk.Label(row_frame, text=g.get_grade_name(), font=("Segoe UI", 13, "bold"),
                                bg=bg_row, fg=colors.get("accent", "#3498DB"), pady=16,
                                width=widths[0], cursor="hand2")
            name_lbl.pack(side="left", fill="x", expand=True)
            name_lbl.bind("<Button-1>", lambda e, gr=g: self.open_grade_catalog(gr))

            # Nr. studenți (clickabil -> deschide catalogul)
            student_count = sum(
                1 for s_id in g.get_student_ids()
                if self.master.student_service.get_student_by_id(s_id)
            )
            count_lbl = tk.Label(row_frame, text=str(student_count), font=("Segoe UI", 12, "bold"),
                                 bg=bg_row, fg=txt_color, pady=16, width=widths[1], cursor="hand2")
            count_lbl.pack(side="left", fill="x", expand=True)
            count_lbl.bind("<Button-1>", lambda e, gr=g: self.open_grade_catalog(gr))

            # Acțiuni (butoane mai mari și vizibile)
            act_f = tk.Frame(row_frame, bg=bg_row, width=widths[2])
            act_f.pack(side="left", fill="x", expand=True)
            btns = tk.Frame(act_f, bg=bg_row)
            btns.pack(expand=True)

            tk.Button(btns, text="📋 Catalog", bg="#3498DB", fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                      padx=14, pady=8,
                      command=lambda gr=g: self.open_grade_catalog(gr)).pack(side="left", padx=6)

            tk.Button(btns, text="✏️ Editează", bg="#F1C40F", fg="#1A1A1A",
                      font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                      padx=14, pady=8,
                      command=lambda gr=g: self.open_edit_grade_modal(gr)).pack(side="left", padx=6)

            tk.Button(btns, text="🗑️ Șterge", bg="#E74C3C", fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                      padx=14, pady=8,
                      command=lambda gr=g: self.master.handle_delete_grade(gr)).pack(side="left", padx=6)

    def open_grade_catalog(self, grade):
        GradeCatalogUi(
            self.master.root,
            self.master.settings_service.get_colors(self.user_id),
            grade,
            self.master.student_service
        )

    def open_edit_grade_modal(self, grade):
        GradeEditUi(self.master.root, self.colors, grade, self.master.grade_service,
                    self.master.student_service, self.master.show_grades, self.master.language_service)