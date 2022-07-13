from typing import Optional

from camayoc.ui.types import HistoryRecord
from camayoc.ui.types import Session


class BasicSession(Session):
    def __init__(self):
        self.history: list[HistoryRecord] = []

    def last_record(self) -> Optional[HistoryRecord]:
        try:
            return self.history[-1]
        except IndexError:
            return None

    def add_record(self, record: HistoryRecord) -> None:
        self.history.append(record)


class DummySession(Session):
    def __init__(self):
        self.history: list[HistoryRecord] = []

    def last_record(self) -> Optional[HistoryRecord]:
        try:
            return self.history[0]
        except IndexError:
            return None

    def add_record(self, record: HistoryRecord) -> None:
        self.history = [record]
