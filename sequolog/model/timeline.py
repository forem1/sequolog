"""Timeline model - sequence of events"""

from sequolog.model.event import Event


class Timeline:
    def __init__(self, timeline_id: str, description: str):
        self.timeline_id = timeline_id
        self.description = description
        self._events: dict[str, Event] = {}

    # TODO: implement "type" feature

    def add_event(self, event: Event) -> None:
        """Add event to timeline"""
        if self.has_event(event.event_id):
            raise ValueError(f"Event with ID '{event.event_id}' already exists in timeline")
        self._events[event.event_id] = event

    def get_event(self, event_id: str) -> Event | None:
        """Get event by ID"""
        return self._events.get(event_id)

    def has_event(self, event_id: str) -> bool:
        """Check if event exists"""
        return event_id in self._events

    def remove_event(self, event_id: str) -> bool:
        """Remove event by ID. Returns True if removed"""
        return self._events.pop(event_id, None) is not None

    def update_event(self, event_id: str, event: Event) -> None:
        """Update event in timeline"""
        if not self.has_event(event_id):
            raise ValueError(f"Event with ID '{event_id}' not found in timeline")
        # If event_id changed, check for conflicts
        if event.event_id != event_id and self.has_event(event.event_id):
            raise ValueError(f"Event with ID '{event.event_id}' already exists in timeline")
        # Remove old entry if ID changed
        if event.event_id != event_id:
            self._events.pop(event_id)
        self._events[event.event_id] = event

    def get_all_events(self) -> list[Event]:
        """Get all events as a list"""
        return list(self._events.values())

    def get_events_by_source(self, source_id: str) -> list[Event]:
        """Get all events from specific source"""
        return [e for e in self._events.values() if e.source_id == source_id]

    def get_event_count(self) -> int:
        """Get total number of events"""
        return len(self._events)

    def is_empty(self) -> bool:
        """Check if timeline has no events"""
        return len(self._events) == 0
