from Internal.entity.Entity import Entity


class Grade(Entity):
    def __init__(self, grade_name, student_ids, day, time_interval, teacher_id, **kwargs):
        super().__init__()
        if 'id_entity' in kwargs:
            self._Entity__id_entity = kwargs['id_entity']
        self.__grade_name = grade_name           # Numele grupei
        self.__student_ids = student_ids     # Listă cu ID-urile studenților (din Students.json)
        self.__day = day                     # Luni, Marți etc.
        self.__time_interval = time_interval  # ex: 14:00 - 16:00
        self.__teacher_id = teacher_id

    def get_grade_name(self):
        return self.__grade_name

    def set_grade_name(self, grade_name):
        self.__grade_name = grade_name

    def get_student_ids(self):
        return self.__student_ids

    def set_student_ids(self, student_ids):
        self.__student_ids = student_ids

    def get_day(self):
        return self.__day

    def set_day(self, day):
        return self.__day

    def get_time_interval(self):
        return self.__time_interval

    def set_time_interval(self, time_interval):
        self.__time_interval = time_interval

    def get_teacher_id(self):
        return self.__teacher_id

    def get_number_of_students(self):
        return len(self.__student_ids)

    def set_teacher_id(self, teacher_id):
        self.__teacher_id = teacher_id


    def get_display_name(self):
        return f"{self.grade_name} - {self.subject}"
