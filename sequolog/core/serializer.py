"""
Serialization and deserialization for sequolog models
Supports JSON format for Project, Timeline, Event, Source, and Time objects
"""

import json
from typing import Any, Dict, Optional
from pathlib import Path

from sequolog.model.project import Project
from sequolog.model.timeline import Timeline
from sequolog.model.event import Event
from sequolog.model.source import Source
from sequolog.model.time.exact_time import ExactTime
from sequolog.model.time.range_time import RangeTime
from sequolog.model.time.relative_time import RelativeTime
from sequolog.model.time.no_time import NoTime
from sequolog.model.time.time_base import CalendarFields, TimeBase


# ========== Serialization (to_dict) ==========


def calendar_fields_to_dict(calendar: Optional[CalendarFields]) -> Optional[Dict[str, Any]]:
    """Serialize CalendarFields to dict"""
    if calendar is None:
        return None
    return {
        "year": calendar.year,
        "month": calendar.month,
        "day": calendar.day,
        "hour": calendar.hour,
        "minute": calendar.minute,
        "second": calendar.second,
        "millisecond": calendar.millisecond,
        "tz_offset_minutes": calendar.tz_offset_minutes,
    }


def time_to_dict(time: TimeBase) -> Dict[str, Any]:
    """Serialize TimeBase to dict with type information"""
    result: Dict[str, Any] = {}
    
    # Determine time type
    if isinstance(time, ExactTime):
        result["type"] = "exact"
        if time.calendar:
            result["calendar"] = calendar_fields_to_dict(time.calendar)
        if time.timestamp is not None:
            result["timestamp"] = time.timestamp
    elif isinstance(time, RangeTime):
        result["type"] = "range"
        if time.start:
            result["start"] = calendar_fields_to_dict(time.start)
        if time.end:
            result["end"] = calendar_fields_to_dict(time.end)
        if time.timestamp is not None:
            result["timestamp"] = time.timestamp
    elif isinstance(time, RelativeTime):
        result["type"] = "relative"
        result["relative_to"] = time.relative_to
        result["offset_ms"] = time.offset_ms
    elif isinstance(time, NoTime):
        result["type"] = "none"
    else:
        raise ValueError(f"Unknown time type: {type(time)}")
    
    # Common fields
    if time.uncertainty is not None:
        result["uncertainty"] = time_to_dict(time.uncertainty)
    if time.sequence is not None:
        result["sequence"] = time.sequence
    
    return result


def event_to_dict(event: Event) -> Dict[str, Any]:
    """Serialize Event to dict"""
    return {
        "event_id": event.event_id,
        "source_id": event.source_id,
        "description": event.description,
        "time": time_to_dict(event.time),
    }


def source_to_dict(source: Source) -> Dict[str, Any]:
    """Serialize Source to dict"""
    return {
        "source_id": source.source_id,
        "description": source.description,
        "reference": source.reference,
    }


def timeline_to_dict(timeline: Timeline) -> Dict[str, Any]:
    """Serialize Timeline to dict"""
    return {
        "timeline_id": timeline.timeline_id,
        "description": timeline.description,
        "events": [event_to_dict(event) for event in timeline.events],
    }


def project_to_dict(project: Project) -> Dict[str, Any]:
    """Serialize Project to dict"""
    return {
        "project_id": project.project_id,
        "title": project.title,
        "description": project.description,
        "timelines": [timeline_to_dict(timeline) for timeline in project.timelines],
        "sources": [source_to_dict(source) for source in project.sources],
    }


# ========== Deserialization (from_dict) ==========


def calendar_fields_from_dict(data: Optional[Dict[str, Any]]) -> Optional[CalendarFields]:
    """Deserialize CalendarFields from dict"""
    if data is None:
        return None
    return CalendarFields(
        year=data.get("year"),
        month=data.get("month"),
        day=data.get("day"),
        hour=data.get("hour"),
        minute=data.get("minute"),
        second=data.get("second"),
        millisecond=data.get("millisecond"),
        tz_offset_minutes=data.get("tz_offset_minutes"),
    )


def time_from_dict(data: Dict[str, Any]) -> TimeBase:
    """Deserialize TimeBase from dict"""
    time_type = data.get("type")
    
    if time_type == "exact":
        calendar = calendar_fields_from_dict(data.get("calendar"))
        timestamp = data.get("timestamp")
        uncertainty = None
        if "uncertainty" in data:
            uncertainty = time_from_dict(data["uncertainty"])
        sequence = data.get("sequence")
        return ExactTime(
            calendar=calendar,
            timestamp=timestamp,
            uncertainty=uncertainty,
            sequence=sequence,
        )
    
    elif time_type == "range":
        start = calendar_fields_from_dict(data.get("start"))
        end = calendar_fields_from_dict(data.get("end"))
        timestamp = data.get("timestamp")
        uncertainty = None
        if "uncertainty" in data:
            uncertainty = time_from_dict(data["uncertainty"])
        sequence = data.get("sequence")
        return RangeTime(
            start=start,
            end=end,
            timestamp=timestamp,
            uncertainty=uncertainty,
            sequence=sequence,
        )
    
    elif time_type == "relative":
        relative_to = data.get("relative_to", "")
        offset_ms = data.get("offset_ms", 0)
        uncertainty = None
        if "uncertainty" in data:
            uncertainty = time_from_dict(data["uncertainty"])
        sequence = data.get("sequence")
        return RelativeTime(
            relative_to=relative_to,
            offset_ms=offset_ms,
            uncertainty=uncertainty,
            sequence=sequence,
        )
    
    elif time_type == "none":
        sequence = data.get("sequence")
        return NoTime(sequence=sequence)
    
    else:
        raise ValueError(f"Unknown time type: {time_type}")


def event_from_dict(data: Dict[str, Any]) -> Event:
    """Deserialize Event from dict"""
    return Event(
        event_id=data["event_id"],
        source_id=data["source_id"],
        description=data["description"],
        time=time_from_dict(data["time"]),
    )


def source_from_dict(data: Dict[str, Any]) -> Source:
    """Deserialize Source from dict"""
    return Source(
        source_id=data["source_id"],
        description=data["description"],
        reference=data["reference"],
    )


def timeline_from_dict(data: Dict[str, Any]) -> Timeline:
    """Deserialize Timeline from dict"""
    return Timeline(
        timeline_id=data["timeline_id"],
        description=data["description"],
        events=[event_from_dict(event_data) for event_data in data.get("events", [])],
    )


def project_from_dict(data: Dict[str, Any]) -> Project:
    """Deserialize Project from dict"""
    return Project(
        project_id=data["project_id"],
        title=data["title"],
        description=data.get("description", ""),
        timelines=[timeline_from_dict(tl_data) for tl_data in data.get("timelines", [])],
        sources=[source_from_dict(src_data) for src_data in data.get("sources", [])],
    )


# ========== File I/O ==========


def save_project(project: Project, filepath: str | Path, indent: int = 2) -> None:
    """
    Save project to JSON file
    
    Args:
        project: Project instance to save
        filepath: Path to output JSON file
        indent: JSON indentation (default: 2)
    """
    filepath = Path(filepath)
    data = project_to_dict(project)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_project(filepath: str | Path) -> Project:
    """
    Load project from JSON file
    
    Args:
        filepath: Path to input JSON file
    
    Returns:
        Project instance
    """
    filepath = Path(filepath)
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return project_from_dict(data)


def project_to_json(project: Project, indent: int = 2) -> str:
    """
    Convert project to JSON string
    
    Args:
        project: Project instance
        indent: JSON indentation (default: 2)
    
    Returns:
        JSON string
    """
    data = project_to_dict(project)
    return json.dumps(data, ensure_ascii=False, indent=indent)


def project_from_json(json_str: str) -> Project:
    """
    Create project from JSON string
    
    Args:
        json_str: JSON string
    
    Returns:
        Project instance
    """
    data = json.loads(json_str)
    return project_from_dict(data)
