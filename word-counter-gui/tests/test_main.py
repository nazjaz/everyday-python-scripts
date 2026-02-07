"""Unit tests for word counter GUI."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    WordCounter,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "average_reading_speed": 200,
                "average_reading_speed_slow": 150,
                "average_reading_speed_fast": 250,
                "top_words_count": 10,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["average_reading_speed"] == 200
            assert result["average_reading_speed_slow"] == 150
            assert result["average_reading_speed_fast"] == 250
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


class TestWordCounter:
    """Test WordCounter class."""

    def test_init_empty(self):
        """Test initialization with empty text."""
        counter = WordCounter()
        assert counter.text == ""

    def test_init_with_text(self):
        """Test initialization with text."""
        counter = WordCounter("Hello world")
        assert counter.text == "Hello world"

    def test_analyze_empty_text(self):
        """Test analysis of empty text."""
        counter = WordCounter()
        result = counter.analyze()

        assert result["word_count"] == 0
        assert result["character_count"] == 0
        assert result["sentence_count"] == 0
        assert result["paragraph_count"] == 0

    def test_word_count(self):
        """Test word counting."""
        counter = WordCounter("Hello world test")
        result = counter.analyze()

        assert result["word_count"] == 3

    def test_character_count(self):
        """Test character counting."""
        counter = WordCounter("Hello world")
        result = counter.analyze()

        assert result["character_count"] == 11
        assert result["character_count_no_spaces"] == 10

    def test_sentence_count(self):
        """Test sentence counting."""
        counter = WordCounter("First sentence. Second sentence! Third sentence?")
        result = counter.analyze()

        assert result["sentence_count"] == 3

    def test_paragraph_count(self):
        """Test paragraph counting."""
        counter = WordCounter("First paragraph.\n\nSecond paragraph.")
        result = counter.analyze()

        assert result["paragraph_count"] == 2

    def test_word_frequency(self):
        """Test word frequency calculation."""
        counter = WordCounter("hello world hello test world")
        result = counter.analyze()

        frequency = result["word_frequency"]
        assert frequency["hello"] == 2
        assert frequency["world"] == 2
        assert frequency["test"] == 1

    def test_reading_time(self):
        """Test reading time calculation."""
        counter = WordCounter("word " * 200)
        result = counter.analyze()

        assert result["reading_time"] > 0
        assert result["reading_time_slow"] > result["reading_time"]
        assert result["reading_time_fast"] < result["reading_time"]

    def test_format_reading_time_seconds(self):
        """Test reading time formatting for seconds."""
        counter = WordCounter()
        result = counter.format_reading_time(0.5)
        assert "second" in result.lower()

    def test_format_reading_time_minutes(self):
        """Test reading time formatting for minutes."""
        counter = WordCounter()
        result = counter.format_reading_time(5.0)
        assert "minute" in result.lower()

    def test_format_reading_time_hours(self):
        """Test reading time formatting for hours."""
        counter = WordCounter()
        result = counter.format_reading_time(65.0)
        assert "hour" in result.lower()

    def test_extract_words(self):
        """Test word extraction."""
        counter = WordCounter("Hello, world! Test123")
        words = counter._extract_words()

        assert "hello" in words
        assert "world" in words
        assert "test123" in words
        assert len(words) == 3

    def test_calculate_word_frequency_top_n(self):
        """Test word frequency with top N limit."""
        counter = WordCounter("a b c d e f g h i j k l m n o")
        frequency = counter._calculate_word_frequency(top_n=5)

        assert len(frequency) <= 5

    def test_analyze_complex_text(self):
        """Test analysis of complex text."""
        text = """This is the first paragraph. It has multiple sentences!
        
        This is the second paragraph. It also has sentences."""
        
        counter = WordCounter(text)
        result = counter.analyze()

        assert result["word_count"] > 0
        assert result["sentence_count"] > 0
        assert result["paragraph_count"] == 2
        assert len(result["word_frequency"]) > 0
