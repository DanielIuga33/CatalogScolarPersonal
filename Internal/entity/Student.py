from datetime import date, datetime
from Internal.entity.Entity import Entity


class Student(Entity):
    def __init__(self, first_name: str, last_name: str, grade: str, marks=None, absences=None, teacher_id: str = "", **kwargs):
        super().__init__()
        if 'id_entity' in kwargs:
            self._Entity__id_entity = kwargs['id_entity']
        self.__first_name = first_name
        self.__last_name = last_name
        self.__grade = grade
        self.__marks = marks if marks is not None else []
        self.__absences = absences if absences is not None else []
        self.__teacher_id = teacher_id

    def get_full_name(self):
        return f"{self.__first_name} {self.__last_name}"

    def get_first_name(self):
        return self.__first_name

    def set_first_name(self, first_name):
        self.__first_name = first_name

    def get_last_name(self):
        return self.__last_name

    def set_last_name(self, last_name):
        self.__last_name = last_name

    def get_grade(self):
        return self.__grade

    def set_grade(self, grade):
        self.__grade = grade

    def add_mark(self, mark):
        self.__marks.append(mark)

    def set_marks(self, marks):
        self.__marks = marks

    def get_marks(self):
        return self.__marks

    def add_absence(self, absence):
        self.__absences.append(absence)

    def set_absences(self, absences):
        self.__absences = absences

    def get_absences(self):
        return self.__absences

    def get_absences_for_month(self, month_num: int):
        """Returnează lista absențelor dintr-o anumită lună (1-12)."""
        result = []
        for a in self.__absences:
            d = a.get_date() if hasattr(a, "get_date") else a
            if isinstance(d, str):
                try:
                    d = datetime.strptime(d, "%Y-%m-%d").date()
                except ValueError:
                    continue
            if isinstance(d, (date, datetime)) and d.month == month_num:
                result.append(a)
        return result

    def get_teacher_id(self):
        return self.__teacher_id

    def set_teacher_id(self, teacher_id):
        self.__teacher_id = teacher_id