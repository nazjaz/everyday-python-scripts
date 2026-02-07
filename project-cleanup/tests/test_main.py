"""Unit tests for Project Cleanup application."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import ProjectCleanup, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestProjectCleanup:
    """Test cases for ProjectCleanup class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        source_dir = temp_dir / "projects"
        archive_dir = temp_dir / "archive"
        source_dir.mkdir()
        archive_dir.mkdir()

        return {
            "source_directory": str(source_dir),
            "archive_directory": str(archive_dir),
            "actions": {
                "archive_after_days": 90,
                "remove_after_days": 365,
                "enable_removal": False,
            },
            "filtering": {
                "exclude_directories": [".git", "node_modules"],
                "exclude_files": [".DS_Store"],
                "project_indicators": ["README.md", "requirements.txt"],
            },
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def cleanup(self, config):
        """Create a ProjectCleanup instance."""
        return ProjectCleanup(config)

    def test_init(self, config):
        """Test ProjectCleanup initialization."""
        cleanup = ProjectCleanup(config)
        assert cleanup.config == config
        assert cleanup.source_dir == Path(config["source_directory"])
        assert cleanup.archive_dir == Path(config["archive_directory"])

    def test_get_project_last_modified(self, cleanup, temp_dir):
        """Test getting last modification time of a project."""
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()

        # Create a file in the project
        test_file = project_dir / "test.txt"
        test_file.write_text("test content")

        last_modified = cleanup.get_project_last_modified(project_dir)
        assert last_modified is not None
        assert isinstance(last_modified, datetime)

    def test_get_project_last_modified_nonexistent(self, cleanup):
        """Test getting modification time for nonexistent project."""
        nonexistent = Path("/nonexistent/path")
        result = cleanup.get_project_last_modified(nonexistent)
        assert result is None

    def test_get_project_last_modified_empty(self, cleanup, temp_dir):
        """Test getting modification time for empty project."""
        empty_dir = temp_dir / "empty_project"
        empty_dir.mkdir()

        result = cleanup.get_project_last_modified(empty_dir)
        # Should return directory modification time or None
        assert result is None or isinstance(result, datetime)

    def test_should_exclude_directory(self, cleanup):
        """Test directory exclusion logic."""
        excluded = Path("/some/path/.git")
        assert cleanup._should_exclude_directory(excluded) is True

        excluded = Path("/some/path/node_modules")
        assert cleanup._should_exclude_directory(excluded) is True

        included = Path("/some/path/normal_dir")
        assert cleanup._should_exclude_directory(included) is False

    def test_should_exclude_file(self, cleanup):
        """Test file exclusion logic."""
        excluded = Path("/some/file.DS_Store")
        assert cleanup._should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert cleanup._should_exclude_file(included) is False

    def test_is_project_inactive(self, cleanup, temp_dir):
        """Test inactivity detection."""
        project_dir = temp_dir / "old_project"
        project_dir.mkdir()

        # Create a file with old modification time
        old_file = project_dir / "old.txt"
        old_file.write_text("old content")

        # Set modification time to 100 days ago
        old_time = datetime.now() - timedelta(days=100)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        is_inactive, last_modified = cleanup.is_project_inactive(project_dir, 90)
        assert is_inactive is True
        assert last_modified is not None

    def test_is_project_inactive_recent(self, cleanup, temp_dir):
        """Test that recent projects are not marked inactive."""
        project_dir = temp_dir / "recent_project"
        project_dir.mkdir()

        recent_file = project_dir / "recent.txt"
        recent_file.write_text("recent content")

        is_inactive, last_modified = cleanup.is_project_inactive(project_dir, 90)
        assert is_inactive is False
        assert last_modified is not None

    def test_archive_project(self, cleanup, temp_dir):
        """Test archiving a project."""
        project_dir = temp_dir / "projects" / "test_project"
        project_dir.mkdir(parents=True)
        (project_dir / "README.md").write_text("# Test Project")

        result = cleanup.archive_project(project_dir)
        assert result is True
        assert not project_dir.exists()

        # Check that archive was created
        archive_files = list(cleanup.archive_dir.glob("test_project_*"))
        assert len(archive_files) > 0

    def test_archive_project_failure(self, cleanup, temp_dir):
        """Test archiving failure handling."""
        # Try to archive a nonexistent project
        nonexistent = Path("/nonexistent/project")
        result = cleanup.archive_project(nonexistent)
        assert result is False

    def test_remove_project(self, cleanup, temp_dir):
        """Test removing a project."""
        project_dir = temp_dir / "projects" / "test_project"
        project_dir.mkdir(parents=True)
        (project_dir / "README.md").write_text("# Test Project")

        result = cleanup.remove_project(project_dir)
        assert result is True
        assert not project_dir.exists()

    def test_remove_project_failure(self, cleanup):
        """Test removal failure handling."""
        nonexistent = Path("/nonexistent/project")
        result = cleanup.remove_project(nonexistent)
        assert result is False

    def test_scan_projects(self, cleanup, temp_dir):
        """Test scanning for projects."""
        projects_dir = Path(cleanup.source_dir)
        projects_dir.mkdir(parents=True, exist_ok=True)

        # Create a project with indicator
        project1 = projects_dir / "project1"
        project1.mkdir()
        (project1 / "README.md").write_text("# Project 1")

        # Create a non-project directory
        non_project = projects_dir / "not_a_project"
        non_project.mkdir()

        projects = cleanup.scan_projects()
        assert len(projects) >= 1
        assert any(p.name == "project1" for p in projects)

    def test_is_project_directory(self, cleanup, temp_dir):
        """Test project directory detection."""
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "README.md").write_text("# Test")

        assert cleanup._is_project_directory(project_dir) is True

        non_project = temp_dir / "not_project"
        non_project.mkdir()

        assert cleanup._is_project_directory(non_project) is False

    def test_process_projects_dry_run(self, cleanup, temp_dir):
        """Test processing projects in dry-run mode."""
        projects_dir = Path(cleanup.source_dir)
        projects_dir.mkdir(parents=True, exist_ok=True)

        # Create an old project
        old_project = projects_dir / "old_project"
        old_project.mkdir()
        (old_project / "README.md").write_text("# Old Project")
        old_file = old_project / "file.txt"
        old_file.write_text("content")

        # Set old modification time
        old_time = datetime.now() - timedelta(days=100)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        results = cleanup.process_projects(dry_run=True)
        assert results["scanned"] >= 1
        assert old_project.exists()  # Should still exist in dry-run

    def test_process_projects_archive(self, cleanup, temp_dir):
        """Test processing projects with archiving."""
        projects_dir = Path(cleanup.source_dir)
        projects_dir.mkdir(parents=True, exist_ok=True)

        # Create an old project
        old_project = projects_dir / "old_project"
        old_project.mkdir()
        (old_project / "README.md").write_text("# Old Project")
        old_file = old_project / "file.txt"
        old_file.write_text("content")

        # Set old modification time
        old_time = datetime.now() - timedelta(days=100)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        results = cleanup.process_projects(dry_run=False)
        assert results["scanned"] >= 1
        assert results["archived"] >= 1 or results["skipped"] >= 1


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
            "source_directory: /test\narchive_directory: /archive\n"
        )

        config = load_config(config_file)
        assert config["source_directory"] == "/test"
        assert config["archive_directory"] == "/archive"

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
