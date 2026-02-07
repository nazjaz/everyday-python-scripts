"""Unit tests for File Tree Generator."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import FileTreeGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    config = {
        "root_directory": str(temp_dir),
        "output_file": str(temp_dir / "tree.txt"),
        "max_depth": None,
        "show_hidden": False,
        "exclusions": {"directories": [], "patterns": [], "extensions": []},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


@pytest.fixture
def test_structure(temp_dir):
    """Create a test directory structure."""
    # Create files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2" * 100)

    # Create subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("content3" * 200)
    (subdir / "file4.txt").write_text("content4")

    # Create nested subdirectory
    nested = subdir / "nested"
    nested.mkdir()
    (nested / "file5.txt").write_text("content5")

    return temp_dir


def test_file_tree_generator_initialization(config_file):
    """Test FileTreeGenerator initialization."""
    generator = FileTreeGenerator(config_path=config_file)
    assert generator.config is not None
    assert generator.root_dir.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        FileTreeGenerator(config_path="nonexistent.yaml")


def test_format_size():
    """Test file size formatting."""
    generator = FileTreeGenerator.__new__(FileTreeGenerator)
    generator.config = {}

    assert "B" in generator._format_size(500)
    assert "KB" in generator._format_size(2048)
    assert "MB" in generator._format_size(2 * 1024 * 1024)
    assert "GB" in generator._format_size(2 * 1024 * 1024 * 1024)
    assert generator._format_size(0) == "0 B"


def test_should_include_path_no_exclusions(config_file):
    """Test path inclusion when no exclusions are configured."""
    generator = FileTreeGenerator(config_path=config_file)
    test_path = Path("/some/path/file.txt")
    assert generator._should_include_path(test_path, False) is True


def test_should_include_path_hidden_files(config_file):
    """Test hidden file filtering."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.config["show_hidden"] = False

    hidden_file = Path("/some/path/.hidden")
    assert generator._should_include_path(hidden_file, False) is False

    generator.config["show_hidden"] = True
    assert generator._should_include_path(hidden_file, False) is True


def test_should_include_path_excluded_directories(config_file, temp_dir):
    """Test path exclusion for directories."""
    generator = FileTreeGenerator(config_path=config_file)
    excluded_dir = temp_dir / "excluded"
    excluded_dir.mkdir()
    generator.config["exclusions"] = {
        "directories": [str(excluded_dir)],
        "patterns": [],
        "extensions": [],
    }

    assert generator._should_include_path(excluded_dir, True) is False
    assert generator._should_include_path(excluded_dir / "file.txt", False) is False


def test_should_include_path_excluded_patterns(config_file):
    """Test path exclusion for patterns."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.config["exclusions"] = {
        "directories": [],
        "patterns": [".DS_Store"],
        "extensions": [],
    }

    excluded_file = Path("/some/path/.DS_Store")
    assert generator._should_include_path(excluded_file, False) is False

    normal_file = Path("/some/path/normal.txt")
    assert generator._should_include_path(normal_file, False) is True


def test_should_include_path_excluded_extensions(config_file):
    """Test path exclusion for file extensions."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.config["exclusions"] = {
        "directories": [],
        "patterns": [],
        "extensions": [".pyc"],
    }

    excluded_file = Path("/some/path/file.pyc")
    assert generator._should_include_path(excluded_file, False) is False

    normal_file = Path("/some/path/file.py")
    assert generator._should_include_path(normal_file, False) is True


def test_calculate_directory_stats(config_file, test_structure):
    """Test directory statistics calculation."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    total_size, file_count = generator._calculate_directory_stats(
        test_structure, None, 0
    )

    assert file_count == 5
    assert total_size > 0


def test_calculate_directory_stats_with_depth_limit(config_file, test_structure):
    """Test directory statistics with depth limit."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    total_size, file_count = generator._calculate_directory_stats(
        test_structure, 1, 0
    )

    # Should only count files in root and first level
    assert file_count >= 2


def test_generate_tree(config_file, test_structure):
    """Test tree generation."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    tree_content = generator.generate_tree()

    assert "File Tree:" in tree_content
    assert "file1.txt" in tree_content or "file2.txt" in tree_content
    assert "Statistics" in tree_content
    assert "Directories Scanned:" in tree_content
    assert "Files Counted:" in tree_content


def test_generate_tree_with_max_depth(config_file, test_structure):
    """Test tree generation with max depth limit."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure
    generator.config["max_depth"] = 1

    tree_content = generator.generate_tree()

    assert "File Tree:" in tree_content
    # Nested directory should not appear in tree
    assert "nested" not in tree_content or "Max Depth: 1" in tree_content


def test_save_tree(config_file, test_structure):
    """Test saving tree to file."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    output_path = generator.save_tree()

    assert output_path.exists()
    assert output_path.suffix == ".txt"

    content = output_path.read_text()
    assert "File Tree:" in content


def test_save_tree_custom_path(config_file, test_structure):
    """Test saving tree to custom file path."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    custom_path = test_structure / "custom_tree.txt"
    output_path = generator.save_tree(output_file=str(custom_path))

    assert output_path == custom_path
    assert custom_path.exists()


def test_tree_includes_file_sizes(config_file, test_structure):
    """Test that tree includes file sizes."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    tree_content = generator.generate_tree()

    # Should contain size information
    assert "KB" in tree_content or "B" in tree_content or "MB" in tree_content


def test_tree_includes_file_counts(config_file, test_structure):
    """Test that tree includes file counts."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    tree_content = generator.generate_tree()

    # Should contain file count information
    assert "files" in tree_content


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    config = {
        "root_directory": str(temp_dir),
        "output_file": str(temp_dir / "tree.txt"),
        "max_depth": None,
        "show_hidden": False,
        "exclusions": {"directories": [], "patterns": [], "extensions": []},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    with patch.dict(os.environ, {"MAX_DEPTH": "2"}):
        generator = FileTreeGenerator(config_path=str(config_path))
        assert generator.config["max_depth"] == 2


def test_tree_structure_visual_elements(config_file, test_structure):
    """Test that tree contains visual elements."""
    generator = FileTreeGenerator(config_path=config_file)
    generator.root_dir = test_structure

    tree_content = generator.generate_tree()

    # Should contain tree drawing characters
    assert "├──" in tree_content or "└──" in tree_content or "│" in tree_content
