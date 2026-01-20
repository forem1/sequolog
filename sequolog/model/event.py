"""Event model - single event with time or/and sequence information"""

from sequolog.model.time.time_base import TimeBase


class Event:
    def __init__(
        self,
        event_id: str,
        source_id: str,
        description: str,
        time: TimeBase,
        # TODO: implement "tags", "confidence" and "artifacts" features
    ):
        self.event_id = event_id
        self.source_id = source_id
        self.description = description
        self.time = time
