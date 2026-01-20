"""Time base classes - CalendarFields and TimeBase abstract class"""

from abc import ABC
from dataclasses import dataclass
from typing import Optional


# TODO: Add check for correct dates
@dataclass
class CalendarFields:
    year: int | None = None
    month: int | None = None
    day: int | None = None
    hour: int | None = None
    minute: int | None = None
    second: int | None = None
    millisecond: int | None = None

    # Time zone in minutes from UTC (for example, 180 = +03:00, -300 = -05:00)
    tz_offset_minutes: int | None = None


class TimeBase(ABC):
    calendar: CalendarFields | None = None
    timestamp: int | None = None

    uncertainty: Optional["TimeBase"] = None

    sequence: int | None = None
