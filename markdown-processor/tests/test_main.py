"""Unit tests for markdown processor."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    MarkdownProcessor,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "base_path": "./docs",
                "validate_external_links": True,
                "toc_placement": "after-first-header",
                "toc_min_depth": 2,
                "toc_max_depth": 4,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["base_path"] == "./docs"
            assert result["validate_external_links"] is True
            assert result["toc_placement"] == "after-first-header"
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


class TestMarkdownProcessor:
    """Test MarkdownProcessor class."""

    def test_init(self):
        """Test initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = MarkdownProcessor()
            assert processor.toc_placement == "top"
            assert processor.toc_min_depth == 2
            assert processor.toc_max_depth == 6

    def test_slugify(self):
        """Test text slugification."""
        processor = MarkdownProcessor()
        assert processor._slugify("Hello World") == "hello-world"
        assert processor._slugify("Test & Example") == "test-example"
        assert processor._slugify("  Spaces  ") == "spaces"

    def test_extract_headers(self):
        """Test header extraction."""
        processor = MarkdownProcessor()
        content = "# Header 1\n## Header 2\n### Header 3"
        headers = processor._extract_headers(content)

        assert len(headers) == 3
        assert headers[0] == (1, "Header 1", "header-1")
        assert headers[1] == (2, "Header 2", "header-2")
        assert headers[2] == (3, "Header 3", "header-3")

    def test_extract_links(self):
        """Test link extraction."""
        processor = MarkdownProcessor()
        content = "[Link Text](https://example.com) [Another](./file.md)"
        links = processor._extract_links(content)

        assert len(links) == 2
        assert links[0][0] == "Link Text"
        assert links[0][1] == "https://example.com"
        assert links[1][1] == "./file.md"

    def test_extract_references(self):
        """Test reference extraction."""
        processor = MarkdownProcessor()
        content = "[ref1]: https://example.com\n[ref2]: ./file.md"
        references = processor._extract_references(content)

        assert len(references) == 2
        assert references["ref1"] == "https://example.com"
        assert references["ref2"] == "./file.md"

    def test_classify_link(self):
        """Test link classification."""
        processor = MarkdownProcessor()
        assert processor._classify_link("https://example.com") == "external"
        assert processor._classify_link("http://example.com") == "external"
        assert processor._classify_link("#anchor") == "anchor"
        assert processor._classify_link("./file.md") == "internal"
        assert processor._classify_link("mailto:test@example.com") == "email"

    def test_validate_anchor_link(self):
        """Test anchor link validation."""
        processor = MarkdownProcessor()
        headers = [(2, "Section One", "section-one"), (2, "Section Two", "section-two")]

        assert processor._validate_anchor_link("#section-one", headers) is True
        assert processor._validate_anchor_link("#nonexistent", headers) is False
        assert processor._validate_anchor_link("#", headers) is True

    def test_generate_toc(self):
        """Test TOC generation."""
        processor = MarkdownProcessor(toc_min_depth=2, toc_max_depth=3)
        headers = [
            (1, "Title", "title"),
            (2, "Section One", "section-one"),
            (3, "Subsection", "subsection"),
            (2, "Section Two", "section-two"),
        ]

        toc = processor._generate_toc(headers)

        assert "Table of Contents" in toc
        assert "Section One" in toc
        assert "Section Two" in toc
        assert "Subsection" in toc
        assert "Title" not in toc

    def test_generate_toc_empty(self):
        """Test TOC generation with no headers."""
        processor = MarkdownProcessor()
        toc = processor._generate_toc([])
        assert toc == ""

    def test_process_file(self):
        """Test processing a markdown file."""
        processor = MarkdownProcessor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n\n[Link](./file.md)\n")
            file_path = Path(f.name)

        try:
            result = processor.process_file(file_path)

            assert result["file_path"] == str(file_path)
            assert len(result["headers"]) == 1
            assert len(result["links"]) == 1
        finally:
            file_path.unlink()

    def test_process_file_not_found(self):
        """Test processing non-existent file."""
        processor = MarkdownProcessor()
        file_path = Path("/nonexistent/file.md")

        with pytest.raises(FileNotFoundError):
            processor.process_file(file_path)

    def test_validate_internal_link(self):
        """Test internal link validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            file_path = base_path / "document.md"
            target_file = base_path / "target.md"
            target_file.write_text("content")

            processor = MarkdownProcessor(base_path=base_path)

            assert processor._validate_internal_link("target.md", file_path) is True
            assert processor._validate_internal_link("nonexistent.md", file_path) is False

    def test_insert_toc_top(self):
        """Test TOC insertion at top."""
        processor = MarkdownProcessor(toc_placement="top")
        content = "# Title\n\nContent here."
        toc = "## Table of Contents\n\n- [Title](#title)\n"

        result = processor._insert_toc(content, toc)

        assert result.startswith("## Table of Contents")
        assert "# Title" in result

    def test_insert_toc_after_first_header(self):
        """Test TOC insertion after first header."""
        processor = MarkdownProcessor(toc_placement="after-first-header")
        content = "# Title\n\nContent here."
        toc = "## Table of Contents\n\n- [Title](#title)\n"

        result = processor._insert_toc(content, toc)

        assert "# Title" in result
        assert "## Table of Contents" in result
        assert result.index("# Title") < result.index("## Table of Contents")

    def test_insert_toc_none(self):
        """Test TOC insertion disabled."""
        processor = MarkdownProcessor(toc_placement="none")
        content = "# Title\n\nContent here."
        toc = "## Table of Contents\n\n- [Title](#title)\n"

        result = processor._insert_toc(content, toc)

        assert result == content
        assert "Table of Contents" not in result

    @patch("src.main.REQUESTS_AVAILABLE", True)
    def test_validate_external_link(self):
        """Test external link validation."""
        processor = MarkdownProcessor()

        with patch("src.main.requests.head") as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            result = processor._validate_external_link("https://example.com")
            assert result is True

    @patch("src.main.REQUESTS_AVAILABLE", False)
    def test_validate_external_link_no_requests(self):
        """Test external link validation without requests library."""
        processor = MarkdownProcessor()
        result = processor._validate_external_link("https://example.com")
        assert result is None
