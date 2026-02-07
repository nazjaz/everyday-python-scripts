"""Unit tests for similar file finder module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import SimilarFileFinder


class TestSimilarFileFinder:
    """Test cases for SimilarFileFinder class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "similarity": {
                "algorithm": "sequence",
                "threshold": 0.8,
                "compare_by": "name",
            },
            "scan": {"skip_patterns": [".git", "__pycache__"]},
            "report": {"output_file": "report.txt"},
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def finder(self, config_file):
        """Create SimilarFileFinder instance."""
        return SimilarFileFinder(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "similarity": {"algorithm": "levenshtein", "threshold": 0.9},
            "scan": {"skip_patterns": []},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        finder = SimilarFileFinder(config_path=str(config_path))
        assert finder.config["similarity"]["algorithm"] == "levenshtein"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            SimilarFileFinder(config_path="nonexistent.yaml")

    def test_sequence_similarity_identical(self, finder):
        """Test sequence similarity for identical strings."""
        similarity = finder._sequence_similarity("test", "test")
        assert similarity == 1.0

    def test_sequence_similarity_similar(self, finder):
        """Test sequence similarity for similar strings."""
        similarity = finder._sequence_similarity("test", "test1")
        assert 0.0 < similarity < 1.0

    def test_sequence_similarity_different(self, finder):
        """Test sequence similarity for different strings."""
        similarity = finder._sequence_similarity("test", "xyz")
        assert similarity < 0.5

    def test_levenshtein_distance_identical(self, finder):
        """Test Levenshtein distance for identical strings."""
        distance = finder._levenshtein_distance("test", "test")
        assert distance == 0

    def test_levenshtein_distance_one_edit(self, finder):
        """Test Levenshtein distance for one edit."""
        distance = finder._levenshtein_distance("test", "test1")
        assert distance == 1

    def test_levenshtein_similarity(self, finder):
        """Test Levenshtein similarity calculation."""
        similarity = finder._levenshtein_similarity("test", "test")
        assert similarity == 1.0

        similarity = finder._levenshtein_similarity("test", "test1")
        assert 0.0 < similarity < 1.0

    def test_jaro_winkler_similarity_identical(self, finder):
        """Test Jaro-Winkler similarity for identical strings."""
        similarity = finder._jaro_winkler_similarity("test", "test")
        assert similarity == 1.0

    def test_jaro_winkler_similarity_similar(self, finder):
        """Test Jaro-Winkler similarity for similar strings."""
        similarity = finder._jaro_winkler_similarity("test", "test1")
        assert 0.0 < similarity < 1.0

    def test_calculate_similarity_sequence(self, finder):
        """Test similarity calculation with sequence algorithm."""
        similarity = finder._calculate_similarity("test", "test1", "sequence")
        assert 0.0 <= similarity <= 1.0

    def test_calculate_similarity_levenshtein(self, finder):
        """Test similarity calculation with Levenshtein algorithm."""
        similarity = finder._calculate_similarity("test", "test1", "levenshtein")
        assert 0.0 <= similarity <= 1.0

    def test_calculate_similarity_jaro_winkler(self, finder):
        """Test similarity calculation with Jaro-Winkler algorithm."""
        similarity = finder._calculate_similarity("test", "test1", "jaro_winkler")
        assert 0.0 <= similarity <= 1.0

    def test_calculate_similarity_unknown(self, finder):
        """Test similarity calculation with unknown algorithm."""
        similarity = finder._calculate_similarity("test", "test1", "unknown")
        assert 0.0 <= similarity <= 1.0

    def test_extract_filename_parts(self, finder, temp_dir):
        """Test filename parts extraction."""
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("content")

        parts = finder._extract_filename_parts(test_file)
        assert parts["name"] == "test_file"
        assert parts["extension"] == ".txt"
        assert parts["full_name"] == "test_file.txt"

    def test_should_skip_path(self, finder):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert finder._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert finder._should_skip_path(path) is False

    def test_scan_directory(self, finder, temp_dir):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content 1")
        (temp_dir / "file2.txt").write_text("content 2")
        (temp_dir / "similar_file.txt").write_text("content 3")

        finder.scan_directory(str(temp_dir))

        assert finder.stats["files_scanned"] == 3
        assert len(finder.files) == 3

    def test_scan_directory_not_found(self, finder):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            finder.scan_directory("/nonexistent/path")

    def test_scan_directory_not_a_directory(self, finder, temp_dir):
        """Test ValueError when path is not a directory."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            finder.scan_directory(str(test_file))

    def test_find_similar_files(self, finder, temp_dir):
        """Test finding similar files."""
        # Create files with similar names
        (temp_dir / "document.txt").write_text("content 1")
        (temp_dir / "document1.txt").write_text("content 2")
        (temp_dir / "document_final.txt").write_text("content 3")
        (temp_dir / "unrelated.txt").write_text("content 4")

        finder.scan_directory(str(temp_dir))
        finder.find_similar_files()

        assert finder.stats["similar_pairs_found"] > 0
        assert len(finder.similar_pairs) > 0

    def test_find_similar_files_no_matches(self, finder, temp_dir):
        """Test finding similar files with no matches."""
        # Create files with very different names
        (temp_dir / "abc.txt").write_text("content 1")
        (temp_dir / "xyz.txt").write_text("content 2")
        (temp_dir / "qwerty.txt").write_text("content 3")

        finder.config["similarity"]["threshold"] = 0.95
        finder.scan_directory(str(temp_dir))
        finder.find_similar_files()

        assert finder.stats["similar_pairs_found"] == 0

    def test_generate_report(self, finder, temp_dir):
        """Test report generation."""
        # Create files and find similarities
        (temp_dir / "file1.txt").write_text("content 1")
        (temp_dir / "file2.txt").write_text("content 2")

        finder.scan_directory(str(temp_dir))
        finder.find_similar_files()

        report_path = temp_dir / "test_report.txt"
        finder.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "SIMILAR FILES REPORT" in content
        assert "SUMMARY" in content
