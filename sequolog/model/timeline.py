"""Timeline model - sequence of events"""

from sequolog.model.event import Event


class Timeline:
    def __init__(
        self,
        timeline_id: str,
        description: str,
        events: list[Event],
        # TODO: implement "type" feature
    ):
        self.timeline_id = timeline_id
        self.description = description
        self.events = events

    def add_event(self, event: Event) -> None:
        """Add event to timeline"""
        if self.has_event(event.event_id):
            raise ValueError(f"Event with ID '{event.event_id}' already exists in timeline")
        self.events.append(event)

    def remove_event(self, event_id: str) -> bool:
        """Remove event by ID. Returns True if removed"""
        initial_len = len(self.events)
        self.events = [e for e in self.events if e.event_id != event_id]
        return len(self.events) < initial_len

    def get_event(self, event_id: str) -> Event | None:
        """Get event by ID"""
        return next((e for e in self.events if e.event_id == event_id), None)

    def has_event(self, event_id: str) -> bool:
        """Check if event exists"""
        return any(e.event_id == event_id for e in self.events)

    def get_events_by_source(self, source_id: str) -> list[Event]:
        """Get all events from specific source"""
        return [e for e in self.events if e.source_id == source_id]

    def get_event_count(self) -> int:
        """Get total number of events"""
        return len(self.events)

    def is_empty(self) -> bool:
        """Check if timeline has no events"""
        return len(self.events) == 0
