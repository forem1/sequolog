"""RangeTime model - time range with start and/or end"""

from sequolog.model.time.time_base import TimeBase, CalendarFields
from typing import Optional


class RangeTime(TimeBase):
    def __init__(
        self,
        start: Optional[CalendarFields] = None,
        end: Optional[CalendarFields] = None,
        timestamp: Optional[int] = None,
        uncertainty: Optional[TimeBase] = None,
        sequence: Optional[int] = None
    ):
        self.start = start
        self.end = end
        self.timestamp = timestamp
        self.uncertainty = uncertainty
        self.sequence = sequence
