"""Unit tests for text pattern search."""

import re
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    TextPatternSearch,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "use_regex": True,
                "case_sensitive": False,
                "context_lines": 5,
                "file_patterns": [".py", ".js"],
                "exclude_patterns": ["__pycache__"],
                "recursive": True,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["use_regex"] is True
            assert result["case_sensitive"] is False
            assert result["context_lines"] == 5
            assert result["file_patterns"] == [".py", ".js"]
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_config_invalid_yaml(self):
        """Test that invalid YAML raises YAMLError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(config_path)
        finally:
            config_path.unlink()


class TestTextPatternSearch:
    """Test TextPatternSearch class."""

    def test_init_literal_pattern(self):
        """Test initialization with literal pattern."""
        searcher = TextPatternSearch("test pattern")
        assert searcher.pattern == "test pattern"
        assert searcher.use_regex is False
        assert searcher.case_sensitive is True

    def test_init_regex_pattern(self):
        """Test initialization with regex pattern."""
        searcher = TextPatternSearch("test.*pattern", use_regex=True)
        assert searcher.pattern == "test.*pattern"
        assert searcher.use_regex is True

    def test_init_invalid_regex(self):
        """Test that invalid regex raises error."""
        with pytest.raises(re.error):
            TextPatternSearch("[invalid", use_regex=True)

    def test_init_case_insensitive(self):
        """Test case-insensitive initialization."""
        searcher = TextPatternSearch("test", case_sensitive=False)
        assert searcher.case_sensitive is False

    def test_is_text_file_by_extension(self):
        """Test text file detection by extension."""
        searcher = TextPatternSearch("test")
        assert searcher._is_text_file(Path("test.py")) is True
        assert searcher._is_text_file(Path("test.txt")) is True
        assert searcher._is_text_file(Path("test.js")) is True

    def test_is_text_file_with_patterns(self):
        """Test text file detection with custom patterns."""
        searcher = TextPatternSearch("test", file_patterns=[".py", ".custom"])
        assert searcher._is_text_file(Path("test.py")) is True
        assert searcher._is_text_file(Path("test.custom")) is True
        assert searcher._is_text_file(Path("test.txt")) is False

    def test_should_exclude_file(self):
        """Test file exclusion logic."""
        searcher = TextPatternSearch("test", exclude_patterns=["__pycache__", ".git"])
        assert searcher._should_exclude_file(Path("__pycache__/file.py")) is True
        assert searcher._should_exclude_file(Path(".git/config")) is True
        assert searcher._should_exclude_file(Path("normal.py")) is False

    def test_is_binary_file(self):
        """Test binary file detection."""
        searcher = TextPatternSearch("test")

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"text content\x00binary")
            binary_file = Path(f.name)

        try:
            assert searcher._is_binary_file(binary_file) is True
        finally:
            binary_file.unlink()

    def test_is_binary_file_text(self):
        """Test that text files are not detected as binary."""
        searcher = TextPatternSearch("test")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("text content")
            text_file = Path(f.name)

        try:
            assert searcher._is_binary_file(text_file) is False
        finally:
            text_file.unlink()

    def test_search_file_found(self):
        """Test searching a file with matches."""
        searcher = TextPatternSearch("test")

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line 1\n")
            f.write("line 2 with test pattern\n")
            f.write("line 3\n")
            test_file = Path(f.name)

        try:
            matches = searcher.search_file(test_file)
            assert len(matches) == 1
            assert matches[0][0] == 2
            assert "test pattern" in matches[0][1]
        finally:
            test_file.unlink()

    def test_search_file_not_found(self):
        """Test searching a file with no matches."""
        searcher = TextPatternSearch("nonexistent")

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line 1\n")
            f.write("line 2\n")
            test_file = Path(f.name)

        try:
            matches = searcher.search_file(test_file)
            assert len(matches) == 0
        finally:
            test_file.unlink()

    def test_search_file_case_insensitive(self):
        """Test case-insensitive search."""
        searcher = TextPatternSearch("TEST", case_sensitive=False)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line with test pattern\n")
            test_file = Path(f.name)

        try:
            matches = searcher.search_file(test_file)
            assert len(matches) == 1
        finally:
            test_file.unlink()

    def test_search_file_regex(self):
        """Test regex pattern search."""
        searcher = TextPatternSearch(r"\d+", use_regex=True)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line with 123 numbers\n")
            test_file = Path(f.name)

        try:
            matches = searcher.search_file(test_file)
            assert len(matches) == 1
        finally:
            test_file.unlink()

    def test_search_file_context(self):
        """Test context lines in search results."""
        searcher = TextPatternSearch("test", context_lines=1)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line 1\n")
            f.write("line 2\n")
            f.write("line 3 with test\n")
            f.write("line 4\n")
            f.write("line 5\n")
            test_file = Path(f.name)

        try:
            matches = searcher.search_file(test_file)
            assert len(matches) == 1
            context = matches[0][2]
            assert "line 2" in context
            assert "line 3 with test" in context
            assert "line 4" in context
        finally:
            test_file.unlink()

    def test_search_directory(self):
        """Test searching files in a directory."""
        searcher = TextPatternSearch("test")

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file1 = dir_path / "file1.txt"
            file1.write_text("line with test pattern\n")
            file2 = dir_path / "file2.txt"
            file2.write_text("line without match\n")

            results = searcher.search_directory(dir_path)

            assert len(results) == 1
            assert results[0][0] == file1

    def test_search_directory_recursive(self):
        """Test recursive directory search."""
        searcher = TextPatternSearch("test")

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            subdir = dir_path / "subdir"
            subdir.mkdir()
            file1 = dir_path / "file1.txt"
            file1.write_text("line with test\n")
            file2 = subdir / "file2.txt"
            file2.write_text("line with test\n")

            results = searcher.search_directory(dir_path, recursive=False)
            assert len(results) == 1

            results = searcher.search_directory(dir_path, recursive=True)
            assert len(results) == 2

    def test_format_results(self):
        """Test result formatting."""
        searcher = TextPatternSearch("test")

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line with test\n")
            test_file = Path(f.name)

        try:
            matches = searcher.search_file(test_file)
            results = [(test_file, matches)]
            formatted = searcher.format_results(results)

            assert "Search Results" in formatted
            assert str(test_file) in formatted
            assert "test" in formatted
        finally:
            test_file.unlink()

    def test_format_results_empty(self):
        """Test formatting empty results."""
        searcher = TextPatternSearch("test")
        formatted = searcher.format_results([])
        assert "No matches found" in formatted

    def test_search_paths_file(self):
        """Test searching a single file path."""
        searcher = TextPatternSearch("test")

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line with test\n")
            test_file = Path(f.name)

        try:
            results = searcher.search_paths([test_file])
            assert len(results) == 1
        finally:
            test_file.unlink()

    def test_search_paths_directory(self):
        """Test searching a directory path."""
        searcher = TextPatternSearch("test")

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file1 = dir_path / "file1.txt"
            file1.write_text("line with test\n")

            results = searcher.search_paths([dir_path])
            assert len(results) == 1
