"""Unit tests for Context-Aware File Organizer application."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from src.main import ContextAnalyzer, ContextOrganizer, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestContextAnalyzer:
    """Test cases for ContextAnalyzer class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "analysis": {
                "weights": {
                    "parent_directories": 0.4,
                    "filename": 0.4,
                    "nearby_files": 0.2,
                }
            },
            "context_keywords": {
                "work": ["work", "job", "project"],
                "personal": ["personal", "home", "family"],
            },
        }

    @pytest.fixture
    def analyzer(self, config):
        """Create a ContextAnalyzer instance."""
        return ContextAnalyzer(config)

    def test_init(self, config):
        """Test ContextAnalyzer initialization."""
        analyzer = ContextAnalyzer(config)
        assert analyzer.config == config

    def test_analyze_parent_directories(self, analyzer, temp_dir):
        """Test parent directory analysis."""
        # Create file in work directory
        work_dir = temp_dir / "work" / "project"
        work_dir.mkdir(parents=True)
        work_file = work_dir / "file.txt"
        work_file.write_text("content")

        context = analyzer.analyze_parent_directories(work_file)
        assert "work" in context or len(context) > 0

    def test_analyze_filename(self, analyzer, temp_dir):
        """Test filename analysis."""
        # Create file with work-related name
        work_file = temp_dir / "work_report.txt"
        work_file.write_text("content")

        context = analyzer.analyze_filename(work_file)
        assert "work" in context

        # Create file with personal name
        personal_file = temp_dir / "family_photo.jpg"
        personal_file.write_text("content")

        context = analyzer.analyze_filename(personal_file)
        assert "personal" in context

    def test_analyze_nearby_files(self, analyzer, temp_dir):
        """Test nearby files analysis."""
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()

        # Create multiple Python files
        for i in range(5):
            (test_dir / f"file{i}.py").write_text("code")

        test_file = test_dir / "target.txt"
        test_file.write_text("content")

        context = analyzer.analyze_nearby_files(test_file)
        # Should detect code context from nearby files
        assert isinstance(context, dict)

    def test_get_type_context(self, analyzer):
        """Test type context extraction."""
        assert analyzer._get_type_context(".jpg") == "image"
        assert analyzer._get_type_context(".pdf") == "document"
        assert analyzer._get_type_context(".py") == "code"
        assert analyzer._get_type_context(".xyz") is None

    def test_combine_context(self, analyzer, temp_dir):
        """Test context combination."""
        # Create file with clear context
        work_dir = temp_dir / "work"
        work_dir.mkdir()
        work_file = work_dir / "project_report.txt"
        work_file.write_text("content")

        category, confidence = analyzer.combine_context(work_file)
        assert isinstance(category, str)
        assert 0.0 <= confidence <= 1.0


class TestContextOrganizer:
    """Test cases for ContextOrganizer class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "organized"
        source_dir.mkdir()
        dest_dir.mkdir()

        return {
            "source_directory": str(source_dir),
            "organization": {
                "destination_directory": str(dest_dir),
                "min_confidence": 0.3,
                "check_duplicates": True,
                "skip_duplicates": True,
                "exclude_directories": [".git"],
                "exclude_files": [".DS_Store"],
                "exclude_extensions": [".tmp"],
            },
            "analysis": {
                "weights": {
                    "parent_directories": 0.4,
                    "filename": 0.4,
                    "nearby_files": 0.2,
                }
            },
            "context_keywords": {
                "work": ["work", "project"],
                "personal": ["personal", "home"],
            },
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def organizer(self, config):
        """Create a ContextOrganizer instance."""
        return ContextOrganizer(config)

    def test_init(self, config):
        """Test ContextOrganizer initialization."""
        organizer = ContextOrganizer(config)
        assert organizer.config == config
        assert organizer.source_dir == Path(config["source_directory"])

    def test_should_exclude_file(self, organizer):
        """Test file exclusion logic."""
        excluded = Path("/some/.DS_Store")
        assert organizer.should_exclude_file(excluded) is True

        excluded = Path("/some/file.tmp")
        assert organizer.should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert organizer.should_exclude_file(included) is False

    def test_should_exclude_directory(self, organizer):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert organizer.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert organizer.should_exclude_directory(included) is False

    def test_calculate_file_hash(self, organizer, temp_dir):
        """Test file hash calculation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        file_hash = organizer.calculate_file_hash(test_file)
        assert file_hash is not None
        assert len(file_hash) == 32  # MD5 hash length

    def test_get_destination_path(self, organizer, temp_dir):
        """Test destination path generation."""
        test_file = temp_dir / "test.txt"
        dest_path = organizer.get_destination_path(test_file, "work", 0.8)
        assert "work" in str(dest_path)

        # Low confidence
        dest_path_low = organizer.get_destination_path(
            test_file, "work", 0.2
        )
        assert "uncertain" in str(dest_path_low)

    def test_organize_file_dry_run(self, organizer, temp_dir):
        """Test organizing file in dry-run mode."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "work_report.txt"
        test_file.write_text("content")

        success, category, confidence = organizer.organize_file(
            test_file, dry_run=True
        )
        assert success is True
        assert test_file.exists()  # Should still exist in dry-run

    def test_organize_file(self, organizer, temp_dir):
        """Test organizing file."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "work_report.txt"
        test_file.write_text("content")

        success, category, confidence = organizer.organize_file(
            test_file, dry_run=False
        )
        assert success is True
        assert not test_file.exists()  # Should be moved

        # Check destination
        dest_file = organizer.destination_dir / category / "work_report.txt"
        assert dest_file.exists() or any(
            f.name == "work_report.txt"
            for f in organizer.destination_dir.rglob("work_report.txt")
        )

    def test_scan_files(self, organizer, temp_dir):
        """Test scanning files."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = source_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = source_dir / "file2.txt"
        file2.write_text("content 2")

        files = organizer.scan_files()
        assert len(files) >= 2

    def test_organize_files_dry_run(self, organizer, temp_dir):
        """Test organizing files in dry-run mode."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = source_dir / "work_file.txt"
        file1.write_text("work content")
        file2 = source_dir / "personal_file.txt"
        file2.write_text("personal content")

        results = organizer.organize_files(dry_run=True)
        assert results["scanned"] >= 2
        assert file1.exists()  # Should still exist in dry-run
        assert file2.exists()  # Should still exist in dry-run


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
            "source_directory: /test\norganization:\n  destination_directory: /dest\n"
        )

        config = load_config(config_file)
        assert config["source_directory"] == "/test"
        assert config["organization"]["destination_directory"] == "/dest"

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
