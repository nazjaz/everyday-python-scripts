"""Unit tests for dependency graph analyzer."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    DependencyGraphAnalyzer,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "base_path": "./src",
                "recursive": True,
                "follow_external": False,
                "max_depth": 10,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["base_path"] == "./src"
            assert result["recursive"] is True
            assert result["follow_external"] is False
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


class TestDependencyGraphAnalyzer:
    """Test DependencyGraphAnalyzer class."""

    def test_init(self):
        """Test initialization."""
        analyzer = DependencyGraphAnalyzer()
        assert analyzer.base_path is None
        assert analyzer.follow_external is False
        assert analyzer.max_depth is None

    def test_get_file_type(self):
        """Test file type detection."""
        analyzer = DependencyGraphAnalyzer()

        assert analyzer._get_file_type(Path("test.py")) == "python"
        assert analyzer._get_file_type(Path("test.js")) == "javascript"
        assert analyzer._get_file_type(Path("test.ts")) == "typescript"
        assert analyzer._get_file_type(Path("test.txt")) is None

    def test_extract_python_imports(self):
        """Test Python import extraction."""
        analyzer = DependencyGraphAnalyzer()
        content = "import os\nfrom sys import path\nimport json"
        imports = analyzer._extract_python_imports(content)

        assert "os" in imports
        assert "sys" in imports
        assert "json" in imports

    def test_extract_javascript_imports(self):
        """Test JavaScript import extraction."""
        analyzer = DependencyGraphAnalyzer()
        content = "import React from 'react'\nconst fs = require('fs')"
        imports = analyzer._extract_javascript_imports(content)

        assert "react" in imports
        assert "fs" in imports

    def test_extract_imports_python(self):
        """Test import extraction for Python file."""
        analyzer = DependencyGraphAnalyzer()
        file_path = Path("test.py")
        content = "import os\nfrom sys import path"

        imports = analyzer._extract_imports(file_path, content)
        assert "os" in imports
        assert "sys" in imports

    def test_extract_imports_javascript(self):
        """Test import extraction for JavaScript file."""
        analyzer = DependencyGraphAnalyzer()
        file_path = Path("test.js")
        content = "import React from 'react'"

        imports = analyzer._extract_imports(file_path, content)
        assert "react" in imports

    def test_is_external_dependency(self):
        """Test external dependency detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            analyzer = DependencyGraphAnalyzer(base_path=base_path)

            assert analyzer._is_external_dependency("os") is True
            assert analyzer._is_external_dependency("sys") is True

            module_dir = base_path / "local_module"
            module_dir.mkdir()
            assert analyzer._is_external_dependency("local_module") is False

    def test_analyze_file(self):
        """Test file analysis."""
        analyzer = DependencyGraphAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nimport sys")
            file_path = Path(f.name)

        try:
            dependencies = analyzer.analyze_file(file_path)
            assert isinstance(dependencies, set)
        finally:
            file_path.unlink()

    def test_analyze_file_not_found(self):
        """Test analysis of non-existent file."""
        analyzer = DependencyGraphAnalyzer()
        file_path = Path("/nonexistent/file.py")

        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file(file_path)

    def test_analyze_files(self):
        """Test analyzing multiple files."""
        analyzer = DependencyGraphAnalyzer()

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file1 = dir_path / "file1.py"
            file1.write_text("import os")
            file2 = dir_path / "file2.py"
            file2.write_text("import sys")

            graph = analyzer.analyze_files([dir_path])

            assert isinstance(graph, dict)
            assert len(graph) >= 2

    def test_analyze_files_recursive(self):
        """Test recursive file analysis."""
        analyzer = DependencyGraphAnalyzer()

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            subdir = dir_path / "subdir"
            subdir.mkdir()
            file1 = dir_path / "file1.py"
            file1.write_text("import os")
            file2 = subdir / "file2.py"
            file2.write_text("import sys")

            graph = analyzer.analyze_files([dir_path], recursive=True)

            assert len(graph) >= 2

    def test_get_reverse_dependencies(self):
        """Test reverse dependency graph."""
        analyzer = DependencyGraphAnalyzer()

        analyzer.graph["file1.py"] = {"file2.py", "file3.py"}
        analyzer.graph["file2.py"] = set()

        reverse_graph = analyzer.get_reverse_dependencies()

        assert "file2.py" in reverse_graph
        assert "file1.py" in reverse_graph["file2.py"]

    def test_format_graph_text(self):
        """Test text graph formatting."""
        analyzer = DependencyGraphAnalyzer()
        analyzer.graph["file1.py"] = {"file2.py"}

        text = analyzer.format_graph_text()

        assert "Dependency Graph Analysis" in text
        assert "file1.py" in text
        assert "file2.py" in text

    def test_format_graph_json(self):
        """Test JSON graph formatting."""
        analyzer = DependencyGraphAnalyzer()
        analyzer.graph["file1.py"] = {"file2.py"}

        json_str = analyzer.format_graph_json()
        data = json.loads(json_str)

        assert "graph" in data
        assert "stats" in data
        assert "reverse_graph" in data

    def test_format_graph_dot(self):
        """Test DOT graph formatting."""
        analyzer = DependencyGraphAnalyzer()
        analyzer.graph["file1.py"] = {"file2.py"}

        dot_str = analyzer.format_graph_dot()

        assert "digraph dependencies" in dot_str
        assert "file1" in dot_str
        assert "file2" in dot_str

    def test_sanitize_node_id(self):
        """Test node ID sanitization."""
        analyzer = DependencyGraphAnalyzer()

        node_id = analyzer._sanitize_node_id("/path/to/file.py")
        assert "/" not in node_id
        assert "." not in node_id
