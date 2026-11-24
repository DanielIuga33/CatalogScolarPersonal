from datetime import datetime
import os
from Internal.security.EncryptionManager import EncryptionManager


class ScheduleService:
    def __init__(self):
        self.__filename = None
        self.__schedule_data = {}
        self.__current_password = None

    def set_schedule_path(self, new_data_path: str, password: str):
        if new_data_path:
            self.__current_password = password
            os.makedirs(new_data_path, exist_ok=True)

            self.__filename = os.path.join(new_data_path, "Schedule.enc")

            if not os.path.exists(self.__filename):
                EncryptionManager.encrypt_to_file(self.__filename, {}, self.__current_password)

            self.__schedule_data = self.load_schedule_data()

    def load_schedule_data(self):
        if not self.__filename or not os.path.exists(self.__filename):
            return {}

        data = EncryptionManager.decrypt_from_file(self.__filename, self.__current_password)

        # Ne asigurăm că returnează mereu dict, chiar dacă în fișier era salvată o listă
        return data if isinstance(data, dict) else {}

    def get_schedule_data(self):
        if not isinstance(self.__schedule_data, dict):
            self.__schedule_data = {}
        return self.__schedule_data

    def save_schedule_data(self):
        if not self.__filename:
            return
        EncryptionManager.encrypt_to_file(self.__filename, self.__schedule_data, self.__current_password)

    def get_today_sessions(self, uid):
        today = datetime.now().strftime("%Y-%m-%d")
        all_data = self.get_schedule_data()
        return {k: v for k, v in all_data.items() if k.startswith(f"{uid}_{today}")}

    def delete_cascade(self, id_grade):
        keys_to_delete = []
        current_data = self.get_schedule_data()

        for key, value in current_data.items():
            if isinstance(value, dict) and value.get('grade_id') == id_grade:
                keys_to_delete.append(key)

        if keys_to_delete:
            for key in keys_to_delete:
                del self.__schedule_data[key]
            self.save_schedule_data()