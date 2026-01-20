"""ExactTime model - exact moment in time (calendar or timestamp)"""

from sequolog.model.time.time_base import TimeBase, CalendarFields
from typing import Optional


class ExactTime(TimeBase):
    def __init__(
        self,
        calendar: Optional[CalendarFields] = None,
        timestamp: Optional[int] = None,
        uncertainty: Optional[TimeBase] = None,
        sequence: Optional[int] = None
    ):
        self.calendar = calendar
        self.timestamp = timestamp
        self.uncertainty = uncertainty
        self.sequence = sequence

