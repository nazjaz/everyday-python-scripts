"""Unit tests for Duplicate Structure Finder application."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from src.main import (
    DirectoryStructure,
    DuplicateStructureFinder,
    StructureAnalyzer,
    load_config,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestStructureAnalyzer:
    """Test cases for StructureAnalyzer class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "analysis": {"max_depth": 0, "include_sizes": True},
            "filtering": {
                "exclude_directories": [".git"],
                "exclude_files": [".DS_Store"],
                "exclude_extensions": [".tmp"],
            },
        }

    @pytest.fixture
    def analyzer(self, config):
        """Create a StructureAnalyzer instance."""
        return StructureAnalyzer(config)

    def test_init(self, config):
        """Test StructureAnalyzer initialization."""
        analyzer = StructureAnalyzer(config)
        assert analyzer.config == config

    def test_should_exclude_directory(self, analyzer):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert analyzer.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert analyzer.should_exclude_directory(included) is False

    def test_should_exclude_file(self, analyzer):
        """Test file exclusion logic."""
        excluded = Path("/some/.DS_Store")
        assert analyzer.should_exclude_file(excluded) is True

        excluded = Path("/some/file.tmp")
        assert analyzer.should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert analyzer.should_exclude_file(included) is False

    def test_analyze_directory_structure(self, analyzer, temp_dir):
        """Test directory structure analysis."""
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()

        # Create files and subdirectories
        (test_dir / "file1.txt").write_text("content")
        (test_dir / "file2.txt").write_text("content")
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content")

        structure = analyzer.analyze_directory_structure(test_dir)

        assert structure.path == test_dir
        assert structure.file_count >= 2
        assert structure.subdirectory_count >= 1
        assert ".txt" in structure.file_extensions
        assert "subdir" in structure.subdirectory_names
        assert structure.structure_hash != ""

    def test_calculate_structure_hash(self, analyzer):
        """Test structure hash calculation."""
        structure1 = DirectoryStructure(
            path=Path("/test1"),
            depth=1,
            file_count=5,
            subdirectory_count=2,
            file_extensions={".txt", ".pdf"},
            subdirectory_names={"dir1", "dir2"},
        )

        structure2 = DirectoryStructure(
            path=Path("/test2"),
            depth=1,
            file_count=5,
            subdirectory_count=2,
            file_extensions={".txt", ".pdf"},
            subdirectory_names={"dir1", "dir2"},
        )

        hash1 = analyzer._calculate_structure_hash(structure1)
        hash2 = analyzer._calculate_structure_hash(structure2)

        assert hash1 == hash2  # Same structure should have same hash

    def test_calculate_similarity(self, analyzer):
        """Test similarity calculation."""
        structure1 = DirectoryStructure(
            path=Path("/test1"),
            depth=1,
            file_count=10,
            subdirectory_count=2,
            file_extensions={".txt", ".pdf"},
            subdirectory_names={"dir1", "dir2"},
        )

        structure2 = DirectoryStructure(
            path=Path("/test2"),
            depth=1,
            file_count=10,
            subdirectory_count=2,
            file_extensions={".txt", ".pdf"},
            subdirectory_names={"dir1", "dir2"},
        )

        similarity = analyzer.calculate_similarity(structure1, structure2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.8  # Should be very similar

        # Different structures
        structure3 = DirectoryStructure(
            path=Path("/test3"),
            depth=2,
            file_count=5,
            subdirectory_count=1,
            file_extensions={".jpg"},
            subdirectory_names={"other"},
        )

        similarity2 = analyzer.calculate_similarity(structure1, structure3)
        assert similarity2 < similarity  # Should be less similar


class TestDuplicateStructureFinder:
    """Test cases for DuplicateStructureFinder class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        return {
            "search": {"directory": str(temp_dir), "include_root": False},
            "comparison": {"similarity_threshold": 0.8},
            "analysis": {},
            "filtering": {"exclude_directories": [".git"]},
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def finder(self, config):
        """Create a DuplicateStructureFinder instance."""
        return DuplicateStructureFinder(config)

    def test_init(self, config):
        """Test DuplicateStructureFinder initialization."""
        finder = DuplicateStructureFinder(config)
        assert finder.config == config

    def test_find_directories(self, finder, temp_dir):
        """Test finding directories."""
        # Create test directories
        dir1 = temp_dir / "dir1"
        dir2 = temp_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "file1.txt").write_text("content")
        (dir2 / "file2.txt").write_text("content")

        directories = finder.find_directories(temp_dir)
        assert len(directories) >= 2

    def test_find_duplicate_structures(self, finder, temp_dir):
        """Test finding duplicate structures."""
        # Create similar directory structures
        dir1 = temp_dir / "project_backup_2023"
        dir2 = temp_dir / "project_backup_2024"
        dir1.mkdir()
        dir2.mkdir()

        # Create similar structure
        for dir_path in [dir1, dir2]:
            (dir_path / "file1.txt").write_text("content")
            (dir_path / "file2.pdf").write_text("content")
            subdir = dir_path / "src"
            subdir.mkdir()
            (subdir / "main.py").write_text("code")

        duplicates = finder.find_duplicate_structures(temp_dir)
        assert len(duplicates) >= 1

    def test_generate_report(self, finder):
        """Test report generation."""
        structure1 = DirectoryStructure(
            path=Path("/test1"),
            depth=1,
            file_count=5,
            subdirectory_count=2,
            file_extensions={".txt"},
            subdirectory_names={"dir1"},
            total_size=1000,
        )

        structure2 = DirectoryStructure(
            path=Path("/test2"),
            depth=1,
            file_count=5,
            subdirectory_count=2,
            file_extensions={".txt"},
            subdirectory_names={"dir1"},
            total_size=1200,
        )

        duplicates = [(structure1, structure2, 0.95)]
        report = finder.generate_report(duplicates)

        assert "Duplicate Directory Structure Report" in report
        assert "test1" in report
        assert "test2" in report

    def test_format_size(self, finder):
        """Test size formatting."""
        assert "B" in finder._format_size(100)
        assert "KB" in finder._format_size(1024)
        assert "MB" in finder._format_size(1024 * 1024)


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
            "search:\n  directory: /test\ncomparison:\n  similarity_threshold: 0.8\n"
        )

        config = load_config(config_file)
        assert config["search"]["directory"] == "/test"
        assert config["comparison"]["similarity_threshold"] == 0.8

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
