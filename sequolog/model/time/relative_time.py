"""RelativeTime model - time relative to another event"""

from sequolog.model.time.time_base import TimeBase
from typing import Optional


class RelativeTime(TimeBase):
    def __init__(
        self,
        relative_to: str,
        offset_ms: int = 0,
        uncertainty: Optional[TimeBase] = None,
        sequence: Optional[int] = None
    ):
        self.relative_to = relative_to
        self.offset_ms = offset_ms
        self.uncertainty = uncertainty
        self.sequence = sequence
