"""Unit tests for File Summary Reporter application."""

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import (
    FileStatisticsCollector,
    RecommendationGenerator,
    ReportGenerator,
    TrendAnalyzer,
    load_config,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestFileStatisticsCollector:
    """Test cases for FileStatisticsCollector class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        return {
            "source_directory": str(source_dir),
            "filtering": {
                "exclude_directories": [".git"],
                "exclude_files": [".DS_Store"],
                "exclude_extensions": [".tmp"],
            },
            "analysis": {
                "top_files_limit": 20,
                "many_files_threshold": 10,
            },
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def collector(self, config):
        """Create a FileStatisticsCollector instance."""
        return FileStatisticsCollector(config)

    def test_init(self, config):
        """Test FileStatisticsCollector initialization."""
        collector = FileStatisticsCollector(config)
        assert collector.config == config
        assert collector.source_dir == Path(config["source_directory"])

    def test_should_exclude_file(self, collector):
        """Test file exclusion logic."""
        excluded = Path("/some/file.DS_Store")
        assert collector.should_exclude_file(excluded) is True

        excluded = Path("/some/file.tmp")
        assert collector.should_exclude_file(excluded) is True

        excluded = Path("/some/.hidden")
        assert collector.should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert collector.should_exclude_file(included) is False

    def test_should_exclude_directory(self, collector):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert collector.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert collector.should_exclude_directory(included) is False

    def test_categorize_file_type(self, collector):
        """Test file type categorization."""
        assert collector._categorize_file_type(".jpg") == "image"
        assert collector._categorize_file_type(".pdf") == "document"
        assert collector._categorize_file_type(".mp4") == "video"
        assert collector._categorize_file_type(".py") == "code"
        assert collector._categorize_file_type(".xyz") == "other"

    def test_categorize_size(self, collector):
        """Test size categorization."""
        assert collector._categorize_size(0) == "empty"
        assert collector._categorize_size(500) == "tiny (<1KB)"
        assert collector._categorize_size(500000) == "small (<1MB)"
        assert collector._categorize_size(5000000) == "medium (<10MB)"
        assert collector._categorize_size(50000000) == "large (<100MB)"
        assert collector._categorize_size(200000000) == "very_large (>100MB)"

    def test_categorize_age(self, collector):
        """Test age categorization."""
        assert collector._categorize_age(3) == "recent (0-7 days)"
        assert collector._categorize_age(20) == "active (8-30 days)"
        assert collector._categorize_age(60) == "moderate (31-90 days)"
        assert collector._categorize_age(200) == "old (91-365 days)"
        assert collector._categorize_age(400) == "very_old (>365 days)"

    def test_collect_file_statistics(self, collector, temp_dir):
        """Test collecting file statistics."""
        source_dir = Path(collector.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = source_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = source_dir / "file2.jpg"
        file2.write_text("content 2")

        stats = collector.collect_file_statistics()
        assert stats["total_files"] >= 2
        assert stats["total_size"] > 0
        assert "document" in stats["file_types"] or "other" in stats["file_types"]


class TestTrendAnalyzer:
    """Test cases for TrendAnalyzer class."""

    @pytest.fixture
    def stats(self):
        """Create sample statistics."""
        return {
            "total_files": 100,
            "total_size": 1024 * 1024 * 100,  # 100 MB
            "file_types": {"document": 50, "image": 30, "other": 20},
            "size_distribution": {"small (<1MB)": 80, "medium (<10MB)": 20},
            "age_distribution": {
                "recent (0-7 days)": 40,
                "old (91-365 days)": 60,
            },
            "empty_files": 5,
            "duplicate_extensions": [{"extension": ".txt", "count": 30}],
            "directory_structure": {0: 1, 1: 5, 2: 10},
        }

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {"analysis": {}}

    @pytest.fixture
    def analyzer(self, stats, config):
        """Create a TrendAnalyzer instance."""
        return TrendAnalyzer(stats, config)

    def test_analyze_trends(self, analyzer):
        """Test trend analysis."""
        trends = analyzer.analyze_trends()
        assert "file_distribution" in trends
        assert "size_trends" in trends
        assert "age_trends" in trends
        assert "growth_indicators" in trends
        assert "organization_opportunities" in trends

    def test_identify_opportunities(self, analyzer):
        """Test opportunity identification."""
        opportunities = analyzer._identify_opportunities()
        assert isinstance(opportunities, list)


class TestRecommendationGenerator:
    """Test cases for RecommendationGenerator class."""

    @pytest.fixture
    def stats(self):
        """Create sample statistics."""
        return {
            "total_files": 100,
            "total_size": 1024 * 1024 * 1024 * 15,  # 15 GB
            "file_types": {"document": 50, "image": 30},
            "size_distribution": {
                "small (<1MB)": 80,
                "very_large (>100MB)": 5,
            },
            "age_distribution": {
                "recent (0-7 days)": 40,
                "very_old (>365 days)": 60,
            },
            "empty_files": 10,
            "duplicate_extensions": [{"extension": ".txt", "count": 30}],
            "directory_structure": {0: 1, 1: 5},
        }

    @pytest.fixture
    def trends(self, stats):
        """Create sample trends."""
        return {
            "file_distribution": {
                "document": {"count": 50, "percentage": 50.0},
                "image": {"count": 30, "percentage": 30.0},
            },
            "size_trends": {"small (<1MB)": 80, "very_large (>100MB)": 5},
            "age_trends": {
                "recent (0-7 days)": 40,
                "very_old (>365 days)": 60,
            },
            "growth_indicators": {
                "total_files": 100,
                "total_size_gb": 15.0,
                "average_file_size_kb": 150.0,
                "empty_files_count": 10,
                "empty_files_percentage": 10.0,
            },
            "organization_opportunities": [],
        }

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {}

    @pytest.fixture
    def generator(self, stats, trends, config):
        """Create a RecommendationGenerator instance."""
        return RecommendationGenerator(stats, trends, config)

    def test_generate_recommendations(self, generator):
        """Test recommendation generation."""
        recommendations = generator.generate_recommendations()
        assert "cleanup" in recommendations
        assert "organization" in recommendations
        assert "optimization" in recommendations
        assert "priority" in recommendations
        assert recommendations["priority"] in ["low", "medium", "high"]


class TestReportGenerator:
    """Test cases for ReportGenerator class."""

    @pytest.fixture
    def stats(self):
        """Create sample statistics."""
        return {
            "total_files": 100,
            "total_directories": 10,
            "total_size": 1024 * 1024 * 1024,  # 1 GB
            "file_types": {"document": 50, "image": 30},
            "largest_files": [
                {"path": "large.txt", "size": 1000000, "modified": "2024-01-01"}
            ],
            "oldest_files": [
                {"path": "old.txt", "age_days": 500, "modified": "2022-01-01"}
            ],
            "recent_files": [],
            "empty_files": 5,
        }

    @pytest.fixture
    def trends(self):
        """Create sample trends."""
        return {
            "file_distribution": {
                "document": {"count": 50, "percentage": 50.0}
            },
            "size_trends": {"small (<1MB)": 80},
            "age_trends": {"recent (0-7 days)": 40},
            "growth_indicators": {
                "total_files": 100,
                "total_size_gb": 1.0,
            },
            "organization_opportunities": ["Test opportunity"],
        }

    @pytest.fixture
    def recommendations(self):
        """Create sample recommendations."""
        return {
            "cleanup": [
                {
                    "action": "Remove empty files",
                    "description": "Delete 5 empty files",
                    "impact": "low",
                    "effort": "low",
                }
            ],
            "organization": [],
            "optimization": [],
            "priority": "low",
        }

    @pytest.fixture
    def generator(self, stats, trends, recommendations):
        """Create a ReportGenerator instance."""
        return ReportGenerator(stats, trends, recommendations)

    def test_generate_text_report(self, generator):
        """Test text report generation."""
        report = generator.generate_text_report()
        assert isinstance(report, str)
        assert "FILE SUMMARY REPORT" in report
        assert "OVERVIEW" in report
        assert "RECOMMENDATIONS" in report

    def test_generate_json_report(self, generator):
        """Test JSON report generation."""
        report = generator.generate_json_report()
        assert isinstance(report, str)
        # Validate JSON
        data = json.loads(report)
        assert "generated" in data
        assert "statistics" in data
        assert "recommendations" in data


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
            "source_directory: /test\nfiltering:\n  exclude_directories: [.git]\n"
        )

        config = load_config(config_file)
        assert config["source_directory"] == "/test"
        assert ".git" in config["filtering"]["exclude_directories"]

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
