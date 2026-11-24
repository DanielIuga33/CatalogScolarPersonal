import tkinter as tk
from tkinter import messagebox, ttk
from Internal.service.SettingsService import SettingsService
from Internal.service.StudentService import StudentService
from Internal.service.LanguageService import LanguageService
from Internal.service.GradeService import GradeService


class StudentAddUi(tk.Toplevel):
    def __init__(self, parent, theme, user_id, student_service: StudentService, grade_service: GradeService, on_success,
                 settings_service: SettingsService, lang_service: LanguageService):
        super().__init__(parent)
        self.theme = theme
        self.user_id = user_id
        self.student_service = student_service
        self.grade_service = grade_service
        self.on_success = on_success
        self.settings_service = settings_service
        self.lang_service = lang_service

        uid = self.user_id
        ls = self.lang_service

        self.colors = self.settings_service.get_colors(uid)
        self.txt_color = self.colors.get("schedule_text", self.colors["fg"])

        self.configure(bg=self.colors["bg"])

        # Titlu fereastră tradus
        self.title(ls.get_text(uid, "student_add_title"))
        self.setup_modal(350, 440)
        self.configure(padx=25, pady=25)
        self.grab_set()

        # Titlu Header tradus
        tk.Label(self, text=f"👤 {ls.get_text(uid, 'student_add_header')}", font=("Segoe UI", 16, "bold"),
                 bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 20))

        # Câmpuri
        self.entries = {}

        # Nume și Prenume traduse
        self.create_field(ls.get_text(uid, "reg_last_name"), "ln")
        self.create_field(ls.get_text(uid, "reg_first_name"), "fn")

        # Câmpul Clasă (dropdown cu clasele existente)
        tk.Label(self, text=ls.get_text(uid, "student_grade_label"), bg=self.colors["bg"],
                 fg=self.txt_color, font=("Segoe UI", 9, "bold")).pack(anchor="w")

        existing_grades = sorted(
            [g.get_grade_name() for g in self.grade_service.get_grades_for_teacher(uid)]
        )

        grade_cb = ttk.Combobox(self, values=existing_grades, state="readonly", font=("Segoe UI", 11))
        grade_cb.pack(fill="x", pady=(5, 15), ipady=4)

        if existing_grades:
            grade_cb.current(0)

        self.entries["gr"] = grade_cb

        # Buton Salvare tradus
        tk.Button(self, text=ls.get_text(uid, "btn_save_student"), command=self.handle_save,
                  bg=self.colors.get("success", "#2ECC71"), fg="white", font=("Segoe UI", 11, "bold"),
                  relief="flat", pady=12, cursor="hand2").pack(fill="x", pady=(15, 0))

    def create_field(self, label_text, key):
        """Helper pentru crearea câmpurilor cu contrast corect."""
        tk.Label(self, text=label_text, bg=self.colors["bg"], fg=self.txt_color,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")

        ent = tk.Entry(self, font=("Segoe UI", 11), relief="flat",
                       bg=self.colors["input_bg"],
                       fg=self.txt_color,
                       insertbackground=self.txt_color)
        ent.pack(fill="x", pady=(5, 15), ipady=5)
        self.entries[key] = ent

    def setup_modal(self, w, h):
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry(f'{w}x{h}+{int(x)}+{int(y)}')

    def handle_save(self):
        uid = self.user_id
        ls = self.lang_service
        fn = self.entries['fn'].get().strip()
        ln = self.entries['ln'].get().strip()
        gr = self.entries['gr'].get().strip()

        if not all([ln, fn, gr]):
            messagebox.showwarning(ls.get_text(uid, "warning"), ls.get_text(uid, "err_fill_fields"))
            return

        res = self.student_service.add_student(fn, ln, gr, [], [] , uid)

        if res[0] == 201:
            student_id = res[2]
            self.grade_service.add_student(gr, student_id)
            self.on_success()
            self.destroy()
        else:
            messagebox.showerror(ls.get_text(uid, "error"), res[1])