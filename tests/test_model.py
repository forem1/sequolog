"""Tests for model classes - Project, Timeline, Event, Source, and Time types"""

import unittest

from sequolog.model.event import Event
from sequolog.model.project import Project
from sequolog.model.source import Source
from sequolog.model.time.exact_time import ExactTime
from sequolog.model.time.no_time import NoTime
from sequolog.model.time.range_time import RangeTime
from sequolog.model.time.relative_time import RelativeTime
from sequolog.model.time.time_base import CalendarFields, TimeBase
from sequolog.model.timeline import Timeline


class TestCalendarFields(unittest.TestCase):
    """Tests for CalendarFields dataclass"""

    def test_all_fields_none(self):
        """Test CalendarFields with all fields as None"""
        calendar = CalendarFields()
        self.assertIsNone(calendar.year)
        self.assertIsNone(calendar.month)
        self.assertIsNone(calendar.day)
        self.assertIsNone(calendar.hour)
        self.assertIsNone(calendar.minute)
        self.assertIsNone(calendar.second)
        self.assertIsNone(calendar.millisecond)
        self.assertIsNone(calendar.tz_offset_minutes)

    def test_all_fields_set(self):
        """Test CalendarFields with all fields set"""
        calendar = CalendarFields(
            year=2024,
            month=3,
            day=15,
            hour=10,
            minute=30,
            second=45,
            millisecond=123,
            tz_offset_minutes=180,
        )
        self.assertEqual(calendar.year, 2024)
        self.assertEqual(calendar.month, 3)
        self.assertEqual(calendar.day, 15)
        self.assertEqual(calendar.hour, 10)
        self.assertEqual(calendar.minute, 30)
        self.assertEqual(calendar.second, 45)
        self.assertEqual(calendar.millisecond, 123)
        self.assertEqual(calendar.tz_offset_minutes, 180)

    def test_partial_fields_year_only(self):
        """Test CalendarFields with only year set"""
        calendar = CalendarFields(year=2024)
        self.assertEqual(calendar.year, 2024)
        self.assertIsNone(calendar.month)

    def test_partial_fields_date_only(self):
        """Test CalendarFields with only date fields set"""
        calendar = CalendarFields(year=2024, month=12, day=31)
        self.assertEqual(calendar.year, 2024)
        self.assertEqual(calendar.month, 12)
        self.assertEqual(calendar.day, 31)
        self.assertIsNone(calendar.hour)

    def test_edge_case_year_zero(self):
        """Test CalendarFields with year 0 (edge case)"""
        calendar = CalendarFields(year=0)
        self.assertEqual(calendar.year, 0)

    def test_edge_case_negative_year(self):
        """Test CalendarFields with negative year (BC dates)"""
        calendar = CalendarFields(year=-100)
        self.assertEqual(calendar.year, -100)

    def test_edge_case_large_year(self):
        """Test CalendarFields with very large year"""
        calendar = CalendarFields(year=9999)
        self.assertEqual(calendar.year, 9999)

    def test_edge_case_month_boundaries(self):
        """Test CalendarFields with month at boundaries (1 and 12)"""
        calendar_min = CalendarFields(month=1)
        calendar_max = CalendarFields(month=12)
        self.assertEqual(calendar_min.month, 1)
        self.assertEqual(calendar_max.month, 12)

    def test_edge_case_day_boundaries(self):
        """Test CalendarFields with day at boundaries (1 and 31)"""
        calendar_min = CalendarFields(day=1)
        calendar_max = CalendarFields(day=31)
        self.assertEqual(calendar_min.day, 1)
        self.assertEqual(calendar_max.day, 31)

    def test_edge_case_hour_boundaries(self):
        """Test CalendarFields with hour at boundaries (0 and 23)"""
        calendar_min = CalendarFields(hour=0)
        calendar_max = CalendarFields(hour=23)
        self.assertEqual(calendar_min.hour, 0)
        self.assertEqual(calendar_max.hour, 23)

    def test_edge_case_minute_boundaries(self):
        """Test CalendarFields with minute at boundaries (0 and 59)"""
        calendar_min = CalendarFields(minute=0)
        calendar_max = CalendarFields(minute=59)
        self.assertEqual(calendar_min.minute, 0)
        self.assertEqual(calendar_max.minute, 59)

    def test_edge_case_second_boundaries(self):
        """Test CalendarFields with second at boundaries (0 and 59)"""
        calendar_min = CalendarFields(second=0)
        calendar_max = CalendarFields(second=59)
        self.assertEqual(calendar_min.second, 0)
        self.assertEqual(calendar_max.second, 59)

    def test_timezone_positive_offset(self):
        """Test CalendarFields with positive timezone offset"""
        calendar = CalendarFields(tz_offset_minutes=180)  # +03:00
        self.assertEqual(calendar.tz_offset_minutes, 180)

    def test_timezone_negative_offset(self):
        """Test CalendarFields with negative timezone offset"""
        calendar = CalendarFields(tz_offset_minutes=-300)  # -05:00
        self.assertEqual(calendar.tz_offset_minutes, -300)

    def test_timezone_zero_offset(self):
        """Test CalendarFields with zero timezone offset (UTC)"""
        calendar = CalendarFields(tz_offset_minutes=0)
        self.assertEqual(calendar.tz_offset_minutes, 0)

    def test_timezone_extreme_offsets(self):
        """Test CalendarFields with extreme timezone offsets"""
        calendar_max = CalendarFields(tz_offset_minutes=840)  # +14:00 (max)
        calendar_min = CalendarFields(tz_offset_minutes=-720)  # -12:00 (min)
        self.assertEqual(calendar_max.tz_offset_minutes, 840)
        self.assertEqual(calendar_min.tz_offset_minutes, -720)


class TestExactTime(unittest.TestCase):
    """Tests for ExactTime class"""

    def test_exact_time_creation(self):
        """Test basic ExactTime creation with calendar"""
        calendar = CalendarFields(year=2024, month=3, day=15, hour=10, minute=30)
        exact_time = ExactTime(calendar=calendar)

        self.assertIsNotNone(exact_time)
        self.assertEqual(exact_time.calendar.year, 2024)
        self.assertEqual(exact_time.calendar.month, 3)
        self.assertEqual(exact_time.calendar.day, 15)
        self.assertEqual(exact_time.calendar.hour, 10)
        self.assertEqual(exact_time.calendar.minute, 30)

    def test_exact_time_with_timestamp_only(self):
        """Test ExactTime with only timestamp"""
        exact_time = ExactTime(timestamp=1710502200)
        self.assertEqual(exact_time.timestamp, 1710502200)
        self.assertIsNone(exact_time.calendar)

    def test_exact_time_with_both_calendar_and_timestamp(self):
        """Test ExactTime with both calendar and timestamp"""
        calendar = CalendarFields(year=2024, month=3, day=15)
        exact_time = ExactTime(calendar=calendar, timestamp=1710502200)
        self.assertIsNotNone(exact_time.calendar)
        self.assertEqual(exact_time.timestamp, 1710502200)

    def test_exact_time_all_none(self):
        """Test ExactTime with all fields as None"""
        exact_time = ExactTime()
        self.assertIsNone(exact_time.calendar)
        self.assertIsNone(exact_time.timestamp)
        self.assertIsNone(exact_time.uncertainty)
        self.assertIsNone(exact_time.sequence)

    def test_exact_time_with_uncertainty(self):
        """Test ExactTime with uncertainty"""
        calendar = CalendarFields(year=2024, month=3, day=15)
        uncertainty = ExactTime(calendar=CalendarFields(year=2024, month=3, day=16))
        exact_time = ExactTime(calendar=calendar, uncertainty=uncertainty)
        self.assertIsNotNone(exact_time.uncertainty)
        self.assertEqual(exact_time.uncertainty.calendar.year, 2024)

    def test_exact_time_with_sequence(self):
        """Test ExactTime with sequence"""
        calendar = CalendarFields(year=2024, month=3, day=15)
        exact_time = ExactTime(calendar=calendar, sequence=1)
        self.assertEqual(exact_time.sequence, 1)

    def test_exact_time_with_all_fields(self):
        """Test ExactTime with all fields set"""
        calendar = CalendarFields(year=2024, month=3, day=15)
        uncertainty = ExactTime(calendar=CalendarFields(year=2024, month=3, day=16))
        exact_time = ExactTime(
            calendar=calendar, timestamp=1710502200, uncertainty=uncertainty, sequence=5
        )
        self.assertIsNotNone(exact_time.calendar)
        self.assertEqual(exact_time.timestamp, 1710502200)
        self.assertIsNotNone(exact_time.uncertainty)
        self.assertEqual(exact_time.sequence, 5)

    def test_exact_time_edge_case_zero_timestamp(self):
        """Test ExactTime with zero timestamp (Unix epoch)"""
        exact_time = ExactTime(timestamp=0)
        self.assertEqual(exact_time.timestamp, 0)

    def test_exact_time_edge_case_negative_timestamp(self):
        """Test ExactTime with negative timestamp (before Unix epoch)"""
        exact_time = ExactTime(timestamp=-86400)
        self.assertEqual(exact_time.timestamp, -86400)

    def test_exact_time_edge_case_large_timestamp(self):
        """Test ExactTime with very large timestamp"""
        exact_time = ExactTime(timestamp=2147483647)  # Max 32-bit signed int
        self.assertEqual(exact_time.timestamp, 2147483647)

    def test_exact_time_edge_case_sequence_zero(self):
        """Test ExactTime with sequence 0"""
        exact_time = ExactTime(sequence=0)
        self.assertEqual(exact_time.sequence, 0)

    def test_exact_time_edge_case_sequence_negative(self):
        """Test ExactTime with negative sequence"""
        exact_time = ExactTime(sequence=-1)
        self.assertEqual(exact_time.sequence, -1)


class TestRangeTime(unittest.TestCase):
    """Tests for RangeTime class"""

    def test_range_time_with_start_only(self):
        """Test RangeTime with only start time"""
        start = CalendarFields(year=2024, month=3, day=15)
        range_time = RangeTime(start=start)
        self.assertEqual(range_time.start.year, 2024)
        self.assertIsNone(range_time.end)

    def test_range_time_with_end_only(self):
        """Test RangeTime with only end time"""
        end = CalendarFields(year=2024, month=3, day=20)
        range_time = RangeTime(end=end)
        self.assertEqual(range_time.end.year, 2024)
        self.assertIsNone(range_time.start)

    def test_range_time_with_both_start_and_end(self):
        """Test RangeTime with both start and end"""
        start = CalendarFields(year=2024, month=3, day=15)
        end = CalendarFields(year=2024, month=3, day=20)
        range_time = RangeTime(start=start, end=end)
        self.assertEqual(range_time.start.year, 2024)
        self.assertEqual(range_time.end.year, 2024)
        self.assertEqual(range_time.start.day, 15)
        self.assertEqual(range_time.end.day, 20)

    def test_range_time_all_none(self):
        """Test RangeTime with all fields as None"""
        range_time = RangeTime()
        self.assertIsNone(range_time.start)
        self.assertIsNone(range_time.end)
        self.assertIsNone(range_time.timestamp)
        self.assertIsNone(range_time.uncertainty)
        self.assertIsNone(range_time.sequence)

    def test_range_time_with_timestamp(self):
        """Test RangeTime with timestamp"""
        start = CalendarFields(year=2024, month=3, day=15)
        range_time = RangeTime(start=start, timestamp=1710502200)
        self.assertEqual(range_time.timestamp, 1710502200)

    def test_range_time_with_uncertainty(self):
        """Test RangeTime with uncertainty"""
        start = CalendarFields(year=2024, month=3, day=15)
        end = CalendarFields(year=2024, month=3, day=20)
        uncertainty = RangeTime(
            start=CalendarFields(year=2024, month=3, day=14),
            end=CalendarFields(year=2024, month=3, day=21),
        )
        range_time = RangeTime(start=start, end=end, uncertainty=uncertainty)
        self.assertIsNotNone(range_time.uncertainty)
        self.assertEqual(range_time.uncertainty.start.day, 14)

    def test_range_time_with_sequence(self):
        """Test RangeTime with sequence"""
        start = CalendarFields(year=2024, month=3, day=15)
        range_time = RangeTime(start=start, sequence=10)
        self.assertEqual(range_time.sequence, 10)

    def test_range_time_with_all_fields(self):
        """Test RangeTime with all fields set"""
        start = CalendarFields(year=2024, month=1, day=15)
        end = CalendarFields(year=2024, month=2, day=20)
        uncertainty = RangeTime(
            start=CalendarFields(year=2024, month=3, day=14),
            end=CalendarFields(year=2024, month=4, day=21),
        )
        range_time = RangeTime(
            start=start, end=end, timestamp=1710502200, uncertainty=uncertainty, sequence=3
        )
        self.assertIsNotNone(range_time.start)
        self.assertIsNotNone(range_time.end)
        self.assertEqual(range_time.timestamp, 1710502200)
        self.assertIsNotNone(range_time.uncertainty)
        self.assertEqual(range_time.sequence, 3)

    def test_range_time_start_after_end(self):
        """Test RangeTime where start is after end (edge case - should still be valid)"""
        start = CalendarFields(year=2024, month=3, day=20)
        end = CalendarFields(year=2024, month=3, day=15)
        range_time = RangeTime(start=start, end=end)
        self.assertEqual(range_time.start.day, 20)
        self.assertEqual(range_time.end.day, 15)

    def test_range_time_same_start_and_end(self):
        """Test RangeTime where start equals end"""
        calendar = CalendarFields(year=2024, month=3, day=15)
        range_time = RangeTime(start=calendar, end=calendar)
        self.assertEqual(range_time.start, range_time.end)

    def test_range_time_edge_case_empty_calendar_fields(self):
        """Test RangeTime with empty CalendarFields"""
        start = CalendarFields()
        end = CalendarFields()
        range_time = RangeTime(start=start, end=end)
        self.assertIsNotNone(range_time.start)
        self.assertIsNotNone(range_time.end)


class TestRelativeTime(unittest.TestCase):
    """Tests for RelativeTime class"""

    def test_relative_time_basic(self):
        """Test basic RelativeTime creation"""
        relative_time = RelativeTime(relative_to="event_start")
        self.assertEqual(relative_time.relative_to, "event_start")
        self.assertEqual(relative_time.offset_ms, 0)

    def test_relative_time_with_positive_offset(self):
        """Test RelativeTime with positive offset"""
        relative_time = RelativeTime(relative_to="event_start", offset_ms=5000)
        self.assertEqual(relative_time.relative_to, "event_start")
        self.assertEqual(relative_time.offset_ms, 5000)

    def test_relative_time_with_negative_offset(self):
        """Test RelativeTime with negative offset"""
        relative_time = RelativeTime(relative_to="event_end", offset_ms=-3000)
        self.assertEqual(relative_time.relative_to, "event_end")
        self.assertEqual(relative_time.offset_ms, -3000)

    def test_relative_time_with_zero_offset(self):
        """Test RelativeTime with zero offset"""
        relative_time = RelativeTime(relative_to="event_start", offset_ms=0)
        self.assertEqual(relative_time.offset_ms, 0)

    def test_relative_time_with_uncertainty(self):
        """Test RelativeTime with uncertainty"""
        uncertainty = RelativeTime(relative_to="event_start", offset_ms=1000)
        relative_time = RelativeTime(
            relative_to="event_start", offset_ms=5000, uncertainty=uncertainty
        )
        self.assertIsNotNone(relative_time.uncertainty)
        self.assertEqual(relative_time.uncertainty.offset_ms, 1000)

    def test_relative_time_with_sequence(self):
        """Test RelativeTime with sequence"""
        relative_time = RelativeTime(relative_to="event_start", sequence=7)
        self.assertEqual(relative_time.sequence, 7)

    def test_relative_time_with_all_fields(self):
        """Test RelativeTime with all fields set"""
        uncertainty = RelativeTime(relative_to="event_start", offset_ms=1000)
        relative_time = RelativeTime(
            relative_to="event_end", offset_ms=-5000, uncertainty=uncertainty, sequence=2
        )
        self.assertEqual(relative_time.relative_to, "event_end")
        self.assertEqual(relative_time.offset_ms, -5000)
        self.assertIsNotNone(relative_time.uncertainty)
        self.assertEqual(relative_time.sequence, 2)

    def test_relative_time_edge_case_empty_string(self):
        """Test RelativeTime with empty relative_to string"""
        relative_time = RelativeTime(relative_to="")
        self.assertEqual(relative_time.relative_to, "")

    def test_relative_time_edge_case_large_positive_offset(self):
        """Test RelativeTime with very large positive offset"""
        relative_time = RelativeTime(relative_to="event_start", offset_ms=2147483647)
        self.assertEqual(relative_time.offset_ms, 2147483647)

    def test_relative_time_edge_case_large_negative_offset(self):
        """Test RelativeTime with very large negative offset"""
        relative_time = RelativeTime(relative_to="event_start", offset_ms=-2147483648)
        self.assertEqual(relative_time.offset_ms, -2147483648)

    def test_relative_time_edge_case_unicode_string(self):
        """Test RelativeTime with Unicode characters in relative_to"""
        relative_time = RelativeTime(relative_to="событие_начало")
        self.assertEqual(relative_time.relative_to, "событие_начало")

    def test_relative_time_edge_case_long_string(self):
        """Test RelativeTime with very long relative_to string"""
        long_string = "event_" + "x" * 1000
        relative_time = RelativeTime(relative_to=long_string)
        self.assertEqual(relative_time.relative_to, long_string)


class TestNoTime(unittest.TestCase):
    """Tests for NoTime class"""

    def test_no_time_without_sequence(self):
        """Test NoTime without sequence (default None)"""
        no_time = NoTime()
        self.assertIsNone(no_time.sequence)

    def test_no_time_with_sequence(self):
        """Test NoTime with sequence"""
        no_time = NoTime(sequence=5)
        self.assertEqual(no_time.sequence, 5)

    def test_no_time_edge_case_sequence_zero(self):
        """Test NoTime with sequence 0"""
        no_time = NoTime(sequence=0)
        self.assertEqual(no_time.sequence, 0)

    def test_no_time_edge_case_sequence_negative(self):
        """Test NoTime with negative sequence"""
        no_time = NoTime(sequence=-10)
        self.assertEqual(no_time.sequence, -10)

    def test_no_time_edge_case_large_sequence(self):
        """Test NoTime with very large sequence"""
        no_time = NoTime(sequence=999999)
        self.assertEqual(no_time.sequence, 999999)

    def test_no_time_inherits_from_time_base(self):
        """Test that NoTime properly inherits from TimeBase"""
        no_time = NoTime(sequence=1)
        self.assertIsInstance(no_time, TimeBase)
        # These should be None by default from TimeBase
        self.assertIsNone(no_time.calendar)
        self.assertIsNone(no_time.timestamp)
        self.assertIsNone(no_time.uncertainty)


class TestSource(unittest.TestCase):
    """Tests for Source class"""

    def test_source_creation(self):
        """Test basic Source creation"""
        source = Source("src_1", "Test source", "ref://test")
        self.assertEqual(source.source_id, "src_1")
        self.assertEqual(source.description, "Test source")
        self.assertEqual(source.reference, "ref://test")

    def test_source_edge_case_empty_strings(self):
        """Test Source with empty strings"""
        source = Source("", "", "")
        self.assertEqual(source.source_id, "")
        self.assertEqual(source.description, "")
        self.assertEqual(source.reference, "")

    def test_source_edge_case_long_strings(self):
        """Test Source with very long strings"""
        long_id = "src_" + "x" * 1000
        long_desc = "Description " + "y" * 1000
        long_ref = "ref://" + "z" * 1000
        source = Source(long_id, long_desc, long_ref)
        self.assertEqual(len(source.source_id), 1004)  # "src_" = 4 chars + 1000
        self.assertEqual(len(source.description), 1012)  # "Description " = 12 chars + 1000
        self.assertEqual(len(source.reference), 1006)  # "ref://" = 6 chars + 1000


class TestEvent(unittest.TestCase):
    """Tests for Event class"""

    def test_event_creation(self):
        """Test basic Event creation with source_id"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event = Event("event_1", "src_1", "Test event", time)
        self.assertEqual(event.event_id, "event_1")
        self.assertEqual(event.source_id, "src_1")
        self.assertEqual(event.description, "Test event")
        self.assertIsNotNone(event.time)

    def test_event_with_different_time_types(self):
        """Test Event with different time types"""
        # ExactTime
        exact_time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "Event with exact time", exact_time)
        self.assertIsInstance(event1.time, ExactTime)

        # RangeTime
        range_time = RangeTime(
            start=CalendarFields(year=2024, month=3, day=15),
            end=CalendarFields(year=2024, month=3, day=20),
        )
        event2 = Event("event_2", "src_1", "Event with range time", range_time)
        self.assertIsInstance(event2.time, RangeTime)

        # RelativeTime
        relative_time = RelativeTime(relative_to="event_1", offset_ms=3600000)
        event3 = Event("event_3", "src_1", "Event with relative time", relative_time)
        self.assertIsInstance(event3.time, RelativeTime)

        # NoTime
        no_time = NoTime(sequence=1)
        event4 = Event("event_4", "src_1", "Event with no time", no_time)
        self.assertIsInstance(event4.time, NoTime)

    def test_event_edge_case_empty_strings(self):
        """Test Event with empty strings"""
        time = ExactTime(calendar=CalendarFields(year=2024))
        event = Event("", "", "", time)
        self.assertEqual(event.event_id, "")
        self.assertEqual(event.source_id, "")
        self.assertEqual(event.description, "")

    def test_event_same_source_id_multiple_events(self):
        """Test multiple events with same source_id"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "First event", time)
        event2 = Event("event_2", "src_1", "Second event", time)
        self.assertEqual(event1.source_id, event2.source_id)
        self.assertNotEqual(event1.event_id, event2.event_id)


class TestTimeline(unittest.TestCase):
    """Tests for Timeline class"""

    def test_timeline_creation(self):
        """Test basic Timeline creation"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "First event", time)
        event2 = Event("event_2", "src_1", "Second event", time)
        timeline = Timeline("tl_1", "Test timeline", [event1, event2])
        self.assertEqual(timeline.timeline_id, "tl_1")
        self.assertEqual(timeline.description, "Test timeline")
        self.assertEqual(len(timeline.events), 2)

    def test_timeline_empty_events(self):
        """Test Timeline with empty events list"""
        timeline = Timeline("tl_empty", "Empty timeline", [])
        self.assertEqual(len(timeline.events), 0)
        self.assertEqual(timeline.events, [])

    def test_timeline_single_event(self):
        """Test Timeline with single event"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event = Event("event_1", "src_1", "Single event", time)
        timeline = Timeline("tl_single", "Single event timeline", [event])
        self.assertEqual(len(timeline.events), 1)
        self.assertEqual(timeline.events[0].event_id, "event_1")

    def test_timeline_multiple_events(self):
        """Test Timeline with multiple events"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        events = [Event(f"event_{i}", "src_1", f"Event {i}", time) for i in range(10)]
        timeline = Timeline("tl_multi", "Multiple events timeline", events)
        self.assertEqual(len(timeline.events), 10)
        self.assertEqual(timeline.events[0].event_id, "event_0")
        self.assertEqual(timeline.events[-1].event_id, "event_9")

    def test_timeline_events_with_different_sources(self):
        """Test Timeline with events from different sources"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "Event from source 1", time)
        event2 = Event("event_2", "src_2", "Event from source 2", time)
        event3 = Event("event_3", "src_1", "Another event from source 1", time)
        timeline = Timeline("tl_mixed", "Mixed sources timeline", [event1, event2, event3])
        self.assertEqual(len(timeline.events), 3)
        self.assertEqual(timeline.events[0].source_id, "src_1")
        self.assertEqual(timeline.events[1].source_id, "src_2")
        self.assertEqual(timeline.events[2].source_id, "src_1")

    def test_timeline_add_event_duplicate_id(self):
        """Test Timeline.add_event() raises ValueError for duplicate event_id"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "First event", time)
        event2 = Event("event_1", "src_1", "Duplicate event", time)
        timeline = Timeline("tl_1", "Test timeline", [event1])
        
        with self.assertRaises(ValueError) as context:
            timeline.add_event(event2)
        self.assertIn("already exists in timeline", str(context.exception))

    def test_timeline_add_event_unique_id(self):
        """Test Timeline.add_event() successfully adds event with unique ID"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "First event", time)
        event2 = Event("event_2", "src_1", "Second event", time)
        timeline = Timeline("tl_1", "Test timeline", [event1])
        
        timeline.add_event(event2)
        self.assertEqual(len(timeline.events), 2)
        self.assertTrue(timeline.has_event("event_1"))
        self.assertTrue(timeline.has_event("event_2"))


class TestProject(unittest.TestCase):
    """Tests for Project class"""

    def test_project_creation(self):
        """Test basic Project creation"""
        source1 = Source("src_1", "Source 1", "ref://source1")
        source2 = Source("src_2", "Source 2", "ref://source2")
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "Event 1", time)
        event2 = Event("event_2", "src_2", "Event 2", time)
        timeline = Timeline("tl_1", "Timeline 1", [event1, event2])
        project = Project(
            "proj_1", "Test Project", "Test description", [timeline], [source1, source2]
        )
        self.assertEqual(project.project_id, "proj_1")
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.description, "Test description")
        self.assertEqual(len(project.timelines), 1)
        self.assertEqual(len(project.sources), 2)

    def test_project_empty_timelines(self):
        """Test Project with empty timelines"""
        source = Source("src_1", "Source 1", "ref://source1")
        project = Project("proj_empty", "Empty Project", "No timelines", [], [source])
        self.assertEqual(len(project.timelines), 0)
        self.assertEqual(project.timelines, [])

    def test_project_empty_sources(self):
        """Test Project with empty sources"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event = Event("event_1", "src_1", "Event 1", time)
        timeline = Timeline("tl_1", "Timeline 1", [event])
        project = Project("proj_no_sources", "No Sources Project", "No sources", [timeline], [])
        self.assertEqual(len(project.sources), 0)
        self.assertEqual(project.sources, [])

    def test_project_multiple_timelines(self):
        """Test Project with multiple timelines"""
        source = Source("src_1", "Source 1", "ref://source1")
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        timelines = [
            Timeline(f"tl_{i}", f"Timeline {i}", [Event(f"event_{i}", "src_1", f"Event {i}", time)])
            for i in range(5)
        ]
        project = Project("proj_multi", "Multiple Timelines", "Many timelines", timelines, [source])
        self.assertEqual(len(project.timelines), 5)
        self.assertEqual(project.timelines[0].timeline_id, "tl_0")
        self.assertEqual(project.timelines[-1].timeline_id, "tl_4")

    def test_project_multiple_sources(self):
        """Test Project with multiple sources"""
        sources = [Source(f"src_{i}", f"Source {i}", f"ref://source{i}") for i in range(10)]
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event = Event("event_1", "src_1", "Event 1", time)
        timeline = Timeline("tl_1", "Timeline 1", [event])
        project = Project(
            "proj_multi_sources", "Multiple Sources", "Many sources", [timeline], sources
        )
        self.assertEqual(len(project.sources), 10)
        self.assertEqual(project.sources[0].source_id, "src_0")
        self.assertEqual(project.sources[-1].source_id, "src_9")

    def test_project_sources_referenced_in_events(self):
        """Test that sources in project match source_ids in events"""
        source1 = Source("src_1", "Source 1", "ref://source1")
        source2 = Source("src_2", "Source 2", "ref://source2")
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "Event from source 1", time)
        event2 = Event("event_2", "src_2", "Event from source 2", time)
        event3 = Event("event_3", "src_1", "Another event from source 1", time)
        timeline = Timeline("tl_1", "Timeline 1", [event1, event2, event3])
        project = Project(
            "proj_refs", "Reference Test", "Test source references", [timeline], [source1, source2]
        )
        # Verify sources exist in project
        source_ids = {s.source_id for s in project.sources}
        self.assertIn("src_1", source_ids)
        self.assertIn("src_2", source_ids)
        # Verify events reference these sources
        event_source_ids = {e.source_id for e in timeline.events}
        self.assertTrue(event_source_ids.issubset(source_ids))

    def test_project_edge_case_empty_strings(self):
        """Test Project with empty strings"""
        source = Source("src_1", "Source 1", "ref://source1")
        timeline = Timeline("tl_1", "Timeline 1", [])
        project = Project("", "", "", [timeline], [source])
        self.assertEqual(project.project_id, "")
        self.assertEqual(project.title, "")
        self.assertEqual(project.description, "")

    def test_project_all_empty(self):
        """Test Project with all empty collections"""
        project = Project("proj_empty_all", "Empty Project", "Everything empty", [], [])
        self.assertEqual(len(project.timelines), 0)
        self.assertEqual(len(project.sources), 0)
        self.assertEqual(project.timelines, [])
        self.assertEqual(project.sources, [])

    def test_project_add_source_duplicate_id(self):
        """Test Project.add_source() raises ValueError for duplicate source_id"""
        source1 = Source("src_1", "Source 1", "ref://source1")
        source2 = Source("src_1", "Source 2", "ref://source2")
        project = Project("proj_1", "Test Project", "Test", [], [source1])
        
        with self.assertRaises(ValueError) as context:
            project.add_source(source2)
        self.assertIn("already exists in project", str(context.exception))

    def test_project_add_source_unique_id(self):
        """Test Project.add_source() successfully adds source with unique ID"""
        source1 = Source("src_1", "Source 1", "ref://source1")
        source2 = Source("src_2", "Source 2", "ref://source2")
        project = Project("proj_1", "Test Project", "Test", [], [source1])
        
        project.add_source(source2)
        self.assertEqual(len(project.sources), 2)
        self.assertTrue(project.has_source("src_1"))
        self.assertTrue(project.has_source("src_2"))

    def test_project_add_timeline_duplicate_id(self):
        """Test Project.add_timeline() raises ValueError for duplicate timeline_id"""
        timeline1 = Timeline("tl_1", "Timeline 1", [])
        timeline2 = Timeline("tl_1", "Timeline 2", [])
        project = Project("proj_1", "Test Project", "Test", [timeline1], [])
        
        with self.assertRaises(ValueError) as context:
            project.add_timeline(timeline2)
        self.assertIn("already exists in project", str(context.exception))

    def test_project_add_timeline_unique_id(self):
        """Test Project.add_timeline() successfully adds timeline with unique ID"""
        timeline1 = Timeline("tl_1", "Timeline 1", [])
        timeline2 = Timeline("tl_2", "Timeline 2", [])
        project = Project("proj_1", "Test Project", "Test", [timeline1], [])
        
        project.add_timeline(timeline2)
        self.assertEqual(len(project.timelines), 2)
        self.assertTrue(project.has_timeline("tl_1"))
        self.assertTrue(project.has_timeline("tl_2"))

    def test_project_add_event_to_timeline_duplicate_id_global(self):
        """Test Project.add_event_to_timeline() raises ValueError for duplicate event_id across timelines"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "First event", time)
        event2 = Event("event_1", "src_1", "Duplicate event", time)
        timeline1 = Timeline("tl_1", "Timeline 1", [event1])
        timeline2 = Timeline("tl_2", "Timeline 2", [])
        project = Project("proj_1", "Test Project", "Test", [timeline1, timeline2], [])
        
        with self.assertRaises(ValueError) as context:
            project.add_event_to_timeline("tl_2", event2)
        self.assertIn("already exists in project", str(context.exception))

    def test_project_add_event_to_timeline_unique_id(self):
        """Test Project.add_event_to_timeline() successfully adds event with unique ID"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "First event", time)
        event2 = Event("event_2", "src_1", "Second event", time)
        timeline = Timeline("tl_1", "Timeline 1", [event1])
        project = Project("proj_1", "Test Project", "Test", [timeline], [])
        
        project.add_event_to_timeline("tl_1", event2)
        self.assertEqual(len(timeline.events), 2)
        self.assertTrue(project.has_event("event_1"))
        self.assertTrue(project.has_event("event_2"))

    def test_project_add_event_to_timeline_nonexistent_timeline(self):
        """Test Project.add_event_to_timeline() raises ValueError for nonexistent timeline"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event = Event("event_1", "src_1", "Test event", time)
        timeline = Timeline("tl_1", "Timeline 1", [])
        project = Project("proj_1", "Test Project", "Test", [timeline], [])
        
        with self.assertRaises(ValueError) as context:
            project.add_event_to_timeline("tl_nonexistent", event)
        self.assertIn("not found in project", str(context.exception))

    def test_project_has_event(self):
        """Test Project.has_event() checks for event across all timelines"""
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "Event 1", time)
        event2 = Event("event_2", "src_1", "Event 2", time)
        timeline1 = Timeline("tl_1", "Timeline 1", [event1])
        timeline2 = Timeline("tl_2", "Timeline 2", [event2])
        project = Project("proj_1", "Test Project", "Test", [timeline1, timeline2], [])
        
        self.assertTrue(project.has_event("event_1"))
        self.assertTrue(project.has_event("event_2"))
        self.assertFalse(project.has_event("event_3"))

    def test_project_same_source_id_in_different_events(self):
        """Test that same source_id can be used in different events (this is allowed)"""
        source = Source("src_1", "Source 1", "ref://source1")
        time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15))
        event1 = Event("event_1", "src_1", "Event 1 from source", time)
        event2 = Event("event_2", "src_1", "Event 2 from same source", time)
        timeline = Timeline("tl_1", "Timeline 1", [])
        project = Project("proj_1", "Test Project", "Test", [timeline], [source])
        
        # Both events should be addable with same source_id
        project.add_event_to_timeline("tl_1", event1)
        project.add_event_to_timeline("tl_1", event2)
        
        self.assertEqual(len(timeline.events), 2)
        self.assertEqual(timeline.events[0].source_id, "src_1")
        self.assertEqual(timeline.events[1].source_id, "src_1")
        self.assertNotEqual(timeline.events[0].event_id, timeline.events[1].event_id)


if __name__ == "__main__":
    unittest.main()
