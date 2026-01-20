"""Tests for serializer core module"""

import os
import tempfile
import unittest

from sequolog.core.serializer import (
    load_project,
    project_from_dict,
    project_from_json,
    project_to_dict,
    project_to_json,
    save_project,
)
from sequolog.model.event import Event
from sequolog.model.project import Project
from sequolog.model.source import Source
from sequolog.model.time.exact_time import ExactTime
from sequolog.model.time.no_time import NoTime
from sequolog.model.time.range_time import RangeTime
from sequolog.model.time.relative_time import RelativeTime
from sequolog.model.time.time_base import CalendarFields
from sequolog.model.timeline import Timeline


class TestSerializer(unittest.TestCase):
    """Tests for serializer module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create test project with all time types
        self.source1 = Source("src_1", "Source 1", "ref://source1")
        self.source2 = Source("src_2", "Source 2", "ref://source2")

        exact_time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15, hour=10))
        range_time = RangeTime(
            start=CalendarFields(year=2024, month=3, day=15),
            end=CalendarFields(year=2024, month=3, day=20),
        )
        relative_time = RelativeTime(relative_to="event_1", offset_ms=3600000)
        no_time = NoTime(sequence=1)

        self.event1 = Event("event_1", "src_1", "Event with exact time", exact_time)
        self.event2 = Event("event_2", "src_1", "Event with range time", range_time)
        self.event3 = Event("event_3", "src_2", "Event with relative time", relative_time)
        self.event4 = Event("event_4", "src_2", "Event with no time", no_time)

        self.timeline = Timeline(
            "tl_1", "Test Timeline", [self.event1, self.event2, self.event3, self.event4]
        )

        self.project = Project(
            "proj_1",
            "Test Project",
            "A test project for serialization",
            [self.timeline],
            [self.source1, self.source2],
        )

    def test_project_to_dict(self):
        """Test project_to_dict serialization"""
        data = project_to_dict(self.project)

        self.assertIsInstance(data, dict)
        self.assertEqual(data["project_id"], "proj_1")
        self.assertEqual(data["title"], "Test Project")
        self.assertEqual(data["description"], "A test project for serialization")
        self.assertEqual(len(data["timelines"]), 1)
        self.assertEqual(len(data["sources"]), 2)

    def test_project_from_dict(self):
        """Test project_from_dict deserialization"""
        data = project_to_dict(self.project)
        loaded_project = project_from_dict(data)

        self.assertEqual(loaded_project.project_id, self.project.project_id)
        self.assertEqual(loaded_project.title, self.project.title)
        self.assertEqual(loaded_project.description, self.project.description)
        self.assertEqual(loaded_project.get_timeline_count(), self.project.get_timeline_count())
        self.assertEqual(loaded_project.get_source_count(), self.project.get_source_count())
        self.assertEqual(loaded_project.get_event_count(), self.project.get_event_count())

    def test_timeline_serialization(self):
        """Test timeline serialization and deserialization"""
        data = project_to_dict(self.project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_1")
        self.assertIsNotNone(loaded_timeline)
        self.assertEqual(loaded_timeline.timeline_id, self.timeline.timeline_id)
        self.assertEqual(loaded_timeline.description, self.timeline.description)
        self.assertEqual(len(loaded_timeline.events), len(self.timeline.events))

    def test_event_serialization(self):
        """Test event serialization and deserialization"""
        data = project_to_dict(self.project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_1")
        loaded_event1 = loaded_timeline.get_event("event_1")
        loaded_event2 = loaded_timeline.get_event("event_2")
        loaded_event3 = loaded_timeline.get_event("event_3")
        loaded_event4 = loaded_timeline.get_event("event_4")

        self.assertIsNotNone(loaded_event1)
        self.assertEqual(loaded_event1.event_id, self.event1.event_id)
        self.assertEqual(loaded_event1.source_id, self.event1.source_id)
        self.assertEqual(loaded_event1.description, self.event1.description)

        self.assertIsNotNone(loaded_event2)
        self.assertEqual(loaded_event2.event_id, self.event2.event_id)

        self.assertIsNotNone(loaded_event3)
        self.assertEqual(loaded_event3.event_id, self.event3.event_id)

        self.assertIsNotNone(loaded_event4)
        self.assertEqual(loaded_event4.event_id, self.event4.event_id)

    def test_time_types_serialization(self):
        """Test all time types serialization"""
        data = project_to_dict(self.project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_1")

        # ExactTime
        loaded_event1 = loaded_timeline.get_event("event_1")
        self.assertIsInstance(loaded_event1.time, ExactTime)
        self.assertIsNotNone(loaded_event1.time.calendar)
        self.assertEqual(loaded_event1.time.calendar.year, 2024)
        self.assertEqual(loaded_event1.time.calendar.month, 3)
        self.assertEqual(loaded_event1.time.calendar.day, 15)
        self.assertEqual(loaded_event1.time.calendar.hour, 10)

        # RangeTime
        loaded_event2 = loaded_timeline.get_event("event_2")
        self.assertIsInstance(loaded_event2.time, RangeTime)
        self.assertIsNotNone(loaded_event2.time.start)
        self.assertIsNotNone(loaded_event2.time.end)
        self.assertEqual(loaded_event2.time.start.year, 2024)
        self.assertEqual(loaded_event2.time.end.year, 2024)

        # RelativeTime
        loaded_event3 = loaded_timeline.get_event("event_3")
        self.assertIsInstance(loaded_event3.time, RelativeTime)
        self.assertEqual(loaded_event3.time.relative_to, "event_1")
        self.assertEqual(loaded_event3.time.offset_ms, 3600000)

        # NoTime
        loaded_event4 = loaded_timeline.get_event("event_4")
        self.assertIsInstance(loaded_event4.time, NoTime)
        self.assertEqual(loaded_event4.time.sequence, 1)

    def test_source_serialization(self):
        """Test source serialization and deserialization"""
        data = project_to_dict(self.project)
        loaded_project = project_from_dict(data)

        loaded_source1 = loaded_project.get_source("src_1")
        loaded_source2 = loaded_project.get_source("src_2")

        self.assertIsNotNone(loaded_source1)
        self.assertEqual(loaded_source1.source_id, self.source1.source_id)
        self.assertEqual(loaded_source1.description, self.source1.description)
        self.assertEqual(loaded_source1.reference, self.source1.reference)

        self.assertIsNotNone(loaded_source2)
        self.assertEqual(loaded_source2.source_id, self.source2.source_id)

    def test_project_to_json(self):
        """Test project_to_json"""
        json_str = project_to_json(self.project)

        self.assertIsInstance(json_str, str)
        self.assertIn("proj_1", json_str)
        self.assertIn("Test Project", json_str)
        self.assertIn("timelines", json_str)
        self.assertIn("sources", json_str)

    def test_project_from_json(self):
        """Test project_from_json"""
        json_str = project_to_json(self.project)
        loaded_project = project_from_json(json_str)

        self.assertEqual(loaded_project.project_id, self.project.project_id)
        self.assertEqual(loaded_project.title, self.project.title)
        self.assertEqual(loaded_project.get_timeline_count(), self.project.get_timeline_count())
        self.assertEqual(loaded_project.get_source_count(), self.project.get_source_count())
        self.assertEqual(loaded_project.get_event_count(), self.project.get_event_count())

    def test_save_and_load_project(self):
        """Test save_project and load_project file I/O"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            save_project(self.project, temp_file)
            self.assertTrue(os.path.exists(temp_file))

            loaded_project = load_project(temp_file)

            self.assertEqual(loaded_project.project_id, self.project.project_id)
            self.assertEqual(loaded_project.title, self.project.title)
            self.assertEqual(loaded_project.description, self.project.description)
            self.assertEqual(loaded_project.get_timeline_count(), self.project.get_timeline_count())
            self.assertEqual(loaded_project.get_source_count(), self.project.get_source_count())
            self.assertEqual(loaded_project.get_event_count(), self.project.get_event_count())

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_empty_project_serialization(self):
        """Test serialization of empty project"""
        empty_project = Project("empty_proj", "Empty Project", "", [], [])
        data = project_to_dict(empty_project)
        loaded_project = project_from_dict(data)

        self.assertEqual(loaded_project.project_id, "empty_proj")
        self.assertEqual(loaded_project.get_timeline_count(), 0)
        self.assertEqual(loaded_project.get_source_count(), 0)
        self.assertEqual(loaded_project.get_event_count(), 0)

    def test_project_with_uncertainty(self):
        """Test serialization of time with uncertainty"""
        uncertainty = ExactTime(calendar=CalendarFields(year=2024, month=3, day=16))
        exact_time = ExactTime(
            calendar=CalendarFields(year=2024, month=3, day=15), uncertainty=uncertainty
        )
        event = Event("event_uncertain", "src_1", "Event with uncertainty", exact_time)
        timeline = Timeline("tl_uncertain", "Timeline with uncertainty", [event])
        project = Project("proj_uncertain", "Uncertainty Test", "", [timeline], [self.source1])

        data = project_to_dict(project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_uncertain")
        loaded_event = loaded_timeline.get_event("event_uncertain")

        self.assertIsNotNone(loaded_event.time.uncertainty)
        self.assertIsInstance(loaded_event.time.uncertainty, ExactTime)
        self.assertEqual(loaded_event.time.uncertainty.calendar.year, 2024)
        self.assertEqual(loaded_event.time.uncertainty.calendar.day, 16)

    def test_project_with_sequence(self):
        """Test serialization of time with sequence"""
        exact_time = ExactTime(calendar=CalendarFields(year=2024, month=3, day=15), sequence=5)
        event = Event("event_seq", "src_1", "Event with sequence", exact_time)
        timeline = Timeline("tl_seq", "Timeline with sequence", [event])
        project = Project("proj_seq", "Sequence Test", "", [timeline], [self.source1])

        data = project_to_dict(project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_seq")
        loaded_event = loaded_timeline.get_event("event_seq")

        self.assertEqual(loaded_event.time.sequence, 5)

    def test_project_with_timestamp(self):
        """Test serialization of time with timestamp"""
        exact_time = ExactTime(timestamp=1710502200)
        event = Event("event_ts", "src_1", "Event with timestamp", exact_time)
        timeline = Timeline("tl_ts", "Timeline with timestamp", [event])
        project = Project("proj_ts", "Timestamp Test", "", [timeline], [self.source1])

        data = project_to_dict(project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_ts")
        loaded_event = loaded_timeline.get_event("event_ts")

        self.assertEqual(loaded_event.time.timestamp, 1710502200)

    def test_project_with_partial_calendar(self):
        """Test serialization with partial calendar fields"""
        exact_time = ExactTime(calendar=CalendarFields(year=2024, month=3))
        event = Event("event_partial", "src_1", "Event with partial date", exact_time)
        timeline = Timeline("tl_partial", "Timeline with partial date", [event])
        project = Project("proj_partial", "Partial Date Test", "", [timeline], [self.source1])

        data = project_to_dict(project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_partial")
        loaded_event = loaded_timeline.get_event("event_partial")

        self.assertEqual(loaded_event.time.calendar.year, 2024)
        self.assertEqual(loaded_event.time.calendar.month, 3)
        self.assertIsNone(loaded_event.time.calendar.day)

    def test_project_with_timezone(self):
        """Test serialization with timezone offset"""
        exact_time = ExactTime(
            calendar=CalendarFields(year=2024, month=3, day=15, hour=10, tz_offset_minutes=180)
        )
        event = Event("event_tz", "src_1", "Event with timezone", exact_time)
        timeline = Timeline("tl_tz", "Timeline with timezone", [event])
        project = Project("proj_tz", "Timezone Test", "", [timeline], [self.source1])

        data = project_to_dict(project)
        loaded_project = project_from_dict(data)

        loaded_timeline = loaded_project.get_timeline("tl_tz")
        loaded_event = loaded_timeline.get_event("event_tz")

        self.assertEqual(loaded_event.time.calendar.tz_offset_minutes, 180)

    def test_multiple_timelines_serialization(self):
        """Test serialization of project with multiple timelines"""
        timeline1 = Timeline("tl_1", "Timeline 1", [self.event1])
        timeline2 = Timeline("tl_2", "Timeline 2", [self.event2])
        project = Project(
            "proj_multi", "Multi Timeline", "", [timeline1, timeline2], [self.source1]
        )

        data = project_to_dict(project)
        loaded_project = project_from_dict(data)

        self.assertEqual(loaded_project.get_timeline_count(), 2)
        self.assertIsNotNone(loaded_project.get_timeline("tl_1"))
        self.assertIsNotNone(loaded_project.get_timeline("tl_2"))

    def test_multiple_sources_serialization(self):
        """Test serialization of project with multiple sources"""
        source3 = Source("src_3", "Source 3", "ref://source3")
        project = Project(
            "proj_multi_src",
            "Multi Source",
            "",
            [self.timeline],
            [self.source1, self.source2, source3],
        )

        data = project_to_dict(project)
        loaded_project = project_from_dict(data)

        self.assertEqual(loaded_project.get_source_count(), 3)
        self.assertIsNotNone(loaded_project.get_source("src_1"))
        self.assertIsNotNone(loaded_project.get_source("src_2"))
        self.assertIsNotNone(loaded_project.get_source("src_3"))


if __name__ == "__main__":
    unittest.main()
