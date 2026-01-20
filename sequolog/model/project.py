"""Project model - top-level container for timelines and sources"""

from sequolog.model.event import Event
from sequolog.model.source import Source
from sequolog.model.timeline import Timeline


class Project:
    def __init__(
        self,
        project_id: str,
        title: str,
        description: str,
        timelines: list[Timeline],
        sources: list[Source],
    ):
        self.project_id = project_id
        self.title = title
        self.description = description
        self.timelines = timelines
        self.sources = sources

    # ========== Source Management ==========
    def add_source(self, source: Source) -> None:
        """Add source to project"""
        if self.has_source(source.source_id):
            raise ValueError(f"Source with ID '{source.source_id}' already exists in project")
        self.sources.append(source)

    def get_source(self, source_id: str) -> Source | None:
        """Get source by ID"""
        return next((s for s in self.sources if s.source_id == source_id), None)

    def has_source(self, source_id: str) -> bool:
        """Check if source exists"""
        return any(s.source_id == source_id for s in self.sources)

    def remove_source(self, source_id: str) -> bool:
        """Remove source by ID. Returns True if removed"""
        initial_len = len(self.sources)
        self.sources = [s for s in self.sources if s.source_id != source_id]
        return len(self.sources) < initial_len

    def get_all_sources(self) -> list[Source]:
        """Get all sources"""
        return self.sources.copy()

    # ========== Timeline Management ==========
    def add_timeline(self, timeline: Timeline) -> None:
        """Add timeline to project"""
        if self.has_timeline(timeline.timeline_id):
            raise ValueError(f"Timeline with ID '{timeline.timeline_id}' already exists in project")
        self.timelines.append(timeline)

    def get_timeline(self, timeline_id: str) -> Timeline | None:
        """Get timeline by ID"""
        return next((t for t in self.timelines if t.timeline_id == timeline_id), None)

    def has_timeline(self, timeline_id: str) -> bool:
        """Check if timeline exists"""
        return any(t.timeline_id == timeline_id for t in self.timelines)

    def remove_timeline(self, timeline_id: str) -> bool:
        """Remove timeline by ID. Returns True if removed"""
        initial_len = len(self.timelines)
        self.timelines = [t for t in self.timelines if t.timeline_id != timeline_id]
        return len(self.timelines) < initial_len

    def get_all_timelines(self) -> list[Timeline]:
        """Get all timelines"""
        return self.timelines.copy()

    # ========== Query Methods ==========
    def get_all_events(self) -> list[Event]:
        """Get all events from all timelines"""
        events = []
        for timeline in self.timelines:
            events.extend(timeline.events)
        return events

    def get_events_by_source(self, source_id: str) -> list[Event]:
        """Get all events from specific source across all timelines"""
        events = []
        for timeline in self.timelines:
            events.extend(timeline.get_events_by_source(source_id))
        return events

    def get_events_by_timeline(self, timeline_id: str) -> list[Event]:
        """Get all events from specific timeline"""
        timeline = self.get_timeline(timeline_id)
        return timeline.events.copy() if timeline else []

    def get_timelines_with_event(self, event_id: str) -> list[Timeline]:
        """Get all timelines containing the event (usually one)"""
        return [t for t in self.timelines if t.has_event(event_id)]

    def has_event(self, event_id: str) -> bool:
        """Check if event exists in any timeline"""
        return any(t.has_event(event_id) for t in self.timelines)

    def add_event_to_timeline(self, timeline_id: str, event: Event) -> None:
        """Add event to timeline with global uniqueness check"""
        if self.has_event(event.event_id):
            raise ValueError(f"Event with ID '{event.event_id}' already exists in project")
        timeline = self.get_timeline(timeline_id)
        if timeline is None:
            raise ValueError(f"Timeline with ID '{timeline_id}' not found in project")
        timeline.add_event(event)

    # ========== Statistics ==========
    def get_event_count(self) -> int:
        """Get total number of events across all timelines"""
        return sum(len(timeline.events) for timeline in self.timelines)

    def get_timeline_count(self) -> int:
        """Get total number of timelines"""
        return len(self.timelines)

    def get_source_count(self) -> int:
        """Get total number of sources"""
        return len(self.sources)
