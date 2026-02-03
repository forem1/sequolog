# Sequolog

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)

Python library for event sequence analysis and timeline reconstruction, aimed at incident analysis, forensics, and any setting where multiple event streams are brought into one or more timelines. 

Timelines need not be coherent or overlapping: a project can hold disjoint timelines, and analytics work per timeline or across the project. Define projects with timelines and events, attach time information, then use analytics for ordering, range queries, intervals and gaps, bounds, clustering, pattern detection and validation. Relative times resolve against reference events.

**Model:**
- **Project** — top-level container; holds timelines and sources.
- **Timeline** — ordered sequence of events.
- **Event** — single item in a timeline; has a source, description, and a time object.
- **Source** — origin of events (log, report, etc.).
- **Time (per event):**
  - **ExactTime** — single point in time (timestamp or calendar fields).
  - **RangeTime** — interval with start and/or end.
  - **RelativeTime** — offset in milliseconds from another event by ID.
  - **NoTime** — time unknown or not applicable.
  Any time type can carry an optional **sequence** number; analytics use it for ordering when time is absent or to disambiguate.

**Partial dates:** Calendar-based time (ExactTime, RangeTime start/end) does not require a full date. Any subset of year, month, day, hour, minute, second, millisecond can be set; the rest stay unspecified. Examples: only year; year and month without day; month without day or year (e.g. “March”); or a full datetime. Analytics that need a single timestamp use defaults for missing parts where applicable (e.g. for bounds or sorting).

**Uncertainty:** Any time type except NoTime can carry an optional uncertainty (a time range or bound around the main value). Analytics can expand uncertainty and compute confidence windows.

**Analytics**:
- **Sorting and filtering** — events ordered by time or by sequence; queries for events in a range, before/after a point, or at a time (with tolerance).
- **Intervals and bounds** — gaps between consecutive events, longest gap, average interval; start/end and duration for a timeline or the whole project.
- **Grouping and patterns** — events by period (day, week, month, year), clusters by proximity, density in a sliding window; detection of regular intervals and temporal anomalies.
- **Validation and statistics** — consistency of sequence vs time order, temporal coverage by source or timeline, basic time statistics.
- **Uncertainty and relative time** — expansion of uncertainty into min/max bounds, confidence windows; resolution of relative times against reference events, chains and circular dependency handling.
- **Timeline comparison** — common events, temporal overlap, alignment of multiple timelines.

**Serialization:** JSON is the main supported format (load/save project, to/from string); the model is built so other containers or formats can be added.
