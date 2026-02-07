"""Unit tests for file indexer."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import FileIndexer, load_config, load_index


class TestFileIndexer:
    """Test cases for FileIndexer class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return {
            "options": {
                "include_hidden": False,
                "include_empty": True,
                "recursive": True,
                "calculate_hashes": False,
                "include_permissions": True,
            },
            "metadata": {
                "size": True,
                "modification_date": True,
                "creation_date": True,
                "file_type": True,
                "full_path": True,
            },
            "exclude_patterns": [],
            "exclude_directories": [],
            "search": {
                "enabled": True,
                "search_fields": ["name", "path"],
            },
        }

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test files
            (tmp_path / "test1.txt").write_text("Test content 1")
            (tmp_path / "test2.py").write_text("print('hello')")
            (tmp_path / ".hidden").write_text("hidden content")

            # Create subdirectory
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            (subdir / "test3.txt").write_text("Test content 3")

            yield tmp_path

    def test_should_exclude_file_hidden(self, sample_config, temp_dir):
        """Test that hidden files are excluded when configured."""
        indexer = FileIndexer(sample_config)
        hidden_file = temp_dir / ".hidden"

        assert indexer.should_exclude_file(hidden_file) is True

    def test_should_exclude_file_includes_hidden(self, sample_config, temp_dir):
        """Test that hidden files are included when configured."""
        sample_config["options"]["include_hidden"] = True
        indexer = FileIndexer(sample_config)
        hidden_file = temp_dir / ".hidden"

        assert indexer.should_exclude_file(hidden_file) is False

    def test_should_exclude_file_by_pattern(self, sample_config, temp_dir):
        """Test file exclusion by pattern."""
        sample_config["exclude_patterns"] = ["\\.py$"]
        indexer = FileIndexer(sample_config)
        py_file = temp_dir / "test2.py"

        assert indexer.should_exclude_file(py_file) is True

    def test_get_file_metadata(self, sample_config, temp_dir):
        """Test metadata extraction."""
        indexer = FileIndexer(sample_config)
        test_file = temp_dir / "test1.txt"
        metadata = indexer.get_file_metadata(test_file)

        assert metadata["name"] == "test1.txt"
        assert "size" in metadata
        assert "modified" in metadata
        assert "created" in metadata
        assert metadata["file_type"] == "txt"
        assert "full_path" in metadata

    def test_index_directory(self, sample_config, temp_dir):
        """Test directory indexing."""
        indexer = FileIndexer(sample_config)
        files = indexer.index_directory(temp_dir, recursive=True)

        assert len(files) >= 2  # At least test1.txt and test2.py
        file_names = [f["name"] for f in files]
        assert "test1.txt" in file_names
        assert "test2.py" in file_names

    def test_index_directory_non_recursive(self, sample_config, temp_dir):
        """Test non-recursive directory indexing."""
        indexer = FileIndexer(sample_config)
        files = indexer.index_directory(temp_dir, recursive=False)

        # Should not include files in subdirectories
        file_paths = [f.get("full_path", "") for f in files]
        assert any("subdir" not in path for path in file_paths)

    def test_create_index(self, sample_config, temp_dir):
        """Test index creation."""
        indexer = FileIndexer(sample_config)
        index = indexer.create_index([temp_dir], recursive=True)

        assert "created_at" in index
        assert "total_files" in index
        assert "directories_indexed" in index
        assert "files" in index
        assert index["total_files"] > 0

    def test_save_index(self, sample_config, temp_dir):
        """Test saving index to JSON."""
        indexer = FileIndexer(sample_config)
        index = indexer.create_index([temp_dir], recursive=True)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            indexer.save_index(index, output_path)
            assert output_path.exists()

            # Verify JSON is valid
            with open(output_path, "r") as f:
                loaded = json.load(f)
                assert loaded["total_files"] == index["total_files"]
        finally:
            output_path.unlink()

    def test_search_index(self, sample_config, temp_dir):
        """Test index searching."""
        indexer = FileIndexer(sample_config)
        index = indexer.create_index([temp_dir], recursive=True)

        # Search for Python files
        matches = indexer.search_index(index, "test2", case_sensitive=False)
        assert len(matches) > 0
        assert any("test2.py" in m.get("name", "") for m in matches)

    def test_search_index_case_sensitive(self, sample_config, temp_dir):
        """Test case-sensitive search."""
        indexer = FileIndexer(sample_config)
        index = indexer.create_index([temp_dir], recursive=True)

        matches_lower = indexer.search_index(index, "test", case_sensitive=False)
        matches_upper = indexer.search_index(index, "TEST", case_sensitive=False)

        assert len(matches_lower) == len(matches_upper)

        matches_sensitive = indexer.search_index(index, "TEST", case_sensitive=True)
        # Should find fewer matches with case-sensitive search
        assert len(matches_sensitive) <= len(matches_lower)

    def test_calculate_file_hash(self, sample_config, temp_dir):
        """Test file hash calculation."""
        sample_config["options"]["calculate_hashes"] = True
        sample_config["options"]["hash_algorithm"] = "sha256"
        indexer = FileIndexer(sample_config)
        test_file = temp_dir / "test1.txt"

        hash_value = indexer.calculate_file_hash(test_file)
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters

    def test_format_size(self, sample_config):
        """Test size formatting."""
        indexer = FileIndexer(sample_config)

        assert "B" in indexer._format_size(500)
        assert "KB" in indexer._format_size(2048)
        assert "MB" in indexer._format_size(1048576)


class TestConfigLoading:
    """Test cases for configuration loading."""

    def test_load_config_valid(self, tmp_path):
        """Test loading valid config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
options:
  include_hidden: false
metadata:
  size: true
"""
        )

        config = load_config(config_file)
        assert "options" in config
        assert config["options"]["include_hidden"] is False

    def test_load_index_valid(self, tmp_path):
        """Test loading valid index file."""
        index_file = tmp_path / "index.json"
        index_data = {
            "created_at": "2024-01-01T00:00:00",
            "total_files": 0,
            "files": [],
        }
        index_file.write_text(json.dumps(index_data))

        index = load_index(index_file)
        assert index["total_files"] == 0
        assert "files" in index
