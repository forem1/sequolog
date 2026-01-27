"""Project model - top-level container for timelines and sources"""

from sequolog.model.event import Event
from sequolog.model.source import Source
from sequolog.model.timeline import Timeline


class Project:
    def __init__(self, project_id: str, title: str, description: str):
        self.project_id = project_id
        self.title = title
        self.description = description
        self._timelines: dict[str, Timeline] = {}
        self._sources: dict[str, Source] = {}

    # ========== Source Management ==========
    def add_source(self, source: Source) -> None:
        """Add source to project"""
        if self.has_source(source.source_id):
            raise ValueError(f"Source with ID '{source.source_id}' already exists in project")
        self._sources[source.source_id] = source

    def get_source(self, source_id: str) -> Source | None:
        """Get source by ID"""
        return self._sources.get(source_id)

    def has_source(self, source_id: str) -> bool:
        """Check if source exists"""
        return source_id in self._sources

    def remove_source(self, source_id: str) -> bool:
        """Remove source by ID. Returns True if removed"""
        return self._sources.pop(source_id, None) is not None

    def get_all_sources(self) -> list[Source]:
        """Get all sources as a list"""
        return list(self._sources.values())

    def update_source(self, source_id: str, source: Source) -> None:
        """Update source in project"""
        if not self.has_source(source_id):
            raise ValueError(f"Source with ID '{source_id}' not found in project")
        # If source_id changed, check for conflicts
        if source.source_id != source_id and self.has_source(source.source_id):
            raise ValueError(f"Source with ID '{source.source_id}' already exists in project")
        # Remove old entry if ID changed
        if source.source_id != source_id:
            self._sources.pop(source_id)
        self._sources[source.source_id] = source

    # ========== Timeline Management ==========
    def add_timeline(self, timeline: Timeline) -> None:
        """Add timeline to project"""
        if self.has_timeline(timeline.timeline_id):
            raise ValueError(f"Timeline with ID '{timeline.timeline_id}' already exists in project")
        self._timelines[timeline.timeline_id] = timeline

    def get_timeline(self, timeline_id: str) -> Timeline | None:
        """Get timeline by ID"""
        return self._timelines.get(timeline_id)

    def has_timeline(self, timeline_id: str) -> bool:
        """Check if timeline exists"""
        return timeline_id in self._timelines

    def remove_timeline(self, timeline_id: str) -> bool:
        """Remove timeline by ID. Returns True if removed"""
        return self._timelines.pop(timeline_id, None) is not None

    def get_all_timelines(self) -> list[Timeline]:
        """Get all timelines"""
        return list(self._timelines.values())

    # ========== Query Methods ==========
    def get_all_events(self) -> list[Event]:
        """Get all events from all timelines"""
        events = []
        for timeline in self._timelines.values():
            events.extend(timeline.get_all_events())
        return events

    def get_events_by_source(self, source_id: str) -> list[Event]:
        """Get all events from specific source across all timelines"""
        events = []
        for timeline in self._timelines.values():
            events.extend(timeline.get_events_by_source(source_id))
        return events

    def get_events_by_timeline(self, timeline_id: str) -> list[Event]:
        """Get all events from specific timeline"""
        timeline = self.get_timeline(timeline_id)
        return timeline.get_all_events() if timeline else []

    def get_timelines_with_event(self, event_id: str) -> list[Timeline]:
        """Get all timelines containing the event (usually one)"""
        return [t for t in self._timelines.values() if t.has_event(event_id)]

    def has_event(self, event_id: str) -> bool:
        """Check if event exists in any timeline"""
        return any(t.has_event(event_id) for t in self._timelines.values())

    def add_event_to_timeline(self, timeline_id: str, event: Event) -> None:
        """Add event to timeline with global uniqueness check"""
        if self.has_event(event.event_id):
            raise ValueError(f"Event with ID '{event.event_id}' already exists in project")
        timeline = self.get_timeline(timeline_id)
        if timeline is None:
            raise ValueError(f"Timeline with ID '{timeline_id}' not found in project")
        timeline.add_event(event)

    def update_event_in_timeline(self, timeline_id: str, event_id: str, event: Event) -> None:
        """Update event in timeline with global uniqueness check"""
        timeline = self.get_timeline(timeline_id)
        if timeline is None:
            raise ValueError(f"Timeline with ID '{timeline_id}' not found in project")
        if not timeline.has_event(event_id):
            raise ValueError(f"Event with ID '{event_id}' not found in timeline")
        # If event_id changed, check for global conflicts
        if event.event_id != event_id and self.has_event(event.event_id):
            raise ValueError(f"Event with ID '{event.event_id}' already exists in project")
        timeline.update_event(event_id, event)

    # ========== Statistics ==========
    def get_event_count(self) -> int:
        """Get total number of events across all timelines"""
        return sum(timeline.get_event_count() for timeline in self._timelines.values())

    def get_timeline_count(self) -> int:
        """Get total number of timelines"""
        return len(self._timelines)

    def get_source_count(self) -> int:
        """Get total number of sources"""
        return len(self._sources)
