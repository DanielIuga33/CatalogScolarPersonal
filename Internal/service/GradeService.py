from Internal.entity.Grade import Grade
from Internal.repository.RepositoryGrade import RepositoryGrade


class GradeService:
    def __init__(self, repository: RepositoryGrade):
        self.__repository = repository

    def set_repository_path(self, path, password):
        self.__repository.set_new_path(path, password)

    def add_grade(self, name, ids, teacher_id):
        if not name:
            return 400, "Numele și materia sunt obligatorii!"
        self.__repository.add_grade(name, ids, teacher_id)
        return 201, "Grupă creată cu succes!"

    def modify_grade(self, grade_old, grade_new):
        self.__repository.modify_grade(grade_old, grade_new)
        return [200, "Modificat cu succes !"]

    def get_grade_by_id(self, id_grade):
        return self.__repository.find_by_id(id_grade)

    def get_grade_students(self, id_grade):
        return self.get_grade_by_id(id_grade).get_student_ids()

    def delete_grade(self, grade_id: str):
        self.__repository.delete_grade(grade_id)

    def delete_cascade(self, student_id):
        for grade in self.__repository.get_all():
            if student_id in self.get_grade_students(grade.get_id_entity()):
                if len(self.get_grade_students(grade.get_id_entity())) < 2:
                    self.delete_grade(grade.get_id_entity())
                    return grade.get_id_entity()
                else:
                    students = grade.get_student_ids()
                    students.remove(student_id)
                    grade.set_student_ids(students)
                    self.__repository.modify_grade(grade, grade)
        return None

    def get_grades_for_teacher(self, teacher_id):
        result = []
        for grade in self.__repository.get_all():
            if grade.get_teacher_id() == teacher_id:
                result.append(grade)
        return result

    def size(self):
        return self.__repository.size()

    def add_student(self,grade_name, student_id):
        for grade in self.__repository.get_all():
            if grade_name == grade.get_grade_name():
                new_grade = grade
                new_student_ids = (grade.get_student_ids())
                new_student_ids.append(student_id)
                new_grade.set_student_ids(new_student_ids)
                self.__repository.modify_grade(grade, new_grade)

    def size_for_user(self, user_id):
        return len(self.get_grades_for_teacher(user_id))
