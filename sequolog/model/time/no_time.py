"""NoTime model - event without time information (only sequence)"""

from sequolog.model.time.time_base import TimeBase


class NoTime(TimeBase):
    def __init__(self, sequence: int = None):
        self.sequence = sequence

