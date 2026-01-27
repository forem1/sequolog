"""temporal analysis methods for events and timelines"""

import math
import statistics
from datetime import UTC, datetime, timedelta, timezone

from sequolog.model.event import Event
from sequolog.model.project import Project
from sequolog.model.time.exact_time import ExactTime
from sequolog.model.time.no_time import NoTime
from sequolog.model.time.range_time import RangeTime
from sequolog.model.time.relative_time import RelativeTime
from sequolog.model.time.time_base import CalendarFields, TimeBase
from sequolog.model.timeline import Timeline

# ========== Helper Functions ==========


def _calendar_to_timestamp_ms(calendar: CalendarFields) -> int | None:
    """Convert CalendarFields to timestamp in milliseconds"""
    if calendar is None:
        return None

    # Use defaults for missing fields
    year = calendar.year if calendar.year is not None else 1970
    month = calendar.month if calendar.month is not None else 1
    day = calendar.day if calendar.day is not None else 1
    hour = calendar.hour if calendar.hour is not None else 0
    minute = calendar.minute if calendar.minute is not None else 0
    second = calendar.second if calendar.second is not None else 0
    millisecond = calendar.millisecond if calendar.millisecond is not None else 0

    try:
        tz = UTC
        if calendar.tz_offset_minutes is not None:
            tz = timezone(timedelta(minutes=calendar.tz_offset_minutes))

        dt = datetime(year, month, day, hour, minute, second, millisecond * 1000, tz)
        return int(dt.timestamp() * 1000)
    except (ValueError, OverflowError):
        return None


def _get_time_value(time: TimeBase) -> int | None:
    """Extract timestamp value from TimeBase (in milliseconds)"""
    if time is None:
        return None

    # If timestamp is directly available, use it (convert seconds to ms if needed)
    if hasattr(time, "timestamp") and time.timestamp is not None:
        # Assume timestamp is in seconds, convert to milliseconds
        ts = time.timestamp
        # If timestamp is already in milliseconds (very large), use as is
        # Otherwise assume seconds and convert
        if ts < 1e10:  # Likely seconds
            return int(ts * 1000)
        return int(ts)

    # For ExactTime with calendar
    if isinstance(time, ExactTime) and time.calendar is not None:
        return _calendar_to_timestamp_ms(time.calendar)

    # For RangeTime, use start or end
    if isinstance(time, RangeTime):
        if time.start is not None:
            return _calendar_to_timestamp_ms(time.start)
        if time.end is not None:
            return _calendar_to_timestamp_ms(time.end)

    # For RelativeTime, cannot resolve without context
    if isinstance(time, RelativeTime):
        return None

    # For NoTime, no time value
    if isinstance(time, NoTime):
        return None

    return None


def _get_time_range(time: TimeBase) -> tuple[int | None, int | None]:
    """Get time range (start, end) from TimeBase in milliseconds"""
    if time is None:
        return None, None

    if isinstance(time, ExactTime):
        ts = _get_time_value(time)
        return ts, ts

    if isinstance(time, RangeTime):
        start_ts = None
        end_ts = None
        if time.start is not None:
            start_ts = _calendar_to_timestamp_ms(time.start)
        if time.end is not None:
            end_ts = _calendar_to_timestamp_ms(time.end)
        if time.timestamp is not None:
            ts = int(time.timestamp * 1000) if time.timestamp < 1e10 else int(time.timestamp)
            if start_ts is None:
                start_ts = ts
            if end_ts is None:
                end_ts = ts
        return start_ts, end_ts

    if isinstance(time, RelativeTime):
        return None, None

    if isinstance(time, NoTime):
        return None, None

    return None, None


def _get_sequence_value(event: Event) -> int:
    """Get sequence value from event, or use a default"""
    if event.time and event.time.sequence is not None:
        return event.time.sequence
    return 0


# ========== 1. Sorting and Ordering ==========


def sort_events_by_time(events: list[Event]) -> list[Event]:
    """Sort events by time (timestamp/calendar/sequence)"""

    def get_sort_key(event: Event) -> tuple[int, int]:
        """Return (timestamp_ms, sequence) for sorting"""
        time_val = _get_time_value(event.time) if event.time else None
        seq_val = _get_sequence_value(event)
        # Use large number for None timestamps to put them at the end
        timestamp_ms = time_val if time_val is not None else 9999999999999
        return timestamp_ms, seq_val

    return sorted(events, key=get_sort_key)


def sort_events_by_sequence(events: list[Event]) -> list[Event]:
    """Sort events by sequence number"""
    return sorted(events, key=_get_sequence_value)


def get_chronological_order(timeline: Timeline) -> list[Event]:
    """Get events in chronological order for a timeline"""
    events = timeline.get_all_events()
    return sort_events_by_time(events)


# ========== 2. Temporal Queries ==========


def get_events_in_range(
    events: list[Event], start_time: int | None, end_time: int | None
) -> list[Event]:
    """Get events within a time range (timestamps in milliseconds)"""
    result = []
    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is None:
            continue

        if start_time is not None and time_val < start_time:
            continue
        if end_time is not None and time_val > end_time:
            continue

        result.append(event)
    return result


def get_events_after(events: list[Event], time_point: int) -> list[Event]:
    """Get events after a specific time point (timestamp in milliseconds)"""
    result = []
    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None and time_val > time_point:
            result.append(event)
    return result


def get_events_before(events: list[Event], time_point: int) -> list[Event]:
    """Get events before a specific time point (timestamp in milliseconds)"""
    result = []
    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None and time_val < time_point:
            result.append(event)
    return result


def get_events_at_time(events: list[Event], time_point: int, tolerance_ms: int = 0) -> list[Event]:
    """Get events at a specific time point (with tolerance in milliseconds)"""
    result = []
    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None:
            diff = abs(time_val - time_point)
            if diff <= tolerance_ms:
                result.append(event)
    return result


# ========== 3. Time Intervals ==========


def get_time_interval(event1: Event, event2: Event) -> int | None:
    """Get time interval between two events (in milliseconds)"""
    time1 = _get_time_value(event1.time) if event1.time else None
    time2 = _get_time_value(event2.time) if event2.time else None

    if time1 is None or time2 is None:
        return None

    return abs(time2 - time1)


def get_all_intervals(events: list[Event]) -> list[dict]:
    """Get all intervals between consecutive events"""
    sorted_events = sort_events_by_time(events)
    intervals = []

    for i in range(len(sorted_events) - 1):
        interval_ms = get_time_interval(sorted_events[i], sorted_events[i + 1])
        if interval_ms is not None:
            intervals.append(
                {
                    "event1_id": sorted_events[i].event_id,
                    "event2_id": sorted_events[i + 1].event_id,
                    "interval_ms": interval_ms,
                }
            )

    return intervals


def get_average_interval(events: list[Event]) -> float | None:
    """Get average interval between events"""
    intervals = get_all_intervals(events)
    if not intervals:
        return None

    interval_values = [interval["interval_ms"] for interval in intervals]
    return statistics.mean(interval_values)


def find_longest_gap(events: list[Event]) -> dict | None:
    """Find the longest gap between events"""
    intervals = get_all_intervals(events)
    if not intervals:
        return None

    longest = max(intervals, key=lambda x: x["interval_ms"])
    return longest


# ========== 4. Time Ranges ==========


def get_timeline_bounds(timeline: Timeline) -> dict | None:
    """Get start and end time bounds of a timeline"""
    events = timeline.get_all_events()
    if not events:
        return None

    timestamps = []
    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None:
            timestamps.append(time_val)

    if not timestamps:
        return None

    return {
        "start_ms": min(timestamps),
        "end_ms": max(timestamps),
        "duration_ms": max(timestamps) - min(timestamps),
    }


def get_project_bounds(project: Project) -> dict | None:
    """Get time bounds of entire project"""
    all_events = project.get_all_events()
    if not all_events:
        return None

    timestamps = []
    for event in all_events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None:
            timestamps.append(time_val)

    if not timestamps:
        return None

    return {
        "start_ms": min(timestamps),
        "end_ms": max(timestamps),
        "duration_ms": max(timestamps) - min(timestamps),
    }


def get_events_overlap(event1: Event, event2: Event) -> bool:
    """Check if two events' time ranges overlap"""
    range1 = _get_time_range(event1.time) if event1.time else (None, None)
    range2 = _get_time_range(event2.time) if event2.time else (None, None)

    start1, end1 = range1
    start2, end2 = range2

    # If either event has no time, no overlap
    if start1 is None or start2 is None:
        return False

    # If both are exact times, check if they're the same
    if end1 == start1 and end2 == start2:
        return start1 == start2

    # Normalize ranges (use start as end if end is None)
    if end1 is None:
        end1 = start1
    if end2 is None:
        end2 = start2

    # Check overlap: ranges overlap if start1 <= end2 and start2 <= end1
    return start1 <= end2 and start2 <= end1


def find_overlapping_events(events: list[Event]) -> list[tuple[Event, Event]]:
    """Find pairs of overlapping events"""
    overlapping = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            if get_events_overlap(events[i], events[j]):
                overlapping.append((events[i], events[j]))
    return overlapping


# ========== 5. Grouping and Clustering ==========


def group_events_by_period(events: list[Event], period: str) -> dict:
    """Group events by time period (day/week/month/year)"""
    grouped: dict[str, list[Event]] = {}

    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is None:
            continue

        dt = datetime.fromtimestamp(time_val / 1000, tz=UTC)

        if period == "year":
            key = str(dt.year)
        elif period == "month":
            key = f"{dt.year}-{dt.month:02d}"
        elif period == "week":
            # ISO week
            year, week, _ = dt.isocalendar()
            key = f"{year}-W{week:02d}"
        elif period == "day":
            key = f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
        else:
            continue

        if key not in grouped:
            grouped[key] = []
        grouped[key].append(event)

    return grouped


def find_time_clusters(events: list[Event], threshold_ms: int) -> list[list[Event]]:
    """Find clusters of events close in time"""
    sorted_events = sort_events_by_time(events)
    if not sorted_events:
        return []

    clusters: list[list[Event]] = []
    current_cluster: list[Event] = [sorted_events[0]]

    for i in range(1, len(sorted_events)):
        prev_time = (
            _get_time_value(sorted_events[i - 1].time) if sorted_events[i - 1].time else None
        )
        curr_time = _get_time_value(sorted_events[i].time) if sorted_events[i].time else None

        if prev_time is not None and curr_time is not None:
            gap = curr_time - prev_time
            if gap <= threshold_ms:
                current_cluster.append(sorted_events[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [sorted_events[i]]
        else:
            # Events without time go to separate clusters
            if current_cluster:
                clusters.append(current_cluster)
            current_cluster = [sorted_events[i]]

    if current_cluster:
        clusters.append(current_cluster)

    return clusters


def get_events_density(events: list[Event], window_ms: int) -> list[dict]:
    """Get events density in sliding time window"""
    sorted_events = sort_events_by_time(events)
    if not sorted_events:
        return []

    # Get time bounds
    timestamps = []
    for event in sorted_events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None:
            timestamps.append(time_val)

    if not timestamps:
        return []

    # Handle zero window size to avoid infinite loop
    if window_ms <= 0:
        return []

    min_time = min(timestamps)
    max_time = max(timestamps)

    density_data = []
    # Slide window across time range
    current_time = min_time
    step = window_ms // 2  # Overlap windows by 50%

    while current_time <= max_time:
        window_start = current_time
        window_end = current_time + window_ms

        count = 0
        for event in sorted_events:
            time_val = _get_time_value(event.time) if event.time else None
            if time_val is not None and window_start <= time_val <= window_end:
                count += 1

        density_data.append(
            {
                "window_start_ms": window_start,
                "window_end_ms": window_end,
                "event_count": count,
                "density": count / (window_ms / 1000),  # events per second
            }
        )

        current_time += step

    return density_data


# ========== 6. Temporal Patterns ==========


def find_regular_intervals(events: list[Event], tolerance_ms: int) -> list[dict]:
    """Find regular intervals between events"""
    intervals = get_all_intervals(events)
    if len(intervals) < 2:
        return []

    # Group intervals by similar values
    interval_groups: dict[int, list[dict]] = {}

    for interval in intervals:
        interval_val = interval["interval_ms"]
        # Find closest group
        found_group = False
        for group_key in interval_groups:
            if abs(interval_val - group_key) <= tolerance_ms:
                interval_groups[group_key].append(interval)
                found_group = True
                break

        if not found_group:
            interval_groups[interval_val] = [interval]

    # Filter groups with at least 2 occurrences
    regular_patterns = []
    for group_key, group_intervals in interval_groups.items():
        if len(group_intervals) >= 2:
            regular_patterns.append(
                {
                    "interval_ms": group_key,
                    "occurrences": len(group_intervals),
                    "intervals": group_intervals,
                }
            )

    return sorted(regular_patterns, key=lambda x: x["occurrences"], reverse=True)


def detect_temporal_patterns(events: list[Event]) -> list[dict]:
    """Detect temporal patterns in events"""
    patterns = []

    # Check for regular intervals
    regular_intervals = find_regular_intervals(events, tolerance_ms=1000)
    if regular_intervals:
        patterns.append({"type": "regular_intervals", "data": regular_intervals})

    # Check for clustering
    clusters = find_time_clusters(events, threshold_ms=60000)  # 1 minute default
    if len(clusters) > 1:
        large_clusters = [c for c in clusters if len(c) >= 3]
        if large_clusters:
            patterns.append(
                {
                    "type": "time_clusters",
                    "data": {
                        "cluster_count": len(large_clusters),
                        "clusters": [[e.event_id for e in cluster] for cluster in large_clusters],
                    },
                }
            )

    return patterns


def get_event_frequency(events: list[Event], period: str) -> dict:
    """Get event frequency by time period"""
    grouped = group_events_by_period(events, period)
    frequency = {}

    for period_key, period_events in grouped.items():
        frequency[period_key] = len(period_events)

    return frequency


# ========== 7. Validation and Checks ==========


def validate_temporal_consistency(timeline: Timeline) -> list[str]:
    """Validate temporal consistency of timeline (returns list of issues)"""
    issues = []
    events = timeline.get_all_events()

    if not events:
        return issues

    # Check for events without time
    events_without_time = [e for e in events if e.time is None or _get_time_value(e.time) is None]
    if events_without_time:
        issues.append(f"Found {len(events_without_time)} events without time information")

    # Check for overlapping events (might be intentional, but flag it)
    overlapping = find_overlapping_events(events)
    if overlapping:
        issues.append(f"Found {len(overlapping)} pairs of overlapping events")

    # Check sequence consistency
    if not check_sequence_consistency(events):
        issues.append("Sequence numbers are not consistent with temporal order")

    # Check for very large gaps (potential data issues)
    intervals = get_all_intervals(events)
    if intervals:
        avg_interval = get_average_interval(events)
        if avg_interval:
            for interval in intervals:
                if interval["interval_ms"] > avg_interval * 10:
                    issues.append(f"Large gap detected: {interval['interval_ms']}ms between events")

    return issues


def check_sequence_consistency(events: list[Event]) -> bool:
    """Check if sequence numbers are consistent"""
    sorted_by_time = sort_events_by_time(events)
    sorted_by_seq = sort_events_by_sequence(events)

    # Check if temporal order matches sequence order
    if len(sorted_by_time) != len(sorted_by_seq):
        return False

    # Compare event IDs in both orders
    time_order_ids = [e.event_id for e in sorted_by_time]
    seq_order_ids = [e.event_id for e in sorted_by_seq]

    return time_order_ids == seq_order_ids


def detect_temporal_anomalies(events: list[Event]) -> list[Event]:
    """Detect temporal anomalies in events"""
    anomalies = []

    if len(events) < 2:
        return anomalies

    sorted_events = sort_events_by_time(events)
    intervals = get_all_intervals(sorted_events)

    if not intervals:
        return anomalies

    # Calculate statistics
    interval_values = [interval["interval_ms"] for interval in intervals]
    if len(interval_values) < 2:
        return anomalies

    mean_interval = statistics.mean(interval_values)
    stdev_interval = statistics.stdev(interval_values) if len(interval_values) > 1 else 0

    # Find outliers (intervals more than 3 standard deviations from mean)
    threshold = mean_interval + 3 * stdev_interval

    for i, interval in enumerate(intervals):
        if interval["interval_ms"] > threshold:
            # Mark the second event in the interval as potentially anomalous
            event_id = interval["event2_id"]
            anomalous_event = next((e for e in events if e.event_id == event_id), None)
            if anomalous_event and anomalous_event not in anomalies:
                anomalies.append(anomalous_event)

    return anomalies


# ========== 8. Statistics ==========


def get_time_statistics(events: list[Event]) -> dict:
    """Get time statistics (min, max, mean, median)"""
    timestamps = []
    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None:
            timestamps.append(time_val)

    if not timestamps:
        return {"count": 0, "min_ms": None, "max_ms": None, "mean_ms": None, "median_ms": None}

    return {
        "count": len(timestamps),
        "min_ms": min(timestamps),
        "max_ms": max(timestamps),
        "mean_ms": statistics.mean(timestamps),
        "median_ms": statistics.median(timestamps),
    }


def get_source_temporal_coverage(project: Project) -> dict:
    """Get temporal coverage by source"""
    coverage = {}
    sources = project.get_all_sources()

    for source in sources:
        events = project.get_events_by_source(source.source_id)
        if not events:
            coverage[source.source_id] = {
                "event_count": 0,
                "start_ms": None,
                "end_ms": None,
                "duration_ms": None,
            }
            continue

        timestamps = []
        for event in events:
            time_val = _get_time_value(event.time) if event.time else None
            if time_val is not None:
                timestamps.append(time_val)

        if timestamps:
            coverage[source.source_id] = {
                "event_count": len(events),
                "start_ms": min(timestamps),
                "end_ms": max(timestamps),
                "duration_ms": max(timestamps) - min(timestamps),
            }
        else:
            coverage[source.source_id] = {
                "event_count": len(events),
                "start_ms": None,
                "end_ms": None,
                "duration_ms": None,
            }

    return coverage


def get_timeline_temporal_coverage(project: Project) -> dict:
    """Get temporal coverage by timeline"""
    coverage = {}
    timelines = project.get_all_timelines()

    for timeline in timelines:
        bounds = get_timeline_bounds(timeline)
        if bounds:
            coverage[timeline.timeline_id] = {
                "event_count": timeline.get_event_count(),
                "start_ms": bounds["start_ms"],
                "end_ms": bounds["end_ms"],
                "duration_ms": bounds["duration_ms"],
            }
        else:
            coverage[timeline.timeline_id] = {
                "event_count": timeline.get_event_count(),
                "start_ms": None,
                "end_ms": None,
                "duration_ms": None,
            }

    return coverage


# ========== 9. Uncertainty Handling ==========


def expand_uncertainty(event: Event) -> dict:
    """Expand event with uncertainty bounds"""
    if event.time is None:
        return {
            "event_id": event.event_id,
            "base_time_ms": None,
            "uncertainty": None,
            "min_time_ms": None,
            "max_time_ms": None,
        }

    base_time = _get_time_value(event.time)
    uncertainty = event.time.uncertainty if hasattr(event.time, "uncertainty") else None

    result = {
        "event_id": event.event_id,
        "base_time_ms": base_time,
        "uncertainty": uncertainty is not None,
    }

    if base_time is not None and uncertainty is not None:
        uncertainty_time = _get_time_value(uncertainty)
        if uncertainty_time is not None:
            # Use uncertainty as a range
            if isinstance(event.time, RangeTime):
                start, end = _get_time_range(event.time)
                result["min_time_ms"] = start
                result["max_time_ms"] = end
            else:
                # Assume uncertainty represents a range around base time
                result["min_time_ms"] = base_time - abs(uncertainty_time - base_time)
                result["max_time_ms"] = base_time + abs(uncertainty_time - base_time)
        else:
            result["min_time_ms"] = base_time
            result["max_time_ms"] = base_time
    else:
        result["min_time_ms"] = base_time
        result["max_time_ms"] = base_time

    return result


def get_events_with_uncertainty(events: list[Event]) -> list[Event]:
    """Get events that have uncertainty"""
    result = []
    for event in events:
        if event.time and hasattr(event.time, "uncertainty") and event.time.uncertainty is not None:
            result.append(event)
    return result


def calculate_confidence_window(event: Event) -> dict | None:
    """Calculate confidence window for event"""
    if event.time is None:
        return None

    base_time = _get_time_value(event.time)
    if base_time is None:
        return None

    uncertainty = event.time.uncertainty if hasattr(event.time, "uncertainty") else None

    if uncertainty is None:
        return {
            "center_ms": base_time,
            "window_start_ms": base_time,
            "window_end_ms": base_time,
            "window_size_ms": 0,
        }

    uncertainty_time = _get_time_value(uncertainty)
    if uncertainty_time is None:
        return {
            "center_ms": base_time,
            "window_start_ms": base_time,
            "window_end_ms": base_time,
            "window_size_ms": 0,
        }

    # Calculate window based on uncertainty
    diff = abs(uncertainty_time - base_time)
    return {
        "center_ms": base_time,
        "window_start_ms": base_time - diff,
        "window_end_ms": base_time + diff,
        "window_size_ms": diff * 2,
    }


# ========== 10. Relative Time ==========


def resolve_relative_times(timeline: Timeline) -> dict:
    """Resolve relative times to absolute times"""
    events = timeline.get_all_events()
    resolved = {}
    unresolved = []

    # Create event map for validation
    event_map = {e.event_id: e for e in events}

    # Build dependency graph for relative times
    relative_events = []
    for event in events:
        if isinstance(event.time, RelativeTime):
            # Validate that referenced event exists
            ref_event_id = event.time.relative_to
            if ref_event_id not in event_map:
                unresolved.append(event.event_id)
            else:
                relative_events.append(event)
        else:
            time_val = _get_time_value(event.time) if event.time else None
            if time_val is not None:
                resolved[event.event_id] = time_val

    # Resolve relative times iteratively
    max_iterations = len(relative_events) * 2  # Prevent infinite loops
    iteration = 0

    while relative_events and iteration < max_iterations:
        iteration += 1
        remaining = []

        for event in relative_events:
            if isinstance(event.time, RelativeTime):
                ref_event_id = event.time.relative_to
                if ref_event_id in resolved:
                    ref_time = resolved[ref_event_id]
                    resolved_time = ref_time + event.time.offset_ms
                    resolved[event.event_id] = resolved_time
                else:
                    remaining.append(event)

        if len(remaining) == len(relative_events):
            # No progress, break to avoid infinite loop
            break
        relative_events = remaining

    # Collect unresolved events
    for event in relative_events:
        unresolved.append(event.event_id)

    return {"resolved": resolved, "unresolved": unresolved}


def get_relative_time_chain(event: Event, timeline: Timeline) -> list[Event]:
    """Get chain of relative time dependencies"""
    if not isinstance(event.time, RelativeTime):
        return [event]

    chain = [event]
    event_map = {e.event_id: e for e in timeline.get_all_events()}
    visited = {event.event_id}
    current = event

    while isinstance(current.time, RelativeTime):
        ref_id = current.time.relative_to
        if ref_id in visited:
            # Circular dependency detected
            break
        if ref_id not in event_map:
            # Reference event not found
            break

        visited.add(ref_id)
        ref_event = event_map[ref_id]
        chain.append(ref_event)
        current = ref_event

    return chain


# ========== 11. Timeline Comparison ==========


def compare_timelines(timeline1: Timeline, timeline2: Timeline) -> dict:
    """Compare two timelines"""
    events1 = timeline1.get_all_events()
    events2 = timeline2.get_all_events()

    bounds1 = get_timeline_bounds(timeline1)
    bounds2 = get_timeline_bounds(timeline2)

    common = find_common_events(timeline1, timeline2)

    # Check temporal overlap
    temporal_overlap = False
    if bounds1 and bounds2:
        overlap_start = max(bounds1["start_ms"], bounds2["start_ms"])
        overlap_end = min(bounds1["end_ms"], bounds2["end_ms"])
        temporal_overlap = overlap_start <= overlap_end

    return {
        "timeline1_id": timeline1.timeline_id,
        "timeline2_id": timeline2.timeline_id,
        "timeline1_event_count": len(events1),
        "timeline2_event_count": len(events2),
        "common_event_count": len(common),
        "timeline1_bounds": bounds1,
        "timeline2_bounds": bounds2,
        "temporal_overlap": temporal_overlap,
        "common_events": [e.event_id for e in common],
    }


def find_common_events(timeline1: Timeline, timeline2: Timeline) -> list[Event]:
    """Find common events between timelines"""
    events1 = {e.event_id: e for e in timeline1.get_all_events()}
    events2 = {e.event_id: e for e in timeline2.get_all_events()}

    common_ids = set(events1.keys()) & set(events2.keys())
    return [events1[eid] for eid in common_ids]


def get_timeline_alignment(timelines: list[Timeline]) -> dict:
    """Get alignment of multiple timelines"""
    if not timelines:
        return {"timeline_count": 0, "bounds": None, "overlap_periods": []}

    all_bounds = []
    for timeline in timelines:
        bounds = get_timeline_bounds(timeline)
        if bounds:
            all_bounds.append(
                {
                    "timeline_id": timeline.timeline_id,
                    "start_ms": bounds["start_ms"],
                    "end_ms": bounds["end_ms"],
                }
            )

    if not all_bounds:
        return {"timeline_count": len(timelines), "bounds": None, "overlap_periods": []}

    # Find overall bounds
    overall_start = min(b["start_ms"] for b in all_bounds)
    overall_end = max(b["end_ms"] for b in all_bounds)

    # Find overlap periods (simplified - finds period where all timelines overlap)
    overlap_start = max(b["start_ms"] for b in all_bounds)
    overlap_end = min(b["end_ms"] for b in all_bounds)

    overlap_periods = []
    if overlap_start <= overlap_end:
        overlap_periods.append(
            {
                "start_ms": overlap_start,
                "end_ms": overlap_end,
                "duration_ms": overlap_end - overlap_start,
            }
        )

    return {
        "timeline_count": len(timelines),
        "bounds": {
            "start_ms": overall_start,
            "end_ms": overall_end,
            "duration_ms": overall_end - overall_start,
        },
        "overlap_periods": overlap_periods,
        "timeline_bounds": all_bounds,
    }


# ========== 12. Temporal Metrics ==========


def calculate_temporal_coverage(events: list[Event]) -> float:
    """Calculate temporal coverage percentage"""
    if not events:
        return 0.0

    timestamps = []
    for event in events:
        time_val = _get_time_value(event.time) if event.time else None
        if time_val is not None:
            timestamps.append(time_val)

    if not timestamps or len(timestamps) < 2:
        return 0.0

    # Calculate total time span
    total_span = max(timestamps) - min(timestamps)
    if total_span == 0:
        return 100.0

    # Sort timestamps for accurate coverage calculation
    sorted_timestamps = sorted(timestamps)

    # For each event, assume it covers a small window (e.g., 1 second)
    # This is a simplified metric
    event_window_ms = 1000  # 1 second per event

    # Calculate unique time coverage
    unique_times = set()
    for ts in sorted_timestamps:
        # Round to nearest second for coverage calculation
        time_bucket = (ts // 1000) * 1000
        unique_times.add(time_bucket)

    covered_time = len(unique_times) * event_window_ms
    coverage_percentage = min(100.0, (covered_time / total_span) * 100) if total_span > 0 else 0.0

    return coverage_percentage


def get_temporal_gaps(events: list[Event], threshold_ms: int) -> list[dict]:
    """Get temporal gaps in events"""
    sorted_events = sort_events_by_time(events)
    gaps = []

    for i in range(len(sorted_events) - 1):
        interval_ms = get_time_interval(sorted_events[i], sorted_events[i + 1])
        if interval_ms is not None and interval_ms > threshold_ms:
            time1 = _get_time_value(sorted_events[i].time) if sorted_events[i].time else None
            time2 = (
                _get_time_value(sorted_events[i + 1].time) if sorted_events[i + 1].time else None
            )

            if time1 is not None and time2 is not None:
                gaps.append(
                    {
                        "gap_start_ms": time1,
                        "gap_end_ms": time2,
                        "gap_size_ms": interval_ms,
                        "event1_id": sorted_events[i].event_id,
                        "event2_id": sorted_events[i + 1].event_id,
                    }
                )

    return gaps


def calculate_temporal_diversity(events: list[Event]) -> float:
    """Calculate temporal diversity metric (0-1, higher = more diverse)"""
    if len(events) < 2:
        return 0.0

    intervals = get_all_intervals(events)
    if not intervals:
        return 0.0

    interval_values = [interval["interval_ms"] for interval in intervals]

    if len(interval_values) < 2:
        return 0.0

    # Calculate coefficient of variation (std/mean) as diversity metric
    mean_interval = statistics.mean(interval_values)
    if mean_interval == 0:
        return 0.0

    stdev_interval = statistics.stdev(interval_values) if len(interval_values) > 1 else 0
    coefficient_of_variation = stdev_interval / mean_interval if mean_interval > 0 else 0

    # Normalize to 0-1 range (using tanh for smooth normalization)
    diversity = math.tanh(coefficient_of_variation)

    return diversity
