import tkinter as tk
from Internal.ui.StudentEditUi import StudentEditUi
from tkinter import messagebox


ROMAN_MONTHS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
    7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
}


class StudentsView:
    def __init__(self, parent_frame, controller):
        self.parent = parent_frame
        self.master = controller

    def render(self, sort_by="grade"):
        """Randare cu suport multilingv și sortare interactivă."""
        self.master.clear_content()
        user_id = self.master.user.get_id_entity()
        ls = self.master.language_service
        colors = self.master.settings_service.get_colors(user_id)
        txt_color = colors.get("schedule_text", colors["fg"])

        # 1. Header principal tradus
        header_frame = tk.Frame(self.parent, bg=colors["bg"])
        header_frame.pack(fill="x", pady=(0, 25))

        tk.Label(header_frame, text=f"👥 {ls.get_text(user_id, 'menu_students')}", font=("Segoe UI", 26, "bold"),
                 bg=colors["bg"], fg=colors["fg"]).pack(side="left")

        tk.Button(header_frame, text=ls.get_text(user_id, 'btn_add_student'),
                  command=self.master.open_add_student_modal,
                  bg=colors.get("success", "#2ECC71"), fg="white", font=("Segoe UI", 11, "bold"),
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

        # --- Header Tabel cu Sortare ---
        header_table = tk.Frame(table_inner, bg=colors["input_bg"])
        header_table.pack(fill="x")

        # (text, cheie sortare, lățime)
        headers_config = [
            (ls.get_text(user_id, "col_name_lastname"), "name", 26),
            (ls.get_text(user_id, "col_grade"), "grade", 10),
            ("Note", None, 22),
            ("Medie", None, 10),
            ("Nr. absențe", None, 12),
            (ls.get_text(user_id, "col_actions"), None, 14)
        ]

        for text, sort_key, col_width in headers_config:
            if sort_key:
                btn = tk.Button(header_table, text=text.upper(), font=("Segoe UI", 10, "bold"),
                                bg=colors["input_bg"], fg=txt_color, relief="flat",
                                activebackground=colors["accent"], cursor="hand2",
                                width=col_width,
                                command=lambda k=sort_key: self.render(k))
                btn.pack(side="left", fill="x", expand=True, ipady=15)
            else:
                tk.Label(header_table, text=text.upper(), font=("Segoe UI", 10, "bold"),
                         bg=colors["input_bg"], fg=txt_color, pady=18, width=col_width).pack(side="left", fill="x",
                                                                                             expand=True)

        # 3. Populare rânduri
        students = self.master.student_service.get_sorted_students(user_id, sort_by)

        for idx, s in enumerate(students):
            bg_row = colors["card_bg"] if idx % 2 == 0 else colors["input_bg"]
            row_frame = tk.Frame(table_inner, bg=bg_row)
            row_frame.pack(fill="x")

            # Preluare sigură pentru note și absențe
            marks = s.get_marks() if hasattr(s, "get_marks") else []
            absences = s.get_absences() if hasattr(s, "get_absences") else []

            mark_values = []
            formatted_marks = []
            for m in marks:
                if hasattr(m, "get_mark"):
                    val = m.get_mark()
                    mark_values.append(val)
                    d = m.get_date() if hasattr(m, "get_date") else None
                    if d and hasattr(d, "day") and hasattr(d, "month"):
                        formatted_marks.append(f"{val}/{d.day}{ROMAN_MONTHS.get(d.month, d.month)}")
                    else:
                        formatted_marks.append(str(val))
                else:
                    mark_values.append(m)
                    formatted_marks.append(str(m))

            marks_str = ", ".join(formatted_marks) if formatted_marks else "-"
            avg_str = f"{sum(mark_values) / len(mark_values):.2f}" if mark_values else "-"

            if isinstance(absences, (list, tuple, set)):
                unmotivated = [
                    a for a in absences
                    if not (hasattr(a, "is_motivated") and a.is_motivated())
                ]
                abs_count = len(unmotivated)
            else:
                abs_count = absences or 0

            # Nume și prenume
            tk.Label(row_frame, text=f"  {s.get_last_name()} {s.get_first_name()}",
                     font=("Segoe UI", 11), bg=bg_row, fg=txt_color,
                     pady=15, width=26, anchor="w").pack(side="left", fill="x", expand=True)

            # Clasă
            tk.Label(row_frame, text=s.get_grade(), font=("Segoe UI", 11),
                     bg=bg_row, fg=txt_color, width=10).pack(side="left", fill="x", expand=True)

            # Note
            tk.Label(row_frame, text=marks_str, font=("Segoe UI", 10),
                     bg=bg_row, fg=txt_color, width=22).pack(side="left", fill="x", expand=True)

            # Medie
            tk.Label(row_frame, text=avg_str, font=("Segoe UI", 11, "bold"),
                     bg=bg_row, fg="#27AE60" if mark_values else txt_color, width=10).pack(side="left", fill="x", expand=True)

            # Nr. absențe
            tk.Label(row_frame, text=str(abs_count), font=("Segoe UI", 11, "bold"),
                     bg=bg_row, fg="#E74C3C" if abs_count > 0 else txt_color, width=12).pack(side="left", fill="x",
                                                                                            expand=True)

            # Acțiuni
            act_f = tk.Frame(row_frame, bg=bg_row, width=14)
            act_f.pack(side="left", fill="x", expand=True)
            btns = tk.Frame(act_f, bg=bg_row)
            btns.pack(expand=True)

            tk.Button(btns, text=" ✏️ ", bg="#F1C40F", fg="black", relief="flat",
                      command=lambda st=s: self.open_edit_modal(st),
                      cursor="hand2", padx=8).pack(side="left", padx=5)

            tk.Button(btns, text=" 🗑️ ", bg="#E74C3C", fg="white", relief="flat",
                      command=lambda st=s: self.confirm_delete(st),
                      cursor="hand2", padx=8).pack(side="left", padx=5)

    def open_edit_modal(self, student):
        StudentEditUi(self.parent, self.master.colors, student,
                      self.master.student_service, self.master.show_students, self.master.language_service)

    def confirm_delete(self, student):
        user_id = self.master.user.get_id_entity()
        ls = self.master.language_service

        title = ls.get_text(user_id, "confirm_title")
        question = ls.get_text(user_id, "confirm_delete_student").replace("{name}", student.get_last_name())

        answer = messagebox.askyesno(title, question)

        if answer:
            self.master.student_service.delete_student(student)
            grade_id = self.master.grade_service.delete_cascade(student.get_id_entity())
            if grade_id is not None:
                self.master.schedule_service.delete_cascade(grade_id)
                self.master.preset_service.delete_cascade(grade_id, self.master.user.get_id_entity())

            msg = ls.get_text(user_id, "msg_student_deleted").replace("{name}", student.get_last_name())
            self.master.show_toast(f"🗑️ {msg}", "#34495E")
            self.render()