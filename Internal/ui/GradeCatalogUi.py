import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date, datetime
from collections import Counter, defaultdict
from tkcalendar import DateEntry
from Internal.entity.Absence import Absence
from Internal.entity.Mark import Mark


ROMAN_MONTHS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
    7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
}
# Ordinea lunilor în anul școlar (Septembrie -> Iunie)
SCHOOL_YEAR_ORDER = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8]


class GradeCatalogUi(tk.Toplevel):
    def __init__(self, parent, colors, grade, student_service):
        super().__init__(parent)
        self.colors = colors
        self.grade = grade
        self.student_service = student_service
        self.txt_color = colors.get("schedule_text", colors["fg"])

        self.title(f"Catalog - Clasa {grade.get_grade_name()}")
        self.configure(bg=colors["bg"], padx=25, pady=20)
        self.setup_modal(1350, 720)
        self.grab_set()

        self.render()

    def setup_modal(self, w, h):
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = max(0, int((ws / 2) - (w / 2)))
        y = max(0, int((hs / 2) - (h / 2)))
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _parse_date(self, raw_date):
        """Convertește sigur un obiect date/datetime sau string YYYY-MM-DD în date."""
        if isinstance(raw_date, datetime):
            return raw_date.date()
        if isinstance(raw_date, date):
            return raw_date
        if isinstance(raw_date, str):
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    return datetime.strptime(raw_date, fmt).date()
                except ValueError:
                    continue
        return None

    def _format_absences(self, absences):
        """Formatează absențele pe luni cu cifre romane, ex: X: 1, 5²"""
        superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        by_month = defaultdict(list)

        for a in absences:
            d = self._parse_date(a.get_date() if hasattr(a, "get_date") else a)
            if d:
                by_month[d.month].append(d.day)

        if not by_month:
            return "-"

        lines = []
        for m in SCHOOL_YEAR_ORDER:
            if m in by_month:
                day_counts = Counter(by_month[m])
                parts = []
                for day in sorted(day_counts.keys()):
                    cnt = day_counts[day]
                    power = str(cnt).translate(superscript_map)
                    parts.append(f"{day}{power}" if cnt > 1 else str(day))
                lines.append(f"{ROMAN_MONTHS[m]}: {', '.join(parts)}")
        return "\n".join(lines)

    def _format_marks(self, marks):
        """Formatează notele cu data și luna în cifre romane, ex: 10/12XI, 9/5X"""
        if not marks:
            return "-", []

        formatted = []
        values = []
        for m in marks:
            val = m.get_mark() if hasattr(m, "get_mark") else int(m)
            values.append(val)
            d = self._parse_date(m.get_date()) if hasattr(m, "get_date") else None
            if d:
                roman_month = ROMAN_MONTHS.get(d.month, str(d.month))
                formatted.append(f"{val}/{d.day}{roman_month}")
            else:
                formatted.append(str(val))
        return ", ".join(formatted), values

    def _persist_students(self, student):
        self.student_service.modify_student(student, student)

    def open_add_absence_modal(self, student):
        """Fereastră rapidă: acceptă o zi sau mai multe separate prin virgulă, ex: 1, 5, 6^3, 11"""
        modal = tk.Toplevel(self)
        modal.title("Adaugă Absențe")
        modal.configure(bg=self.colors["bg"], padx=25, pady=20)
        modal.grab_set()

        w, h = 370, 250
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        modal.geometry(f"{w}x{h}+{x}+{y}")

        today = date.today()
        month_options = [
            "09 - Septembrie", "10 - Octombrie", "11 - Noiembrie", "12 - Decembrie",
            "01 - Ianuarie", "02 - Februarie", "03 - Martie", "04 - Aprilie",
            "05 - Mai", "06 - Iunie", "07 - Iulie", "08 - August"
        ]

        tk.Label(modal, text=f"{student.get_last_name()} {student.get_first_name()}",
                 font=("Segoe UI", 12, "bold"), bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 12))

        # Luna
        tk.Label(modal, text="Luna:", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["bg"], fg=self.txt_color).pack(anchor="w")
        month_cb = ttk.Combobox(modal, values=month_options, state="readonly", font=("Segoe UI", 10))
        month_cb.pack(fill="x", pady=(4, 12), ipady=4)

        current_prefix = f"{today.month:02d} -"
        for idx, opt in enumerate(month_options):
            if opt.startswith(current_prefix):
                month_cb.current(idx)
                break

        # Zile (suportă format 1, 5, 6^3, 11)
        tk.Label(modal, text="Zile (ex: 1, 5, 6^3, 11):", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["bg"], fg=self.txt_color).pack(anchor="w")
        days_var = tk.StringVar(value=str(today.day))
        days_entry = tk.Entry(modal, textvariable=days_var, font=("Segoe UI", 11),
                              bg=self.colors["input_bg"], fg=self.txt_color,
                              insertbackground=self.txt_color, relief="flat")
        days_entry.pack(fill="x", pady=(4, 18), ipady=5)

        days_entry.focus()
        days_entry.select_range(0, tk.END)

        def save(event=None):
            raw_input = days_var.get().strip()
            if not raw_input:
                messagebox.showwarning("Atenție", "Introdu cel puțin o zi.", parent=modal)
                return

            month_val = int(month_cb.get().split(" - ")[0])
            entries_to_add = []

            for token in raw_input.split(","):
                token = token.strip()
                if not token:
                    continue

                try:
                    if "^" in token:
                        day_part, count_part = token.split("^", 1)
                        day_val = int(day_part.strip())
                        count_val = int(count_part.strip())
                    else:
                        day_val = int(token)
                        count_val = 1

                    if count_val < 1 or count_val > 10:
                        raise ValueError("Număr invalid de absențe")

                    selected_date = date(today.year, month_val, day_val)
                    entries_to_add.append((selected_date, count_val))
                except ValueError:
                    messagebox.showwarning(
                        "Format invalid",
                        f"Valoarea '{token}' nu este validă pentru luna selectată.\nFolosește formatul: 1, 5, 6^3, 11",
                        parent=modal
                    )
                    return

            for selected_date, count_val in entries_to_add:
                for _ in range(count_val):
                    student.add_absence(Absence(selected_date))

            self._persist_students(student)
            modal.destroy()
            self.render()

        modal.bind("<Return>", save)

        tk.Button(modal, text="Salvează Absențele", command=save,
                  bg="#E67E22", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=9, cursor="hand2").pack(fill="x")

        def save(event=None):
            try:
                day_val = int(day_var.get().strip())
                month_val = int(month_cb.get().split(" - ")[0])
                selected_date = date(today.year, month_val, day_val)
            except ValueError:
                messagebox.showwarning("Atenție", "Data introdusă nu este validă (verifică ziua și luna).",
                                       parent=modal)
                return

            raw_count = count_var.get().strip()
            if not raw_count:
                count_val = 1
            else:
                try:
                    count_val = int(raw_count)
                    if count_val < 1 or count_val > 10:
                        raise ValueError
                except ValueError:
                    messagebox.showwarning("Atenție", "Numărul de absențe trebuie să fie între 1 și 10.", parent=modal)
                    return

            for _ in range(count_val):
                student.add_absence(Absence(selected_date))

            self._persist_students(student)
            modal.destroy()
            self.render()

        modal.bind("<Return>", save)

        tk.Button(modal, text="Salvează Absența", command=save,
                  bg="#E67E22", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=9, cursor="hand2").pack(fill="x")

    def open_add_mark_modal(self, student):
        """Fereastră rapidă: notă + zi + lună, cu salvare pe Enter."""
        modal = tk.Toplevel(self)
        modal.title("Adaugă Notă")
        modal.configure(bg=self.colors["bg"], padx=25, pady=20)
        modal.grab_set()

        w, h = 340, 270
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        modal.geometry(f"{w}x{h}+{x}+{y}")

        today = date.today()
        month_options = [
            "09 - Septembrie", "10 - Octombrie", "11 - Noiembrie", "12 - Decembrie",
            "01 - Ianuarie", "02 - Februarie", "03 - Martie", "04 - Aprilie",
            "05 - Mai", "06 - Iunie", "07 - Iulie", "08 - August"
        ]

        tk.Label(modal, text=f"{student.get_last_name()} {student.get_first_name()}",
                 font=("Segoe UI", 12, "bold"), bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 12))

        tk.Label(modal, text="Nota (1 - 10):", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["bg"], fg=self.txt_color).pack(anchor="w")
        mark_var = tk.StringVar()
        mark_entry = tk.Entry(modal, textvariable=mark_var, font=("Segoe UI", 11),
                              bg=self.colors["input_bg"], fg=self.txt_color,
                              insertbackground=self.txt_color, relief="flat")
        mark_entry.pack(fill="x", pady=(4, 12), ipady=5)
        mark_entry.focus()

        # Rând Zi + Lună
        date_frame = tk.Frame(modal, bg=self.colors["bg"])
        date_frame.pack(fill="x", pady=(0, 18))

        day_col = tk.Frame(date_frame, bg=self.colors["bg"])
        day_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(day_col, text="Ziua:", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["bg"], fg=self.txt_color).pack(anchor="w")
        day_var = tk.StringVar(value=str(today.day))
        tk.Entry(day_col, textvariable=day_var, font=("Segoe UI", 11),
                 bg=self.colors["input_bg"], fg=self.txt_color,
                 insertbackground=self.txt_color, relief="flat", width=6).pack(fill="x", pady=(4, 0), ipady=5)

        month_col = tk.Frame(date_frame, bg=self.colors["bg"])
        month_col.pack(side="left", fill="x", expand=True)
        tk.Label(month_col, text="Luna:", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["bg"], fg=self.txt_color).pack(anchor="w")
        month_cb = ttk.Combobox(month_col, values=month_options, state="readonly", font=("Segoe UI", 10))
        month_cb.pack(fill="x", pady=(4, 0), ipady=4)

        current_prefix = f"{today.month:02d} -"
        for idx, opt in enumerate(month_options):
            if opt.startswith(current_prefix):
                month_cb.current(idx)
                break

        def save(event=None):
            try:
                val = int(mark_var.get().strip())
                if not (1 <= val <= 10):
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Atenție", "Introdu o notă întreagă între 1 și 10.", parent=modal)
                return

            try:
                day_val = int(day_var.get().strip())
                month_val = int(month_cb.get().split(" - ")[0])
                selected_date = date(today.year, month_val, day_val)
            except ValueError:
                messagebox.showwarning("Atenție", "Data introdusă nu este validă.", parent=modal)
                return

            student.add_mark(Mark(val, selected_date))
            self._persist_students(student)
            modal.destroy()
            self.render()

        modal.bind("<Return>", save)

        tk.Button(modal, text="Salvează Nota", command=save,
                  bg="#27AE60", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=9, cursor="hand2").pack(fill="x")

        def save():
            try:
                val = int(mark_var.get().strip())
                if not (1 <= val <= 10):
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Atenție", "Introdu o notă întreagă între 1 și 10.", parent=modal)
                return

            selected_date = cal.get_date()
            student.add_mark(Mark(val, selected_date))
            self._persist_students(student)
            modal.destroy()
            self.render()

        tk.Button(modal, text="Salvează Nota", command=save,
                  bg="#27AE60", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=8, cursor="hand2").pack(fill="x")

    def render(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Header
        header = tk.Frame(self, bg=self.colors["bg"])
        header.pack(fill="x", pady=(0, 15))

        tk.Label(
            header,
            text=f"📘 Catalog Clasa {self.grade.get_grade_name()}",
            font=("Segoe UI", 22, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["fg"]
        ).pack(side="left")

        # Container cu scroll
        container = tk.Frame(self, bg=self.colors["bg"])
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        table = tk.Frame(canvas, bg=self.colors["bg"])
        win_id = canvas.create_window((0, 0), window=table, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        table.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        # Header tabel
        hdr = tk.Frame(table, bg=self.colors["input_bg"])
        hdr.pack(fill="x", pady=(0, 4))

        cols = [
            ("ELEV", 22, "w"),
            ("ABSENȚE", 28, "w"),
            ("NOTE", 30, "w"),
            ("MEDIE", 8, "center"),
            ("ACȚIUNI", 20, "center")
        ]
        for title, w, anc in cols:
            tk.Label(hdr, text=title, font=("Segoe UI", 10, "bold"),
                     bg=self.colors["input_bg"], fg=self.txt_color,
                     width=w, pady=15, anchor=anc, padx=10).pack(side="left", expand=True, fill="x")

        # Elevii din clasă
        teacher_id = self.grade.get_teacher_id()
        grade_name = self.grade.get_grade_name().strip().lower()
        grade_ids = {str(s_id) for s_id in self.grade.get_student_ids()}

        all_students = self.student_service.get_sorted_students(teacher_id, "name")
        students = [
            s for s in all_students
            if str(s.get_id_entity()) in grade_ids
            or str(s.get_grade()).strip().lower() == grade_name
        ]
        students.sort(key=lambda st: (st.get_last_name(), st.get_first_name()))

        if not students:
            tk.Label(
                table,
                text="Nu există studenți în această clasă.",
                font=("Segoe UI", 12),
                bg=self.colors["bg"],
                fg="#888888",
                pady=40
            ).pack()
            return

        for idx, s in enumerate(students):
            bg_row = self.colors["card_bg"] if idx % 2 == 0 else self.colors["input_bg"]
            row = tk.Frame(table, bg=bg_row, pady=12)
            row.pack(fill="x", pady=3)

            # Nume elev
            tk.Label(
                row,
                text=f"{s.get_last_name()} {s.get_first_name()}",
                font=("Segoe UI", 11, "bold"),
                bg=bg_row,
                fg=self.txt_color,
                width=22,
                anchor="w",
                padx=10
            ).pack(side="left", expand=True, fill="x")

            # Absențe (click dreapta pe o zi -> motivare cu cerc verde)
            self._render_absences_cell(row, s, bg_row)

            # Note (cu dată și lună)
            marks_str, mark_values = self._format_marks(s.get_marks())
            tk.Label(
                row,
                text=marks_str,
                font=("Segoe UI", 10),
                bg=bg_row,
                fg=self.txt_color,
                width=30,
                anchor="w",
                justify="left",
                wraplength=260,
                padx=10
            ).pack(side="left", expand=True, fill="x")

            # Medie
            avg_str = f"{sum(mark_values) / len(mark_values):.2f}" if mark_values else "-"
            tk.Label(
                row,
                text=avg_str,
                font=("Segoe UI", 11, "bold"),
                bg=bg_row,
                fg="#2ECC71" if mark_values else self.txt_color,
                width=8
            ).pack(side="left", expand=True, fill="x")

            # Acțiuni (+ Notă și + Absență)
            act_f = tk.Frame(row, bg=bg_row, width=20)
            act_f.pack(side="left", expand=True, fill="x")
            btns = tk.Frame(act_f, bg=bg_row)
            btns.pack(expand=True)

            tk.Button(
                btns,
                text="+ Notă",
                bg="#27AE60",
                fg="white",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=6,
                command=lambda st=s: self.open_add_mark_modal(st)
            ).pack(side="left", padx=4)

            tk.Button(
                btns,
                text="+ Absență",
                bg="#E67E22",
                fg="white",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=6,
                command=lambda st=s: self.open_add_absence_modal(st)
            ).pack(side="left", padx=4)

    def _toggle_motivate_day(self, student, month_num, day_num):
        """Comută starea motivată/nemotivată pentru absențele dintr-o anumită zi."""
        day_absences = []
        for a in student.get_absences():
            d = self._parse_date(a.get_date() if hasattr(a, "get_date") else a)
            if d and d.month == month_num and d.day == day_num:
                day_absences.append(a)

        if not day_absences:
            return

        # Dacă toate sunt deja motivate, le demotivăm; altfel le motivăm pe toate din acea zi
        all_motivated = all(a.is_motivated() for a in day_absences if hasattr(a, "is_motivated"))
        new_state = not all_motivated

        for a in day_absences:
            if hasattr(a, "set_motivated"):
                a.set_motivated(new_state)

        self._persist_students(student)
        self.render()

    def _render_absences_cell(self, parent_row, student, bg_row):
        """Randează absențele pe luni, cu cerc verde la click dreapta pentru cele motivate."""
        superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        container = tk.Frame(parent_row, bg=bg_row, width=28)
        container.pack(side="left", expand=True, fill="x", padx=10)

        # Grupăm absențele pe (lună -> zi -> listă de obiecte Absence)
        by_month = defaultdict(lambda: defaultdict(list))
        for a in student.get_absences():
            d = self._parse_date(a.get_date() if hasattr(a, "get_date") else a)
            if d:
                by_month[d.month][d.day].append(a)

        if not by_month:
            tk.Label(container, text="-", font=("Segoe UI", 10),
                     bg=bg_row, fg="#7F8C8D", anchor="w").pack(anchor="w")
            return

        for m in SCHOOL_YEAR_ORDER:
            if m not in by_month:
                continue

            month_frame = tk.Frame(container, bg=bg_row)
            month_frame.pack(anchor="w", pady=2)

            tk.Label(month_frame, text=f"{ROMAN_MONTHS[m]}:", font=("Segoe UI", 10, "bold"),
                     bg=bg_row, fg=self.txt_color).pack(side="left", padx=(0, 4))

            days_sorted = sorted(by_month[m].keys())
            for i, day in enumerate(days_sorted):
                abs_list = by_month[m][day]
                cnt = len(abs_list)
                power = str(cnt).translate(superscript_map) if cnt > 1 else ""
                text = f"{day}{power}"

                is_motivated = all(a.is_motivated() for a in abs_list if hasattr(a, "is_motivated"))
                fg_color = "#2ECC71" if is_motivated else "#E74C3C"

                # Calculăm lățimea canvas-ului în funcție de lungimea textului (ex: "5" vs "24³")
                w_canvas = max(28, len(text) * 10 + 12)
                h_canvas = 26

                c = tk.Canvas(month_frame, width=w_canvas, height=h_canvas,
                              bg=bg_row, highlightthickness=0, cursor="hand2")
                c.pack(side="left", padx=1)

                if is_motivated:
                    c.create_oval(2, 2, w_canvas - 2, h_canvas - 2, outline="#2ECC71", width=1.8)

                c.create_text(w_canvas // 2, h_canvas // 2, text=text,
                              fill=fg_color, font=("Segoe UI", 10, "bold" if is_motivated else "normal"))

                # Click dreapta -> motivează / demotivează
                c.bind("<Button-3>", lambda e, st=student, mn=m, dn=day: self._toggle_motivate_day(st, mn, dn))

                # Virgulă între zile
                if i < len(days_sorted) - 1:
                    tk.Label(month_frame, text=",", font=("Segoe UI", 10),
                             bg=bg_row, fg="#7F8C8D").pack(side="left")