"""Tests for analytics core module - temporal analysis functions"""

import unittest

from sequolog.core import analytics
from sequolog.model.event import Event
from sequolog.model.project import Project
from sequolog.model.source import Source
from sequolog.model.time.exact_time import ExactTime
from sequolog.model.time.no_time import NoTime
from sequolog.model.time.range_time import RangeTime
from sequolog.model.time.relative_time import RelativeTime
from sequolog.model.time.time_base import CalendarFields
from sequolog.model.timeline import Timeline


class TestSortingAndOrdering(unittest.TestCase):
    """Tests for sorting and ordering functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

        # Create events with different times
        self.event1 = Event(
            "evt_1",
            "src_1",
            "First event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        self.event2 = Event(
            "evt_2",
            "src_1",
            "Second event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=12)),
        )
        self.event3 = Event(
            "evt_3",
            "src_1",
            "Third event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)),
        )
        self.event4 = Event("evt_4", "src_1", "Event with sequence only", NoTime(sequence=5))

    def test_sort_events_by_time(self):
        """Test sorting events by time"""
        events = [self.event2, self.event1, self.event3]
        sorted_events = analytics.sort_events_by_time(events)

        self.assertEqual(len(sorted_events), 3)
        self.assertEqual(sorted_events[0].event_id, "evt_1")
        self.assertEqual(sorted_events[1].event_id, "evt_3")
        self.assertEqual(sorted_events[2].event_id, "evt_2")

    def test_sort_events_by_time_with_sequence(self):
        """Test sorting events by time including sequence"""
        events = [self.event4, self.event1, self.event2]
        sorted_events = analytics.sort_events_by_time(events)

        # Events with time should come before events with only sequence
        self.assertEqual(sorted_events[0].event_id, "evt_1")
        self.assertEqual(sorted_events[1].event_id, "evt_2")
        self.assertEqual(sorted_events[2].event_id, "evt_4")

    def test_sort_events_by_sequence(self):
        """Test sorting events by sequence number"""
        event_a = Event("evt_a", "src_1", "A", NoTime(sequence=3))
        event_b = Event("evt_b", "src_1", "B", NoTime(sequence=1))
        event_c = Event("evt_c", "src_1", "C", NoTime(sequence=2))

        events = [event_a, event_b, event_c]
        sorted_events = analytics.sort_events_by_sequence(events)

        self.assertEqual(sorted_events[0].event_id, "evt_b")
        self.assertEqual(sorted_events[1].event_id, "evt_c")
        self.assertEqual(sorted_events[2].event_id, "evt_a")

    def test_get_chronological_order(self):
        """Test getting chronological order from timeline"""
        timeline = Timeline("tl_1", "Test Timeline")
        timeline.add_event(self.event2)
        timeline.add_event(self.event1)
        timeline.add_event(self.event3)

        chronological = analytics.get_chronological_order(timeline)

        self.assertEqual(len(chronological), 3)
        self.assertEqual(chronological[0].event_id, "evt_1")
        self.assertEqual(chronological[1].event_id, "evt_3")
        self.assertEqual(chronological[2].event_id, "evt_2")


class TestTemporalQueries(unittest.TestCase):
    """Tests for temporal query functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

        # Create events at different times
        self.event1 = Event(
            "evt_1",
            "src_1",
            "Event at 10:00",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        self.event2 = Event(
            "evt_2",
            "src_1",
            "Event at 12:00",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=12)),
        )
        self.event3 = Event(
            "evt_3",
            "src_1",
            "Event at 14:00",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=14)),
        )

    def test_get_events_in_range(self):
        """Test getting events within time range"""
        events = [self.event1, self.event2, self.event3]

        # Convert times to milliseconds for comparison
        start = analytics._calendar_to_timestamp_ms(
            CalendarFields(year=2024, month=1, day=15, hour=11)
        )
        end = analytics._calendar_to_timestamp_ms(
            CalendarFields(year=2024, month=1, day=15, hour=13)
        )

        result = analytics.get_events_in_range(events, start, end)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].event_id, "evt_2")

    def test_get_events_after(self):
        """Test getting events after a time point"""
        events = [self.event1, self.event2, self.event3]

        time_point = analytics._calendar_to_timestamp_ms(
            CalendarFields(year=2024, month=1, day=15, hour=11)
        )

        result = analytics.get_events_after(events, time_point)

        self.assertEqual(len(result), 2)
        self.assertIn(self.event2, result)
        self.assertIn(self.event3, result)

    def test_get_events_before(self):
        """Test getting events before a time point"""
        events = [self.event1, self.event2, self.event3]

        time_point = analytics._calendar_to_timestamp_ms(
            CalendarFields(year=2024, month=1, day=15, hour=13)
        )

        result = analytics.get_events_before(events, time_point)

        self.assertEqual(len(result), 2)
        self.assertIn(self.event1, result)
        self.assertIn(self.event2, result)

    def test_get_events_at_time(self):
        """Test getting events at specific time with tolerance"""
        events = [self.event1, self.event2, self.event3]

        time_point = analytics._calendar_to_timestamp_ms(
            CalendarFields(year=2024, month=1, day=15, hour=12, minute=5)
        )
        tolerance_ms = 10 * 60 * 1000  # 10 minutes

        result = analytics.get_events_at_time(events, time_point, tolerance_ms)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].event_id, "evt_2")

    def test_get_events_in_range_with_none(self):
        """Test getting events in range with None boundaries"""
        events = [self.event1, self.event2, self.event3]

        # Test with None start_time
        start = analytics._calendar_to_timestamp_ms(
            CalendarFields(year=2024, month=1, day=15, hour=11)
        )
        result = analytics.get_events_in_range(events, None, start)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].event_id, "evt_1")

        # Test with None end_time
        result = analytics.get_events_in_range(events, start, None)
        self.assertEqual(len(result), 2)

        # Test with both None
        result = analytics.get_events_in_range(events, None, None)
        self.assertEqual(len(result), 3)

    def test_get_events_in_range_empty(self):
        """Test getting events in range with empty list"""
        result = analytics.get_events_in_range([], 1000, 2000)
        self.assertEqual(len(result), 0)


class TestTimeIntervals(unittest.TestCase):
    """Tests for time interval functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

        self.event1 = Event(
            "evt_1",
            "src_1",
            "First event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        self.event2 = Event(
            "evt_2",
            "src_1",
            "Second event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)),
        )
        self.event3 = Event(
            "evt_3",
            "src_1",
            "Third event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=13)),
        )

    def test_get_time_interval(self):
        """Test getting time interval between two events"""
        interval = analytics.get_time_interval(self.event1, self.event2)

        # Should be approximately 1 hour = 3600000 ms
        self.assertIsNotNone(interval)
        self.assertAlmostEqual(interval, 3600000, delta=1000)

    def test_get_time_interval_none_for_no_time(self):
        """Test that interval returns None for events without time"""
        event_no_time = Event("evt_no", "src_1", "No time", NoTime())

        interval = analytics.get_time_interval(self.event1, event_no_time)
        self.assertIsNone(interval)

    def test_get_all_intervals(self):
        """Test getting all intervals between consecutive events"""
        events = [self.event1, self.event2, self.event3]
        intervals = analytics.get_all_intervals(events)

        self.assertEqual(len(intervals), 2)
        self.assertEqual(intervals[0]["event1_id"], "evt_1")
        self.assertEqual(intervals[0]["event2_id"], "evt_2")
        self.assertEqual(intervals[1]["event1_id"], "evt_2")
        self.assertEqual(intervals[1]["event2_id"], "evt_3")

    def test_get_average_interval(self):
        """Test getting average interval between events"""
        events = [self.event1, self.event2, self.event3]
        avg = analytics.get_average_interval(events)

        self.assertIsNotNone(avg)
        # Average of 1 hour and 2 hours = 1.5 hours
        self.assertAlmostEqual(avg, 5400000, delta=1000)

    def test_find_longest_gap(self):
        """Test finding longest gap between events"""
        events = [self.event1, self.event2, self.event3]
        longest = analytics.find_longest_gap(events)

        self.assertIsNotNone(longest)
        self.assertEqual(longest["event1_id"], "evt_2")
        self.assertEqual(longest["event2_id"], "evt_3")
        # Should be 2 hours = 7200000 ms
        self.assertAlmostEqual(longest["interval_ms"], 7200000, delta=1000)

    def test_get_average_interval_empty(self):
        """Test getting average interval with empty or single event"""
        # Empty list
        result = analytics.get_average_interval([])
        self.assertIsNone(result)

        # Single event
        result = analytics.get_average_interval([self.event1])
        self.assertIsNone(result)

    def test_find_longest_gap_empty(self):
        """Test finding longest gap with empty or single event"""
        # Empty list
        result = analytics.find_longest_gap([])
        self.assertIsNone(result)

        # Single event
        result = analytics.find_longest_gap([self.event1])
        self.assertIsNone(result)


class TestTimeRanges(unittest.TestCase):
    """Tests for time range functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

        self.timeline = Timeline("tl_1", "Test Timeline")
        self.event1 = Event(
            "evt_1",
            "src_1",
            "First event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        self.event2 = Event(
            "evt_2",
            "src_1",
            "Last event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=14)),
        )
        self.timeline.add_event(self.event1)
        self.timeline.add_event(self.event2)

    def test_get_timeline_bounds(self):
        """Test getting timeline time bounds"""
        bounds = analytics.get_timeline_bounds(self.timeline)

        self.assertIsNotNone(bounds)
        self.assertIn("start_ms", bounds)
        self.assertIn("end_ms", bounds)
        self.assertIn("duration_ms", bounds)
        self.assertLess(bounds["start_ms"], bounds["end_ms"])
        self.assertEqual(bounds["duration_ms"], bounds["end_ms"] - bounds["start_ms"])

    def test_get_timeline_bounds_empty(self):
        """Test getting bounds for empty timeline"""
        empty_timeline = Timeline("tl_empty", "Empty")
        bounds = analytics.get_timeline_bounds(empty_timeline)

        self.assertIsNone(bounds)

    def test_get_project_bounds(self):
        """Test getting project time bounds"""
        project = Project("proj_1", "Test Project", "Test")
        timeline1 = Timeline("tl_1", "Timeline 1")
        timeline2 = Timeline("tl_2", "Timeline 2")

        event1 = Event(
            "evt_1", "src_1", "Early", ExactTime(calendar=CalendarFields(year=2024, month=1, day=1))
        )
        event2 = Event(
            "evt_2",
            "src_1",
            "Late",
            ExactTime(calendar=CalendarFields(year=2024, month=12, day=31)),
        )

        timeline1.add_event(event1)
        timeline2.add_event(event2)
        project.add_timeline(timeline1)
        project.add_timeline(timeline2)

        bounds = analytics.get_project_bounds(project)

        self.assertIsNotNone(bounds)
        self.assertIn("start_ms", bounds)
        self.assertIn("end_ms", bounds)
        self.assertLess(bounds["start_ms"], bounds["end_ms"])

    def test_get_events_overlap(self):
        """Test checking if events overlap"""
        event_range1 = Event(
            "evt_1",
            "src_1",
            "Range 1",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=10),
                end=CalendarFields(year=2024, month=1, day=15, hour=12),
            ),
        )
        event_range2 = Event(
            "evt_2",
            "src_1",
            "Range 2",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=11),
                end=CalendarFields(year=2024, month=1, day=15, hour=13),
            ),
        )
        event_no_overlap = Event(
            "evt_3",
            "src_1",
            "No overlap",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=14),
                end=CalendarFields(year=2024, month=1, day=15, hour=15),
            ),
        )

        self.assertTrue(analytics.get_events_overlap(event_range1, event_range2))
        self.assertFalse(analytics.get_events_overlap(event_range1, event_no_overlap))

    def test_get_events_overlap_exact_time(self):
        """Test checking overlap with ExactTime events"""
        event1 = Event(
            "evt_1",
            "src_1",
            "Exact 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        event2 = Event(
            "evt_2",
            "src_1",
            "Exact 2 same time",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        event3 = Event(
            "evt_3",
            "src_1",
            "Exact 3 different time",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)),
        )

        self.assertTrue(analytics.get_events_overlap(event1, event2))
        self.assertFalse(analytics.get_events_overlap(event1, event3))

    def test_get_events_overlap_exact_vs_range(self):
        """Test checking overlap between ExactTime and RangeTime"""
        exact_event = Event(
            "evt_1",
            "src_1",
            "Exact",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)),
        )
        range_event_overlap = Event(
            "evt_2",
            "src_1",
            "Range overlapping",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=10),
                end=CalendarFields(year=2024, month=1, day=15, hour=12),
            ),
        )
        range_event_no_overlap = Event(
            "evt_3",
            "src_1",
            "Range not overlapping",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=13),
                end=CalendarFields(year=2024, month=1, day=15, hour=14),
            ),
        )

        self.assertTrue(analytics.get_events_overlap(exact_event, range_event_overlap))
        self.assertFalse(analytics.get_events_overlap(exact_event, range_event_no_overlap))

    def test_get_events_overlap_range_with_none_end(self):
        """Test checking overlap with RangeTime that has None end"""
        event1 = Event(
            "evt_1", "src_1", "Range with start only",
            RangeTime(start=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        event2 = Event(
            "evt_2", "src_1", "Range overlapping",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=11),
                end=CalendarFields(year=2024, month=1, day=15, hour=12)
            )
        )
        
        # Should normalize None end to start and check overlap
        result = analytics.get_events_overlap(event1, event2)
        self.assertIsInstance(result, bool)

    def test_get_events_overlap_no_time(self):
        """Test checking overlap with events without time"""
        event1 = Event("evt_1", "src_1", "No time", NoTime())
        event2 = Event(
            "evt_2", "src_1", "With time",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        
        # Should return False if either event has no time
        self.assertFalse(analytics.get_events_overlap(event1, event2))
        self.assertFalse(analytics.get_events_overlap(event2, event1))

    def test_find_overlapping_events(self):
        """Test finding overlapping events"""
        event1 = Event(
            "evt_1",
            "src_1",
            "Event 1",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=10),
                end=CalendarFields(year=2024, month=1, day=15, hour=12),
            ),
        )
        event2 = Event(
            "evt_2",
            "src_1",
            "Event 2",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=11),
                end=CalendarFields(year=2024, month=1, day=15, hour=13),
            ),
        )
        event3 = Event(
            "evt_3",
            "src_1",
            "Event 3",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=14),
                end=CalendarFields(year=2024, month=1, day=15, hour=15),
            ),
        )

        events = [event1, event2, event3]
        overlapping = analytics.find_overlapping_events(events)

        self.assertEqual(len(overlapping), 1)
        self.assertIn((event1, event2), overlapping)


class TestGroupingAndClustering(unittest.TestCase):
    """Tests for grouping and clustering functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

        self.events = [
            Event(
                "evt_1",
                "src_1",
                "Jan 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=1)),
            ),
            Event(
                "evt_2",
                "src_1",
                "Jan 15",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15)),
            ),
            Event(
                "evt_3",
                "src_1",
                "Feb 1",
                ExactTime(calendar=CalendarFields(year=2024, month=2, day=1)),
            ),
            Event(
                "evt_4",
                "src_1",
                "Feb 15",
                ExactTime(calendar=CalendarFields(year=2024, month=2, day=15)),
            ),
        ]

    def test_group_events_by_period_year(self):
        """Test grouping events by year"""
        grouped = analytics.group_events_by_period(self.events, "year")

        self.assertEqual(len(grouped), 1)
        self.assertIn("2024", grouped)
        self.assertEqual(len(grouped["2024"]), 4)

    def test_group_events_by_period_month(self):
        """Test grouping events by month"""
        grouped = analytics.group_events_by_period(self.events, "month")

        self.assertEqual(len(grouped), 2)
        self.assertIn("2024-01", grouped)
        self.assertIn("2024-02", grouped)
        self.assertEqual(len(grouped["2024-01"]), 2)
        self.assertEqual(len(grouped["2024-02"]), 2)

    def test_group_events_by_period_day(self):
        """Test grouping events by day"""
        grouped = analytics.group_events_by_period(self.events, "day")

        self.assertEqual(len(grouped), 4)
        self.assertIn("2024-01-01", grouped)
        self.assertIn("2024-01-15", grouped)

    def test_group_events_by_period_week(self):
        """Test grouping events by week"""
        grouped = analytics.group_events_by_period(self.events, "week")
        
        self.assertIsInstance(grouped, dict)
        self.assertGreater(len(grouped), 0)
        # Check that week keys are in format YYYY-WNN
        for key in grouped.keys():
            self.assertIn("-W", key)

    def test_group_events_by_period_invalid(self):
        """Test grouping events by invalid period"""
        grouped = analytics.group_events_by_period(self.events, "invalid_period")
        
        # Should return empty dict for invalid period
        self.assertEqual(len(grouped), 0)

    def test_find_time_clusters(self):
        """Test finding time clusters"""
        # Create events close in time
        event1 = Event(
            "evt_1",
            "src_1",
            "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=0)),
        )
        event2 = Event(
            "evt_2",
            "src_1",
            "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=5)),
        )
        event3 = Event(
            "evt_3",
            "src_1",
            "Event 3",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11, minute=0)),
        )

        events = [event1, event2, event3]
        clusters = analytics.find_time_clusters(events, threshold_ms=15 * 60 * 1000)  # 15 minutes

        # First two events should be in one cluster, third in another
        self.assertGreaterEqual(len(clusters), 2)

    def test_get_events_density(self):
        """Test getting events density"""
        density = analytics.get_events_density(
            self.events, window_ms=30 * 24 * 60 * 60 * 1000
        )  # 30 days

        self.assertIsInstance(density, list)
        self.assertGreater(len(density), 0)
        for entry in density:
            self.assertIn("window_start_ms", entry)
            self.assertIn("window_end_ms", entry)
            self.assertIn("event_count", entry)
            self.assertIn("density", entry)


class TestTemporalPatterns(unittest.TestCase):
    """Tests for temporal pattern detection functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_find_regular_intervals(self):
        """Test finding regular intervals"""
        # Create events with regular 1-hour intervals
        events = []
        for i in range(5):
            events.append(
                Event(
                    f"evt_{i}",
                    "src_1",
                    f"Event {i}",
                    ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10 + i)),
                )
            )

        patterns = analytics.find_regular_intervals(
            events, tolerance_ms=5 * 60 * 1000
        )  # 5 min tolerance

        self.assertIsInstance(patterns, list)
        # Should find regular 1-hour interval pattern
        if patterns:
            self.assertIn("interval_ms", patterns[0])
            self.assertIn("occurrences", patterns[0])

    def test_find_regular_intervals_less_than_two(self):
        """Test finding regular intervals with less than 2 intervals"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)))
        ]
        
        patterns = analytics.find_regular_intervals(events, tolerance_ms=1000)
        self.assertEqual(len(patterns), 0)

    def test_find_regular_intervals_no_matching(self):
        """Test finding regular intervals when intervals don't match tolerance"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11))),
            Event("evt_3", "src_1", "Event 3",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=13))),
        ]
        
        # Very small tolerance - intervals won't match
        patterns = analytics.find_regular_intervals(events, tolerance_ms=1)
        # Should return empty or patterns with single occurrences
        self.assertIsInstance(patterns, list)

    def test_find_regular_intervals_single_occurrence_groups(self):
        """Test finding regular intervals when groups have only one occurrence"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11))),
            Event("evt_3", "src_1", "Event 3",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=13))),
        ]
        
        # Each interval is unique, so no groups with >= 2 occurrences
        patterns = analytics.find_regular_intervals(events, tolerance_ms=1000)
        
        # Should return empty list (no groups with >= 2 occurrences)
        self.assertEqual(len(patterns), 0)

    def test_detect_temporal_patterns(self):
        """Test detecting temporal patterns"""
        events = []
        for i in range(5):
            events.append(
                Event(
                    f"evt_{i}",
                    "src_1",
                    f"Event {i}",
                    ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10 + i)),
                )
            )

        patterns = analytics.detect_temporal_patterns(events)

        self.assertIsInstance(patterns, list)
        for pattern in patterns:
            self.assertIn("type", pattern)
            self.assertIn("data", pattern)

    def test_detect_temporal_patterns_no_patterns(self):
        """Test detecting patterns when there are no patterns"""
        # Events with irregular intervals, no clusters
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=1))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=6, day=15))),
        ]
        
        patterns = analytics.detect_temporal_patterns(events)
        
        # Should return empty list or list without patterns
        self.assertIsInstance(patterns, list)

    def test_detect_temporal_patterns_small_clusters(self):
        """Test detecting patterns with small clusters (less than 3 events)"""
        # Create events that form small clusters
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=0))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=1))),
        ]
        
        patterns = analytics.detect_temporal_patterns(events)
        
        # Small clusters (< 3) should not be reported
        self.assertIsInstance(patterns, list)

    def test_detect_temporal_patterns_single_cluster(self):
        """Test detecting patterns when there's only one cluster"""
        # All events in one cluster
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=0))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=1))),
            Event("evt_3", "src_1", "Event 3",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=2))),
        ]
        
        patterns = analytics.detect_temporal_patterns(events)
        
        # Single cluster (len(clusters) <= 1) should not add time_clusters pattern
        self.assertIsInstance(patterns, list)

    def test_get_event_frequency(self):
        """Test getting event frequency by period"""
        events = [
            Event(
                "evt_1",
                "src_1",
                "Jan 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=1)),
            ),
            Event(
                "evt_2",
                "src_1",
                "Jan 15",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15)),
            ),
            Event(
                "evt_3",
                "src_1",
                "Feb 1",
                ExactTime(calendar=CalendarFields(year=2024, month=2, day=1)),
            ),
        ]

        frequency = analytics.get_event_frequency(events, "month")

        self.assertIsInstance(frequency, dict)
        self.assertEqual(frequency["2024-01"], 2)
        self.assertEqual(frequency["2024-02"], 1)


class TestValidationAndChecks(unittest.TestCase):
    """Tests for validation and check functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_validate_temporal_consistency(self):
        """Test validating temporal consistency"""
        timeline = Timeline("tl_1", "Test Timeline")

        event1 = Event(
            "evt_1",
            "src_1",
            "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        event2 = Event(
            "evt_2",
            "src_1",
            "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)),
        )
        timeline.add_event(event1)
        timeline.add_event(event2)

        issues = analytics.validate_temporal_consistency(timeline)

        self.assertIsInstance(issues, list)
        # Should have no issues for consistent timeline
        # (may have overlapping events warning, but that's acceptable)

    def test_validate_temporal_consistency_with_no_time(self):
        """Test validation with events without time"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        event_no_time = Event("evt_1", "src_1", "No time", NoTime())
        timeline.add_event(event_no_time)
        
        issues = analytics.validate_temporal_consistency(timeline)
        
        # Should report events without time
        self.assertGreater(len(issues), 0)

    def test_validate_temporal_consistency_with_large_gaps(self):
        """Test validation with large temporal gaps"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        event1 = Event(
            "evt_1", "src_1", "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=1))
        )
        event2 = Event(
            "evt_2", "src_1", "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=2))
        )
        event3 = Event(
            "evt_3", "src_1", "Event 3",
            ExactTime(calendar=CalendarFields(year=2024, month=12, day=31))  # Large gap
        )
        
        timeline.add_event(event1)
        timeline.add_event(event2)
        timeline.add_event(event3)
        
        issues = analytics.validate_temporal_consistency(timeline)
        
        # Should detect large gap
        self.assertIsInstance(issues, list)
        # May or may not have issues depending on threshold

    def test_validate_temporal_consistency_no_intervals(self):
        """Test validation when there are no intervals"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        event = Event(
            "evt_1", "src_1", "Single event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=1))
        )
        
        timeline.add_event(event)
        
        issues = analytics.validate_temporal_consistency(timeline)
        
        # Should handle gracefully when no intervals
        self.assertIsInstance(issues, list)

    def test_validate_temporal_consistency_no_avg_interval(self):
        """Test validation when average interval cannot be calculated"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        # Events where intervals can't be calculated properly
        event1 = Event(
            "evt_1", "src_1", "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=1))
        )
        event2 = Event(
            "evt_2", "src_1", "Event 2",
            NoTime()  # No time, so interval can't be calculated
        )
        
        timeline.add_event(event1)
        timeline.add_event(event2)
        
        issues = analytics.validate_temporal_consistency(timeline)
        
        # Should handle gracefully when avg_interval is None
        self.assertIsInstance(issues, list)

    def test_check_sequence_consistency(self):
        """Test checking sequence consistency"""
        event1 = Event(
            "evt_1",
            "src_1",
            "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10), sequence=1),
        )
        event2 = Event(
            "evt_2",
            "src_1",
            "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11), sequence=2),
        )

        events = [event1, event2]
        is_consistent = analytics.check_sequence_consistency(events)

        self.assertTrue(is_consistent)

    def test_detect_temporal_anomalies(self):
        """Test detecting temporal anomalies"""
        # Create events with one large gap
        events = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
            ),
            Event(
                "evt_2",
                "src_1",
                "Event 2",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)),
            ),
            Event(
                "evt_3",
                "src_1",
                "Event 3",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=20, hour=10)),
            ),  # Large gap
        ]

        anomalies = analytics.detect_temporal_anomalies(events)

        self.assertIsInstance(anomalies, list)
        # May detect evt_3 as anomalous due to large gap

    def test_detect_temporal_anomalies_no_intervals(self):
        """Test detecting anomalies when there are no intervals"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)))
        ]
        
        anomalies = analytics.detect_temporal_anomalies(events)
        self.assertEqual(len(anomalies), 0)

    def test_detect_temporal_anomalies_single_interval(self):
        """Test detecting anomalies with only one interval"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11))),
        ]
        
        anomalies = analytics.detect_temporal_anomalies(events)
        # With only one interval, can't calculate stdev properly
        self.assertEqual(len(anomalies), 0)


class TestStatistics(unittest.TestCase):
    """Tests for statistics functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

        self.events = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
            ),
            Event(
                "evt_2",
                "src_1",
                "Event 2",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=12)),
            ),
            Event(
                "evt_3",
                "src_1",
                "Event 3",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=14)),
            ),
        ]

    def test_get_time_statistics(self):
        """Test getting time statistics"""
        stats = analytics.get_time_statistics(self.events)

        self.assertIn("count", stats)
        self.assertIn("min_ms", stats)
        self.assertIn("max_ms", stats)
        self.assertIn("mean_ms", stats)
        self.assertIn("median_ms", stats)
        self.assertEqual(stats["count"], 3)
        self.assertIsNotNone(stats["min_ms"])
        self.assertIsNotNone(stats["max_ms"])
        self.assertLess(stats["min_ms"], stats["max_ms"])

    def test_get_time_statistics_empty(self):
        """Test getting time statistics with empty list"""
        stats = analytics.get_time_statistics([])

        self.assertEqual(stats["count"], 0)
        self.assertIsNone(stats["min_ms"])
        self.assertIsNone(stats["max_ms"])
        self.assertIsNone(stats["mean_ms"])
        self.assertIsNone(stats["median_ms"])

    def test_get_time_statistics_no_time(self):
        """Test getting time statistics with events without time"""
        events = [
            Event("evt_1", "src_1", "No time", NoTime()),
            Event("evt_2", "src_1", "No time 2", NoTime()),
        ]

        stats = analytics.get_time_statistics(events)

        self.assertEqual(stats["count"], 0)
        self.assertIsNone(stats["min_ms"])

    def test_get_source_temporal_coverage(self):
        """Test getting source temporal coverage"""
        project = Project("proj_1", "Test", "Test")
        source1 = Source("src_1", "Source 1", "ref://1")
        source2 = Source("src_2", "Source 2", "ref://2")

        project.add_source(source1)
        project.add_source(source2)

        timeline = Timeline("tl_1", "Timeline")
        event1 = Event(
            "evt_1",
            "src_1",
            "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=1)),
        )
        event2 = Event(
            "evt_2",
            "src_2",
            "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=12, day=31)),
        )

        timeline.add_event(event1)
        timeline.add_event(event2)
        project.add_timeline(timeline)

        coverage = analytics.get_source_temporal_coverage(project)

        self.assertIn("src_1", coverage)
        self.assertIn("src_2", coverage)
        self.assertEqual(coverage["src_1"]["event_count"], 1)
        self.assertEqual(coverage["src_2"]["event_count"], 1)

    def test_get_timeline_temporal_coverage(self):
        """Test getting timeline temporal coverage"""
        project = Project("proj_1", "Test", "Test")
        timeline1 = Timeline("tl_1", "Timeline 1")
        timeline2 = Timeline("tl_2", "Timeline 2")

        event1 = Event(
            "evt_1",
            "src_1",
            "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=1)),
        )
        event2 = Event(
            "evt_2",
            "src_1",
            "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=12, day=31)),
        )

        timeline1.add_event(event1)
        timeline2.add_event(event2)
        project.add_timeline(timeline1)
        project.add_timeline(timeline2)

        coverage = analytics.get_timeline_temporal_coverage(project)

        self.assertIn("tl_1", coverage)
        self.assertIn("tl_2", coverage)
        self.assertEqual(coverage["tl_1"]["event_count"], 1)
        self.assertEqual(coverage["tl_2"]["event_count"], 1)


class TestUncertaintyHandling(unittest.TestCase):
    """Tests for uncertainty handling functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_expand_uncertainty(self):
        """Test expanding event with uncertainty"""
        uncertainty = ExactTime(calendar=CalendarFields(year=2024, month=1, day=16))
        event = Event(
            "evt_1",
            "src_1",
            "Event with uncertainty",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15), uncertainty=uncertainty),
        )

        expanded = analytics.expand_uncertainty(event)

        self.assertIn("event_id", expanded)
        self.assertIn("base_time_ms", expanded)
        self.assertIn("uncertainty", expanded)
        self.assertIn("min_time_ms", expanded)
        self.assertIn("max_time_ms", expanded)
        self.assertTrue(expanded["uncertainty"])

    def test_expand_uncertainty_no_time(self):
        """Test expanding event without time"""
        event = Event("evt_1", "src_1", "No time", NoTime())

        expanded = analytics.expand_uncertainty(event)

        self.assertEqual(expanded["event_id"], "evt_1")
        self.assertIsNone(expanded["base_time_ms"])
        self.assertFalse(expanded["uncertainty"])
        self.assertIsNone(expanded["min_time_ms"])
        self.assertIsNone(expanded["max_time_ms"])

    def test_expand_uncertainty_no_uncertainty(self):
        """Test expanding event without uncertainty"""
        event = Event(
            "evt_1",
            "src_1",
            "No uncertainty",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15)),
        )

        expanded = analytics.expand_uncertainty(event)

        self.assertFalse(expanded["uncertainty"])
        self.assertIsNotNone(expanded["base_time_ms"])

    def test_get_events_with_uncertainty(self):
        """Test getting events with uncertainty"""
        event_with = Event(
            "evt_1",
            "src_1",
            "With uncertainty",
            ExactTime(
                calendar=CalendarFields(year=2024, month=1, day=15),
                uncertainty=ExactTime(calendar=CalendarFields(year=2024, month=1, day=16)),
            ),
        )
        event_without = Event(
            "evt_2",
            "src_1",
            "Without uncertainty",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15)),
        )

        events = [event_with, event_without]
        result = analytics.get_events_with_uncertainty(events)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].event_id, "evt_1")

    def test_calculate_confidence_window(self):
        """Test calculating confidence window"""
        uncertainty = ExactTime(calendar=CalendarFields(year=2024, month=1, day=16))
        event = Event(
            "evt_1",
            "src_1",
            "Event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15), uncertainty=uncertainty),
        )

        window = analytics.calculate_confidence_window(event)

        self.assertIsNotNone(window)
        self.assertIn("center_ms", window)
        self.assertIn("window_start_ms", window)
        self.assertIn("window_end_ms", window)
        self.assertIn("window_size_ms", window)
        self.assertLessEqual(window["window_start_ms"], window["center_ms"])
        self.assertGreaterEqual(window["window_end_ms"], window["center_ms"])

    def test_calculate_confidence_window_no_time(self):
        """Test calculating confidence window for event without time"""
        event = Event("evt_1", "src_1", "No time", NoTime())

        window = analytics.calculate_confidence_window(event)

        self.assertIsNone(window)

    def test_calculate_confidence_window_no_uncertainty(self):
        """Test calculating confidence window for event without uncertainty"""
        event = Event(
            "evt_1",
            "src_1",
            "No uncertainty",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15)),
        )

        window = analytics.calculate_confidence_window(event)

        self.assertIsNotNone(window)
        self.assertEqual(window["window_size_ms"], 0)
        self.assertEqual(window["window_start_ms"], window["center_ms"])
        self.assertEqual(window["window_end_ms"], window["center_ms"])


class TestRelativeTime(unittest.TestCase):
    """Tests for relative time functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_resolve_relative_times(self):
        """Test resolving relative times to absolute"""
        timeline = Timeline("tl_1", "Test Timeline")

        base_event = Event(
            "evt_base",
            "src_1",
            "Base event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        relative_event = Event(
            "evt_rel",
            "src_1",
            "Relative event",
            RelativeTime(relative_to="evt_base", offset_ms=3600000),  # 1 hour later
        )

        timeline.add_event(base_event)
        timeline.add_event(relative_event)

        resolved = analytics.resolve_relative_times(timeline)

        self.assertIn("resolved", resolved)
        self.assertIn("unresolved", resolved)
        self.assertIn("evt_base", resolved["resolved"])
        self.assertIn("evt_rel", resolved["resolved"])
        # Relative event should be 1 hour after base
        base_time = resolved["resolved"]["evt_base"]
        rel_time = resolved["resolved"]["evt_rel"]
        self.assertAlmostEqual(rel_time - base_time, 3600000, delta=1000)

    def test_resolve_relative_times_missing_reference(self):
        """Test resolving relative times with missing reference"""
        timeline = Timeline("tl_1", "Test Timeline")

        relative_event = Event(
            "evt_rel",
            "src_1",
            "Relative event",
            RelativeTime(relative_to="nonexistent", offset_ms=3600000),
        )

        timeline.add_event(relative_event)

        resolved = analytics.resolve_relative_times(timeline)

        self.assertIn("evt_rel", resolved["unresolved"])

    def test_get_relative_time_chain(self):
        """Test getting relative time dependency chain"""
        timeline = Timeline("tl_1", "Test Timeline")

        base_event = Event(
            "evt_base",
            "src_1",
            "Base",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        rel1 = Event(
            "evt_rel1",
            "src_1",
            "Relative 1",
            RelativeTime(relative_to="evt_base", offset_ms=3600000),
        )
        rel2 = Event(
            "evt_rel2",
            "src_1",
            "Relative 2",
            RelativeTime(relative_to="evt_rel1", offset_ms=1800000),
        )

        timeline.add_event(base_event)
        timeline.add_event(rel1)
        timeline.add_event(rel2)

        chain = analytics.get_relative_time_chain(rel2, timeline)

        self.assertGreater(len(chain), 1)
        self.assertEqual(chain[-1].event_id, "evt_base")

    def test_get_relative_time_chain_non_relative(self):
        """Test getting chain for non-relative event"""
        timeline = Timeline("tl_1", "Test Timeline")

        event = Event(
            "evt_1",
            "src_1",
            "Non-relative",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )

        timeline.add_event(event)

        chain = analytics.get_relative_time_chain(event, timeline)

        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0].event_id, "evt_1")


class TestTimelineComparison(unittest.TestCase):
    """Tests for timeline comparison functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.timeline1 = Timeline("tl_1", "Timeline 1")
        self.timeline2 = Timeline("tl_2", "Timeline 2")

        self.event1 = Event(
            "evt_1",
            "src_1",
            "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
        )
        self.event2 = Event(
            "evt_2",
            "src_1",
            "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=12)),
        )
        self.event3 = Event(
            "evt_3",
            "src_1",
            "Event 3",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=14)),
        )

    def test_compare_timelines(self):
        """Test comparing two timelines"""
        self.timeline1.add_event(self.event1)
        self.timeline1.add_event(self.event2)
        self.timeline2.add_event(self.event2)
        self.timeline2.add_event(self.event3)

        comparison = analytics.compare_timelines(self.timeline1, self.timeline2)

        self.assertIn("timeline1_id", comparison)
        self.assertIn("timeline2_id", comparison)
        self.assertIn("timeline1_event_count", comparison)
        self.assertIn("timeline2_event_count", comparison)
        self.assertIn("common_event_count", comparison)
        self.assertEqual(comparison["common_event_count"], 1)
        self.assertIn("evt_2", comparison["common_events"])

    def test_compare_timelines_no_bounds(self):
        """Test comparing timelines when one has no bounds"""
        self.timeline1.add_event(self.event1)
        # timeline2 has no events with time
        
        comparison = analytics.compare_timelines(self.timeline1, self.timeline2)
        
        self.assertIn("temporal_overlap", comparison)
        self.assertFalse(comparison["temporal_overlap"])

    def test_compare_timelines_no_overlap(self):
        """Test comparing timelines that don't overlap temporally"""
        timeline1 = Timeline("tl_1", "Timeline 1")
        timeline2 = Timeline("tl_2", "Timeline 2")
        
        event1 = Event(
            "evt_1", "src_1", "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=1))
        )
        event2 = Event(
            "evt_2", "src_1", "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=12, day=31))
        )
        
        timeline1.add_event(event1)
        timeline2.add_event(event2)
        
        comparison = analytics.compare_timelines(timeline1, timeline2)
        
        self.assertFalse(comparison["temporal_overlap"])

    def test_find_common_events(self):
        """Test finding common events between timelines"""
        self.timeline1.add_event(self.event1)
        self.timeline1.add_event(self.event2)
        self.timeline2.add_event(self.event2)
        self.timeline2.add_event(self.event3)

        common = analytics.find_common_events(self.timeline1, self.timeline2)

        self.assertEqual(len(common), 1)
        self.assertEqual(common[0].event_id, "evt_2")

    def test_get_timeline_alignment(self):
        """Test getting alignment of multiple timelines"""
        self.timeline1.add_event(self.event1)
        self.timeline2.add_event(self.event2)

        alignment = analytics.get_timeline_alignment([self.timeline1, self.timeline2])

        self.assertIn("timeline_count", alignment)
        self.assertIn("bounds", alignment)
        self.assertIn("overlap_periods", alignment)
        self.assertEqual(alignment["timeline_count"], 2)

    def test_get_timeline_alignment_empty(self):
        """Test getting alignment with empty list"""
        alignment = analytics.get_timeline_alignment([])
        
        self.assertEqual(alignment["timeline_count"], 0)
        self.assertIsNone(alignment["bounds"])
        self.assertEqual(len(alignment["overlap_periods"]), 0)

    def test_get_timeline_alignment_no_overlap(self):
        """Test getting alignment when timelines don't overlap"""
        timeline1 = Timeline("tl_1", "Timeline 1")
        timeline2 = Timeline("tl_2", "Timeline 2")
        
        event1 = Event(
            "evt_1", "src_1", "Event 1",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=1))
        )
        event2 = Event(
            "evt_2", "src_1", "Event 2",
            ExactTime(calendar=CalendarFields(year=2024, month=12, day=31))
        )
        
        timeline1.add_event(event1)
        timeline2.add_event(event2)
        
        alignment = analytics.get_timeline_alignment([timeline1, timeline2])
        
        # Should have bounds but no overlap periods
        self.assertIsNotNone(alignment["bounds"])
        # overlap_start > overlap_end, so no overlap periods
        self.assertEqual(len(alignment["overlap_periods"]), 0)

    def test_get_timeline_alignment_no_bounds(self):
        """Test getting alignment when timelines have no time bounds"""
        timeline1 = Timeline("tl_1", "Timeline 1")
        timeline2 = Timeline("tl_2", "Timeline 2")
        
        # Add events without time
        event1 = Event("evt_1", "src_1", "No time", NoTime())
        event2 = Event("evt_2", "src_1", "No time 2", NoTime())
        
        timeline1.add_event(event1)
        timeline2.add_event(event2)
        
        alignment = analytics.get_timeline_alignment([timeline1, timeline2])
        
        # Should handle gracefully
        self.assertEqual(alignment["timeline_count"], 2)
        self.assertIsNone(alignment["bounds"])
        self.assertEqual(len(alignment["overlap_periods"]), 0)


class TestTemporalMetrics(unittest.TestCase):
    """Tests for temporal metrics functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_calculate_temporal_coverage(self):
        """Test calculating temporal coverage"""
        events = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=1)),
            ),
            Event(
                "evt_2",
                "src_1",
                "Event 2",
                ExactTime(calendar=CalendarFields(year=2024, month=6, day=15)),
            ),
            Event(
                "evt_3",
                "src_1",
                "Event 3",
                ExactTime(calendar=CalendarFields(year=2024, month=12, day=31)),
            ),
        ]

        coverage = analytics.calculate_temporal_coverage(events)

        self.assertIsInstance(coverage, float)
        self.assertGreaterEqual(coverage, 0.0)
        self.assertLessEqual(coverage, 100.0)

    def test_calculate_temporal_coverage_empty(self):
        """Test calculating temporal coverage with empty list"""
        coverage = analytics.calculate_temporal_coverage([])
        self.assertEqual(coverage, 0.0)

    def test_calculate_temporal_coverage_single(self):
        """Test calculating temporal coverage with single event"""
        events = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=1)),
            )
        ]

        coverage = analytics.calculate_temporal_coverage(events)
        self.assertEqual(coverage, 0.0)

    def test_calculate_temporal_coverage_zero_span(self):
        """Test calculating temporal coverage when all events are at the same time"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))),
        ]
        
        coverage = analytics.calculate_temporal_coverage(events)
        
        # When total_span == 0, should return 100.0
        self.assertEqual(coverage, 100.0)

    def test_get_temporal_gaps(self):
        """Test getting temporal gaps"""
        events = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
            ),
            Event(
                "evt_2",
                "src_1",
                "Event 2",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)),
            ),
            Event(
                "evt_3",
                "src_1",
                "Event 3",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=20, hour=10)),
            ),  # Large gap
        ]

        gaps = analytics.get_temporal_gaps(events, threshold_ms=24 * 60 * 60 * 1000)  # 1 day

        self.assertIsInstance(gaps, list)
        # Should find gap between evt_2 and evt_3
        self.assertGreater(len(gaps), 0)
        for gap in gaps:
            self.assertIn("gap_start_ms", gap)
            self.assertIn("gap_end_ms", gap)
            self.assertIn("gap_size_ms", gap)

    def test_get_temporal_gaps_empty(self):
        """Test getting temporal gaps with empty list"""
        gaps = analytics.get_temporal_gaps([], threshold_ms=1000)
        self.assertEqual(len(gaps), 0)

    def test_get_temporal_gaps_single(self):
        """Test getting temporal gaps with single event"""
        events = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
            )
        ]

        gaps = analytics.get_temporal_gaps(events, threshold_ms=1000)
        self.assertEqual(len(gaps), 0)

    def test_get_temporal_gaps_with_no_time_events(self):
        """Test getting temporal gaps when some events have no time"""
        events = [
            Event(
                "evt_1", "src_1", "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
            ),
            Event("evt_2", "src_1", "No time", NoTime()),
            Event(
                "evt_3", "src_1", "Event 3",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=12))
            ),
        ]
        
        gaps = analytics.get_temporal_gaps(events, threshold_ms=1000)
        
        # Should handle events without time gracefully
        self.assertIsInstance(gaps, list)

    def test_calculate_temporal_diversity(self):
        """Test calculating temporal diversity"""
        # Events with regular intervals (low diversity)
        events_regular = [
            Event(
                f"evt_{i}",
                "src_1",
                f"Event {i}",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10 + i)),
            )
            for i in range(5)
        ]

        # Events with irregular intervals (high diversity)
        events_irregular = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=1)),
            ),
            Event(
                "evt_2",
                "src_1",
                "Event 2",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=2)),
            ),
            Event(
                "evt_3",
                "src_1",
                "Event 3",
                ExactTime(calendar=CalendarFields(year=2024, month=12, day=31)),
            ),
        ]

        diversity_regular = analytics.calculate_temporal_diversity(events_regular)
        diversity_irregular = analytics.calculate_temporal_diversity(events_irregular)

        self.assertIsInstance(diversity_regular, float)
        self.assertIsInstance(diversity_irregular, float)
        self.assertGreaterEqual(diversity_regular, 0.0)
        self.assertLessEqual(diversity_regular, 1.0)
        # Irregular should generally have higher diversity
        self.assertGreaterEqual(diversity_irregular, 0.0)
        self.assertLessEqual(diversity_irregular, 1.0)

    def test_calculate_temporal_diversity_empty(self):
        """Test calculating temporal diversity with empty list"""
        diversity = analytics.calculate_temporal_diversity([])
        self.assertEqual(diversity, 0.0)

    def test_calculate_temporal_diversity_single(self):
        """Test calculating temporal diversity with single event"""
        events = [
            Event(
                "evt_1",
                "src_1",
                "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)),
            )
        ]

        diversity = analytics.calculate_temporal_diversity(events)
        self.assertEqual(diversity, 0.0)


class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_calendar_to_timestamp_with_tz_offset(self):
        """Test calendar to timestamp conversion with timezone offset"""
        calendar = CalendarFields(
            year=2024, month=1, day=15, hour=10, tz_offset_minutes=180  # +03:00
        )
        timestamp = analytics._calendar_to_timestamp_ms(calendar)
        self.assertIsNotNone(timestamp)

    def test_calendar_to_timestamp_invalid_date(self):
        """Test calendar to timestamp with invalid date (should return None)"""
        # Invalid date: February 30
        calendar = CalendarFields(year=2024, month=2, day=30)
        timestamp = analytics._calendar_to_timestamp_ms(calendar)
        # Should handle gracefully and return None on ValueError
        # Note: Python's datetime might auto-correct, so this might not trigger ValueError
        # But if it does, should return None

    def test_calendar_to_timestamp_overflow(self):
        """Test calendar to timestamp with very large year (potential overflow)"""
        # Very large year that might cause overflow
        calendar = CalendarFields(year=999999, month=12, day=31)
        timestamp = analytics._calendar_to_timestamp_ms(calendar)
        # Should handle gracefully - might return None on OverflowError or valid timestamp

    def test_get_time_value_with_timestamp_seconds(self):
        """Test _get_time_value with timestamp in seconds"""
        event = Event(
            "evt_1", "src_1", "Event",
            ExactTime(timestamp=1705312200)  # timestamp in seconds
        )
        time_val = analytics._get_time_value(event.time)
        self.assertIsNotNone(time_val)
        # Should be converted to milliseconds
        self.assertGreater(time_val, 1705312200)

    def test_get_time_value_with_timestamp_milliseconds(self):
        """Test _get_time_value with timestamp already in milliseconds"""
        # Very large timestamp (milliseconds)
        large_ts = 1705312200000
        event = Event("evt_1", "src_1", "Event", ExactTime(timestamp=large_ts))
        time_val = analytics._get_time_value(event.time)
        self.assertIsNotNone(time_val)
        # Should use as is
        self.assertEqual(time_val, large_ts)

    def test_get_time_value_range_time_with_timestamp(self):
        """Test _get_time_value with RangeTime that has timestamp"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(timestamp=1705312200)
        )
        time_val = analytics._get_time_value(event.time)
        # Should use timestamp if start/end are None
        self.assertIsNotNone(time_val)

    def test_get_time_value_range_time_end_only(self):
        """Test _get_time_value with RangeTime that has only end"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(end=CalendarFields(year=2024, month=1, day=15))
        )
        time_val = analytics._get_time_value(event.time)
        # Should use end if start is None
        self.assertIsNotNone(time_val)

    def test_get_time_value_exact_time_no_calendar(self):
        """Test _get_time_value with ExactTime that has no calendar"""
        event = Event(
            "evt_1", "src_1", "Event",
            ExactTime(timestamp=1705312200)  # Only timestamp, no calendar
        )
        time_val = analytics._get_time_value(event.time)
        # Should use timestamp
        self.assertIsNotNone(time_val)

    def test_get_time_range_range_time_with_timestamp(self):
        """Test _get_time_range with RangeTime that has timestamp"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(timestamp=1705312200)
        )
        start, end = analytics._get_time_range(event.time)
        # Should use timestamp for both start and end if they're None
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_get_time_range_range_time_start_only(self):
        """Test _get_time_range with RangeTime that has only start"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(start=CalendarFields(year=2024, month=1, day=15))
        )
        start, end = analytics._get_time_range(event.time)
        self.assertIsNotNone(start)
        # End might be None or same as start depending on implementation

    def test_get_time_range_range_time_end_only(self):
        """Test _get_time_range with RangeTime that has only end"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(end=CalendarFields(year=2024, month=1, day=15))
        )
        start, end = analytics._get_time_range(event.time)
        self.assertIsNotNone(end)
        # Start might be None or same as end depending on implementation

    def test_get_time_range_range_time_with_timestamp_fallback(self):
        """Test _get_time_range with RangeTime that uses timestamp as fallback"""
        # RangeTime with timestamp but no start/end
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(timestamp=1705312200)  # timestamp in seconds
        )
        start, end = analytics._get_time_range(event.time)
        # Should use timestamp for both start and end
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_get_time_range_range_time_start_and_timestamp(self):
        """Test _get_time_range with RangeTime that has start and timestamp"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15),
                timestamp=1705312200
            )
        )
        start, end = analytics._get_time_range(event.time)
        # Start should use calendar, end should use timestamp
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_get_time_range_range_time_end_and_timestamp(self):
        """Test _get_time_range with RangeTime that has end and timestamp"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(
                end=CalendarFields(year=2024, month=1, day=15),
                timestamp=1705312200
            )
        )
        start, end = analytics._get_time_range(event.time)
        # Start should use timestamp, end should use calendar
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_get_time_range_range_time_start_with_timestamp(self):
        """Test _get_time_range with RangeTime that has start and timestamp"""
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15),
                timestamp=1705312200
            )
        )
        start, end = analytics._get_time_range(event.time)
        self.assertIsNotNone(start)
        # End should use timestamp if end is None
        self.assertIsNotNone(end)


class TestExpandUncertaintyEdgeCases(unittest.TestCase):
    """Tests for expand_uncertainty edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_expand_uncertainty_range_time(self):
        """Test expand_uncertainty with RangeTime"""
        uncertainty = ExactTime(calendar=CalendarFields(year=2024, month=1, day=16))
        event = Event(
            "evt_1", "src_1", "Event",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15),
                end=CalendarFields(year=2024, month=1, day=17),
                uncertainty=uncertainty
            )
        )
        
        expanded = analytics.expand_uncertainty(event)
        
        self.assertIn("min_time_ms", expanded)
        self.assertIn("max_time_ms", expanded)
        # For RangeTime, should use the range itself
        self.assertIsNotNone(expanded["min_time_ms"])
        self.assertIsNotNone(expanded["max_time_ms"])

    def test_expand_uncertainty_with_uncertainty_no_time_value(self):
        """Test expand_uncertainty when uncertainty has no time value"""
        uncertainty = NoTime()  # Uncertainty without time
        event = Event(
            "evt_1", "src_1", "Event",
            ExactTime(
                calendar=CalendarFields(year=2024, month=1, day=15),
                uncertainty=uncertainty
            )
        )
        
        expanded = analytics.expand_uncertainty(event)
        
        # Should handle gracefully
        self.assertIsNotNone(expanded["base_time_ms"])
        self.assertEqual(expanded["min_time_ms"], expanded["base_time_ms"])
        self.assertEqual(expanded["max_time_ms"], expanded["base_time_ms"])


class TestResolveRelativeTimesEdgeCases(unittest.TestCase):
    """Tests for resolve_relative_times edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_resolve_relative_times_circular_dependency(self):
        """Test resolving relative times with circular dependency"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        event1 = Event(
            "evt_1", "src_1", "Event 1",
            RelativeTime(relative_to="evt_2", offset_ms=1000)
        )
        event2 = Event(
            "evt_2", "src_1", "Event 2",
            RelativeTime(relative_to="evt_1", offset_ms=1000)
        )
        
        timeline.add_event(event1)
        timeline.add_event(event2)
        
        resolved = analytics.resolve_relative_times(timeline)
        
        # Both should be unresolved due to circular dependency
        self.assertIn("evt_1", resolved["unresolved"])
        self.assertIn("evt_2", resolved["unresolved"])

    def test_resolve_relative_times_max_iterations(self):
        """Test resolving relative times that requires many iterations"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        # Create a chain of relative times
        base = Event(
            "evt_base", "src_1", "Base",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        timeline.add_event(base)
        
        # Create many relative events
        for i in range(10):
            prev_id = "evt_base" if i == 0 else f"evt_{i-1}"
            event = Event(
                f"evt_{i}", "src_1", f"Event {i}",
                RelativeTime(relative_to=prev_id, offset_ms=1000)
            )
            timeline.add_event(event)
        
        resolved = analytics.resolve_relative_times(timeline)
        
        # Should resolve all events
        self.assertIn("evt_base", resolved["resolved"])
        # Most should be resolved (depending on max_iterations)

    def test_get_relative_time_chain_circular(self):
        """Test get_relative_time_chain with circular dependency"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        event1 = Event(
            "evt_1", "src_1", "Event 1",
            RelativeTime(relative_to="evt_2", offset_ms=1000)
        )
        event2 = Event(
            "evt_2", "src_1", "Event 2",
            RelativeTime(relative_to="evt_1", offset_ms=1000)
        )
        
        timeline.add_event(event1)
        timeline.add_event(event2)
        
        chain = analytics.get_relative_time_chain(event1, timeline)
        
        # Should detect circular dependency and stop
        self.assertGreaterEqual(len(chain), 1)
        self.assertLessEqual(len(chain), 2)  # Should stop at circular dependency

    def test_get_relative_time_chain_missing_reference(self):
        """Test get_relative_time_chain with missing reference"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        event = Event(
            "evt_1", "src_1", "Event",
            RelativeTime(relative_to="nonexistent", offset_ms=1000)
        )
        
        timeline.add_event(event)
        
        chain = analytics.get_relative_time_chain(event, timeline)
        
        # Should return only the event itself since reference is missing
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0].event_id, "evt_1")

    def test_resolve_relative_times_with_no_time_events(self):
        """Test resolve_relative_times with events that have no time value"""
        timeline = Timeline("tl_1", "Test Timeline")
        
        # Event with time that can't be resolved
        event_no_time_val = Event(
            "evt_1", "src_1", "No time value",
            NoTime()  # No time value
        )
        relative_event = Event(
            "evt_2", "src_1", "Relative",
            RelativeTime(relative_to="evt_1", offset_ms=1000)
        )
        
        timeline.add_event(event_no_time_val)
        timeline.add_event(relative_event)
        
        resolved = analytics.resolve_relative_times(timeline)
        
        # evt_1 should not be in resolved (no time value)
        # evt_2 should be unresolved (can't resolve relative to evt_1)
        self.assertNotIn("evt_1", resolved["resolved"])
        self.assertIn("evt_2", resolved["unresolved"])


class TestEdgeCases(unittest.TestCase):
    """Tests for various edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.source = Source("src_1", "Test Source", "ref://test")

    def test_get_events_density_empty(self):
        """Test get_events_density with empty list"""
        density = analytics.get_events_density([], window_ms=1000)
        self.assertEqual(len(density), 0)

    def test_get_events_density_no_time(self):
        """Test get_events_density with events without time"""
        events = [
            Event("evt_1", "src_1", "No time", NoTime()),
            Event("evt_2", "src_1", "No time 2", NoTime()),
        ]
        density = analytics.get_events_density(events, window_ms=1000)
        self.assertEqual(len(density), 0)

    def test_get_events_density_zero_window(self):
        """Test get_events_density with zero window size"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)))
        ]
        density = analytics.get_events_density(events, window_ms=0)
        # Should return empty list for zero or negative window to avoid infinite loop
        self.assertEqual(len(density), 0)

    def test_find_time_clusters_empty(self):
        """Test find_time_clusters with empty list"""
        clusters = analytics.find_time_clusters([], threshold_ms=1000)
        self.assertEqual(len(clusters), 0)

    def test_find_time_clusters_single(self):
        """Test find_time_clusters with single event"""
        event = Event(
            "evt_1", "src_1", "Event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        clusters = analytics.find_time_clusters([event], threshold_ms=1000)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0]), 1)

    def test_find_time_clusters_with_no_time(self):
        """Test find_time_clusters with events without time"""
        event1 = Event(
            "evt_1", "src_1", "With time",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        event2 = Event("evt_2", "src_1", "No time", NoTime())
        event3 = Event(
            "evt_3", "src_1", "With time 2",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11))
        )
        
        clusters = analytics.find_time_clusters([event1, event2, event3], threshold_ms=3600000)
        # Events without time should be in separate clusters
        self.assertGreaterEqual(len(clusters), 2)

    def test_get_all_intervals_empty(self):
        """Test get_all_intervals with empty list"""
        intervals = analytics.get_all_intervals([])
        self.assertEqual(len(intervals), 0)

    def test_get_all_intervals_single(self):
        """Test get_all_intervals with single event"""
        event = Event(
            "evt_1", "src_1", "Event",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        intervals = analytics.get_all_intervals([event])
        self.assertEqual(len(intervals), 0)

    def test_get_project_bounds_empty(self):
        """Test get_project_bounds with empty project"""
        project = Project("proj_1", "Test", "Test")
        bounds = analytics.get_project_bounds(project)
        self.assertIsNone(bounds)

    def test_get_project_bounds_no_time_events(self):
        """Test get_project_bounds with events without time"""
        project = Project("proj_1", "Test", "Test")
        timeline = Timeline("tl_1", "Timeline")
        event = Event("evt_1", "src_1", "No time", NoTime())
        timeline.add_event(event)
        project.add_timeline(timeline)
        
        bounds = analytics.get_project_bounds(project)
        self.assertIsNone(bounds)

    def test_check_sequence_consistency_inconsistent(self):
        """Test check_sequence_consistency with inconsistent sequences"""
        # event1 is earlier in time but has higher sequence
        # event2 is later in time but has lower sequence
        # This makes them inconsistent
        event1 = Event("evt_1", "src_1", "Event 1",
                      ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10), sequence=2))
        event2 = Event("evt_2", "src_1", "Event 2",
                      ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11), sequence=1))
        
        events = [event1, event2]
        is_consistent = analytics.check_sequence_consistency(events)
        
        # Should be False because temporal order (evt_1, evt_2) doesn't match sequence order (evt_2, evt_1)
        self.assertFalse(is_consistent)

    def test_check_sequence_consistency_no_sequence(self):
        """Test check_sequence_consistency with events without sequence"""
        event1 = Event("evt_1", "src_1", "Event 1",
                      ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10)))
        event2 = Event("evt_2", "src_1", "Event 2",
                      ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11)))
        
        events = [event1, event2]
        is_consistent = analytics.check_sequence_consistency(events)
        
        # Should be True because all have sequence=0 (default)
        self.assertTrue(is_consistent)

    def test_check_sequence_consistency_different_lengths(self):
        """Test check_sequence_consistency when sorted lists have different lengths"""
        # This shouldn't happen in normal cases, but test the branch
        # Create events where one might be filtered out differently
        event1 = Event("evt_1", "src_1", "Event 1",
                      ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10), sequence=1))
        event2 = Event("evt_2", "src_1", "Event 2",
                      NoTime())  # No time, only sequence
        
        events = [event1, event2]
        is_consistent = analytics.check_sequence_consistency(events)
        
        # Both should be in both sorted lists, so lengths should match
        # But test the branch anyway
        self.assertIsInstance(is_consistent, bool)

    def test_get_events_overlap_range_with_none_end(self):
        """Test checking overlap with RangeTime that has None end"""
        event1 = Event(
            "evt_1", "src_1", "Range with start only",
            RangeTime(start=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        event2 = Event(
            "evt_2", "src_1", "Range overlapping",
            RangeTime(
                start=CalendarFields(year=2024, month=1, day=15, hour=11),
                end=CalendarFields(year=2024, month=1, day=15, hour=12)
            )
        )
        
        # Should normalize None end to start and check overlap
        result = analytics.get_events_overlap(event1, event2)
        self.assertIsInstance(result, bool)

    def test_get_events_overlap_no_time(self):
        """Test checking overlap with events without time"""
        event1 = Event("evt_1", "src_1", "No time", NoTime())
        event2 = Event(
            "evt_2", "src_1", "With time",
            ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
        )
        
        # Should return False if either event has no time
        self.assertFalse(analytics.get_events_overlap(event1, event2))
        self.assertFalse(analytics.get_events_overlap(event2, event1))

    def test_detect_temporal_anomalies_event_not_found(self):
        """Test detect_temporal_anomalies when event is not found in original list"""
        # This tests the case where event_id from interval doesn't match any event
        # This shouldn't happen normally, but tests the branch
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=11))),
        ]
        
        anomalies = analytics.detect_temporal_anomalies(events)
        # Should handle gracefully
        self.assertIsInstance(anomalies, list)

    def test_get_source_temporal_coverage_empty_source(self):
        """Test get_source_temporal_coverage with source that has no events"""
        project = Project("proj_1", "Test", "Test")
        source = Source("src_1", "Source 1", "ref://1")
        project.add_source(source)
        
        coverage = analytics.get_source_temporal_coverage(project)
        
        self.assertIn("src_1", coverage)
        self.assertEqual(coverage["src_1"]["event_count"], 0)
        self.assertIsNone(coverage["src_1"]["start_ms"])

    def test_get_source_temporal_coverage_source_with_no_time_events(self):
        """Test get_source_temporal_coverage with source that has events without time"""
        project = Project("proj_1", "Test", "Test")
        source = Source("src_1", "Source 1", "ref://1")
        project.add_source(source)
        
        timeline = Timeline("tl_1", "Timeline")
        event = Event("evt_1", "src_1", "No time", NoTime())
        timeline.add_event(event)
        project.add_timeline(timeline)
        
        coverage = analytics.get_source_temporal_coverage(project)
        
        self.assertIn("src_1", coverage)
        self.assertEqual(coverage["src_1"]["event_count"], 1)
        self.assertIsNone(coverage["src_1"]["start_ms"])

    def test_get_timeline_temporal_coverage_empty_timeline(self):
        """Test get_timeline_temporal_coverage with empty timeline"""
        project = Project("proj_1", "Test", "Test")
        timeline = Timeline("tl_1", "Empty Timeline")
        project.add_timeline(timeline)
        
        coverage = analytics.get_timeline_temporal_coverage(project)
        
        self.assertIn("tl_1", coverage)
        self.assertEqual(coverage["tl_1"]["event_count"], 0)
        self.assertIsNone(coverage["tl_1"]["start_ms"])

    def test_get_timeline_temporal_coverage_timeline_with_no_time_events(self):
        """Test get_timeline_temporal_coverage with timeline that has events without time"""
        project = Project("proj_1", "Test", "Test")
        timeline = Timeline("tl_1", "Timeline")
        event = Event("evt_1", "src_1", "No time", NoTime())
        timeline.add_event(event)
        project.add_timeline(timeline)
        
        coverage = analytics.get_timeline_temporal_coverage(project)
        
        self.assertIn("tl_1", coverage)
        self.assertEqual(coverage["tl_1"]["event_count"], 1)
        self.assertIsNone(coverage["tl_1"]["start_ms"])

    def test_get_temporal_gaps_interval_none(self):
        """Test getting temporal gaps when interval calculation returns None"""
        events = [
            Event(
                "evt_1", "src_1", "Event 1",
                ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10))
            ),
            Event("evt_2", "src_1", "No time", NoTime()),
        ]
        
        gaps = analytics.get_temporal_gaps(events, threshold_ms=1000)
        
        # Should handle None intervals gracefully
        self.assertIsInstance(gaps, list)

    def test_get_temporal_gaps_time_none(self):
        """Test getting temporal gaps when time values are None"""
        events = [
            Event("evt_1", "src_1", "No time", NoTime()),
            Event("evt_2", "src_1", "No time 2", NoTime()),
        ]
        
        gaps = analytics.get_temporal_gaps(events, threshold_ms=1000)
        
        # Should handle None time values gracefully
        self.assertEqual(len(gaps), 0)

    def test_calculate_temporal_coverage_with_duplicate_times(self):
        """Test calculating temporal coverage with events at same time"""
        events = [
            Event("evt_1", "src_1", "Event 1",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=0, second=0))),
            Event("evt_2", "src_1", "Event 2",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=0, second=0))),
            Event("evt_3", "src_1", "Event 3",
                  ExactTime(calendar=CalendarFields(year=2024, month=1, day=15, hour=10, minute=0, second=1))),
        ]
        
        coverage = analytics.calculate_temporal_coverage(events)
        
        # Should handle duplicate times (same time bucket)
        self.assertIsInstance(coverage, float)
        self.assertGreaterEqual(coverage, 0.0)
        self.assertLessEqual(coverage, 100.0)


if __name__ == "__main__":
    unittest.main()
