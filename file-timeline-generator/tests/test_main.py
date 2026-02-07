"""Unit tests for File Timeline Generator application."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import (
    FileTimeline,
    FileTimelineEvent,
    FileTimelineGenerator,
    TimelineAnalyzer,
    TimelineCollector,
    TimelineReporter,
    load_config,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestTimelineCollector:
    """Test cases for TimelineCollector class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "filtering": {
                "exclude_directories": [".git"],
                "exclude_files": [".DS_Store"],
                "exclude_extensions": [".tmp"],
            }
        }

    @pytest.fixture
    def collector(self, config):
        """Create a TimelineCollector instance."""
        return TimelineCollector(config)

    def test_init(self, config):
        """Test TimelineCollector initialization."""
        collector = TimelineCollector(config)
        assert collector.config == config

    def test_should_exclude_file(self, collector):
        """Test file exclusion logic."""
        excluded = Path("/some/.DS_Store")
        assert collector.should_exclude_file(excluded) is True

        excluded = Path("/some/file.tmp")
        assert collector.should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert collector.should_exclude_file(included) is False

    def test_should_exclude_directory(self, collector):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert collector.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert collector.should_exclude_directory(included) is False

    def test_collect_file_timeline(self, collector, temp_dir):
        """Test collecting file timeline."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        timeline = collector.collect_file_timeline(test_file)
        assert timeline is not None
        assert timeline.file_path == test_file
        assert timeline.created is not None
        assert timeline.modified is not None
        assert timeline.accessed is not None
        assert len(timeline.events) >= 3

    def test_collect_file_timeline_nonexistent(self, collector):
        """Test collecting timeline for nonexistent file."""
        nonexistent = Path("/nonexistent/file.txt")
        result = collector.collect_file_timeline(nonexistent)
        assert result is None

    def test_collect_timelines(self, collector, temp_dir):
        """Test collecting timelines for multiple files."""
        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = temp_dir / "file2.txt"
        file2.write_text("content 2")

        timelines = collector.collect_timelines(temp_dir)
        assert len(timelines) >= 2


class TestTimelineAnalyzer:
    """Test cases for TimelineAnalyzer class."""

    @pytest.fixture
    def timelines(self, temp_dir):
        """Create sample timelines."""
        timelines = []

        # Create files with different timestamps
        file1 = temp_dir / "file1.txt"
        file1.write_text("content 1")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(file1, (old_time, old_time))

        file2 = temp_dir / "file2.txt"
        file2.write_text("content 2")
        recent_time = (datetime.now() - timedelta(days=1)).timestamp()
        os.utime(file2, (recent_time, recent_time))

        # Create timelines
        collector = TimelineCollector({})
        timelines.append(collector.collect_file_timeline(file1))
        timelines.append(collector.collect_file_timeline(file2))

        return [t for t in timelines if t is not None]

    @pytest.fixture
    def analyzer(self, timelines):
        """Create a TimelineAnalyzer instance."""
        return TimelineAnalyzer(timelines)

    def test_init(self, timelines):
        """Test TimelineAnalyzer initialization."""
        analyzer = TimelineAnalyzer(timelines)
        assert analyzer.timelines == timelines

    def test_get_timeline_statistics(self, analyzer):
        """Test getting timeline statistics."""
        stats = analyzer.get_timeline_statistics()
        assert "total_files" in stats
        assert "total_events" in stats
        assert "earliest_event" in stats
        assert "latest_event" in stats

    def test_get_chronological_timeline(self, analyzer):
        """Test getting chronological timeline."""
        chronological = analyzer.get_chronological_timeline()
        assert isinstance(chronological, list)
        if chronological:
            # Check sorting
            for i in range(len(chronological) - 1):
                assert chronological[i].timestamp <= chronological[i + 1].timestamp

    def test_get_events_by_date(self, analyzer):
        """Test getting events grouped by date."""
        events_by_date = analyzer.get_events_by_date()
        assert isinstance(events_by_date, dict)
        for date_key, events in events_by_date.items():
            assert isinstance(date_key, str)
            assert isinstance(events, list)

    def test_get_project_evolution(self, analyzer):
        """Test getting project evolution."""
        evolution = analyzer.get_project_evolution()
        assert isinstance(evolution, list)
        if evolution:
            for snapshot in evolution:
                assert "date" in snapshot
                assert "created" in snapshot
                assert "modified" in snapshot
                assert "total_files" in snapshot


class TestTimelineReporter:
    """Test cases for TimelineReporter class."""

    @pytest.fixture
    def timelines(self, temp_dir):
        """Create sample timelines."""
        timelines = []
        file1 = temp_dir / "file1.txt"
        file1.write_text("content")
        collector = TimelineCollector({})
        timeline = collector.collect_file_timeline(file1)
        if timeline:
            timelines.append(timeline)
        return timelines

    @pytest.fixture
    def analyzer(self, timelines):
        """Create a TimelineAnalyzer instance."""
        return TimelineAnalyzer(timelines)

    @pytest.fixture
    def reporter(self, analyzer):
        """Create a TimelineReporter instance."""
        return TimelineReporter(analyzer)

    def test_init(self, analyzer):
        """Test TimelineReporter initialization."""
        reporter = TimelineReporter(analyzer)
        assert reporter.analyzer == analyzer

    def test_generate_text_report(self, reporter):
        """Test text report generation."""
        report = reporter.generate_text_report()
        assert isinstance(report, str)
        assert "FILE TIMELINE REPORT" in report

    def test_generate_json_report(self, reporter):
        """Test JSON report generation."""
        report = reporter.generate_json_report()
        assert isinstance(report, str)
        # Validate JSON
        import json
        data = json.loads(report)
        assert "generated" in data
        assert "statistics" in data

    def test_generate_csv_report(self, reporter):
        """Test CSV report generation."""
        report = reporter.generate_csv_report()
        assert isinstance(report, str)
        assert "Timestamp" in report
        assert "Type" in report


class TestFileTimelineGenerator:
    """Test cases for FileTimelineGenerator class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        return {
            "search": {"directory": str(temp_dir)},
            "filtering": {"exclude_directories": [".git"]},
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def generator(self, config):
        """Create a FileTimelineGenerator instance."""
        return FileTimelineGenerator(config)

    def test_init(self, config):
        """Test FileTimelineGenerator initialization."""
        generator = FileTimelineGenerator(config)
        assert generator.config == config

    def test_generate_timeline(self, generator, temp_dir):
        """Test timeline generation."""
        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = temp_dir / "file2.txt"
        file2.write_text("content 2")

        timelines = generator.generate_timeline(temp_dir)
        assert len(timelines) >= 2


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "search:\n  directory: /test\noutput:\n  format: json\n"
        )

        config = load_config(config_file)
        assert config["search"]["directory"] == "/test"
        assert config["output"]["format"] == "json"

    def test_load_config_nonexistent(self):
        """Test loading a nonexistent configuration file."""
        nonexistent = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(Exception):  # yaml.YAMLError
            load_config(config_file)
