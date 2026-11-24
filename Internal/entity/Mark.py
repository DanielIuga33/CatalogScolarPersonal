from datetime import date, datetime


class Mark:
    def __init__(self, mark: int, mark_date: date):
        self.__mark = mark
        self.__date = mark_date

    def get_mark(self) -> int:
        return self.__mark

    def set_mark(self, mark: int):
        self.__mark = mark

    def get_date(self) -> date:
        return self.__date

    def set_date(self, mark_date: date):
        self.__date = mark_date

    def to_dict(self) -> dict:
        d = self.__date
        date_str = d.strftime("%Y-%m-%d") if isinstance(d, (date, datetime)) else str(d)
        return {
            "mark": self.__mark,
            "date": date_str
        }

    @staticmethod
    def from_dict(data: dict):
        raw_date = data.get("date")
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date() if isinstance(raw_date, str) else raw_date
        return Mark(int(data.get("mark")), parsed_date)