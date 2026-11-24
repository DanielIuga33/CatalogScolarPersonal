import os
from Internal.entity.Grade import Grade
from Internal.security.EncryptionManager import EncryptionManager


class RepositoryGrade:
    def __init__(self, user_data_path: str, session_password: str):
        # 1. Inițializăm variabilele
        self.__grade_list = []
        self.__filename = None
        self.__current_password = session_password  # Parola din RAM

        if user_data_path:
            os.makedirs(user_data_path, exist_ok=True)
            # Modificăm extensia în .enc
            self.__filename = os.path.join(user_data_path, "Grades.enc")

            # 2. Dacă fișierul nu există, îl creăm criptat cu o listă goală
            if not os.path.exists(self.__filename):
                EncryptionManager.encrypt_to_file(self.__filename, [], self.__current_password)

            # 3. Citim datele folosind decriptarea
            self.__grade_list = self.__read()

    def __read(self):
        """Decriptează fișierul binar în obiecte grade."""
        if not self.__filename or not os.path.exists(self.__filename):
            return []

        # Managerul returnează None dacă parola e greșită
        temp = EncryptionManager.decrypt_from_file(self.__filename, self.__current_password)

        if temp is None:
            return []

        # Reconstruim obiectele folosind datele decriptate
        return [Grade(**date) for date in temp]

    def __save(self):
        """Salvează grupele folosind criptarea AES."""
        if not self.__filename:
            return

        temp = []
        for g in self.__grade_list:
            data = {
                "id_entity": g.get_id_entity(),
                "grade_name": g.get_grade_name(),
                "student_ids": g.get_student_ids(),
                "day": g.get_day(),
                "time_interval": g.get_time_interval(),
                "teacher_id": g.get_teacher_id(),
            }
            temp.append(data)

        # Scriem binar pe disc via EncryptionManager
        EncryptionManager.encrypt_to_file(self.__filename, temp, self.__current_password)

    # --- Metodele de business rămân identice, ele apelează self.__save() care e acum securizată ---
    def add_or_update_grade(self, cell_id, grade_obj):
        self.__grade_list[cell_id] = grade_obj
        self.__save()

    def add_grade(self, name, ids, teacher_id):
        self.__grade_list.append(Grade(grade_name=name, student_ids=ids, day="", time_interval="",
                                       teacher_id=teacher_id, ))
        self.__save()

    def find_by_id(self, id_grade):
        for g in self.__grade_list:
            if g.get_id_entity() == id_grade:
                return g
        return None

    def delete_grade(self, cell_id):
        grade = self.find_by_id(cell_id)
        if grade:
            self.__grade_list.remove(grade)
            self.__save()

    def modify_grade(self, grade_old, grade_new):
        if grade_old in self.__grade_list:
            self.__grade_list.remove(grade_old)
            self.__grade_list.append(grade_new)
            self.__save()

    def get_all(self):
        return self.__grade_list

    def size(self):
        return len(self.__grade_list)

    def set_new_path(self, new_data_path: str, password: str):
        if new_data_path:
            # Aici salvăm parola primită de la login!
            self.__current_password = password

            os.makedirs(new_data_path, exist_ok=True)
            self.__filename = os.path.join(new_data_path, "Grades.enc")

            # Acum, când apelăm encrypt_to_file, self.__current_password nu mai este None
            if not os.path.exists(self.__filename):
                EncryptionManager.encrypt_to_file(self.__filename, [], self.__current_password)

            self.__grade_list = self.__read()

    def update_encryption_password(self, new_password):
        """
        Re-criptează datele actuale cu o nouă parolă.
        """
        # 1. Actualizăm parola în variabila privată a repository-ului
        self.__current_password = new_password

        # 2. Forțăm o salvare. Metoda __save() va folosi automat
        # noua valoare din self.__current_password pentru criptare.
        self.__save()
