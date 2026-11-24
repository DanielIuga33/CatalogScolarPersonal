from datetime import date, datetime


class Absence:
    def __init__(self, absence_date: date, motivated: bool = False):
        self.__date = absence_date
        self.__motivated = motivated

    def get_date(self) -> date:
        return self.__date

    def set_date(self, absence_date: date):
        self.__date = absence_date

    def is_motivated(self) -> bool:
        return self.__motivated

    def set_motivated(self, motivated: bool):
        self.__motivated = motivated

    def to_dict(self) -> dict:
        d = self.__date
        date_str = d.strftime("%Y-%m-%d") if isinstance(d, (date, datetime)) else str(d)
        return {
            "date": date_str,
            "motivated": self.__motivated
        }

    @staticmethod
    def from_dict(data: dict):
        raw_date = data.get("date")
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date() if isinstance(raw_date, str) else raw_date
        return Absence(parsed_date, data.get("motivated", False))