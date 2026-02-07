"""Unit tests for calculator GUI."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import CalculatorEngine


@pytest.fixture
def engine():
    """Create CalculatorEngine instance for testing."""
    return CalculatorEngine()


class TestCalculatorEngine:
    """Test cases for CalculatorEngine class."""

    def test_init(self, engine):
        """Test engine initialization."""
        assert engine.memory == 0.0
        assert engine.current_value == "0"
        assert engine.previous_value is None
        assert engine.operation is None
        assert engine.history == []

    def test_input_digit(self, engine):
        """Test digit input."""
        result = engine.input_digit("5")
        assert result == "5"
        assert engine.current_value == "5"

        result = engine.input_digit("3")
        assert result == "53"
        assert engine.current_value == "53"

    def test_input_digit_zero(self, engine):
        """Test inputting zero."""
        result = engine.input_digit("0")
        assert result == "0"
        
        result = engine.input_digit("5")
        assert result == "5"

    def test_input_decimal(self, engine):
        """Test decimal point input."""
        engine.input_digit("5")
        result = engine.input_decimal()
        assert result == "5."
        assert "." in engine.current_value

    def test_input_decimal_duplicate(self, engine):
        """Test duplicate decimal point input."""
        engine.input_digit("5")
        engine.input_decimal()
        result = engine.input_decimal()
        assert result == "5."  # Should not add another decimal

    def test_clear(self, engine):
        """Test clear function."""
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        
        result = engine.clear()
        assert result == "0"
        assert engine.current_value == "0"
        assert engine.previous_value is None
        assert engine.operation is None

    def test_clear_entry(self, engine):
        """Test clear entry function."""
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        
        result = engine.clear_entry()
        assert result == "0"
        assert engine.current_value == "0"
        assert engine.previous_value == 5.0  # Previous value preserved
        assert engine.operation == "+"  # Operation preserved

    def test_set_operation(self, engine):
        """Test setting operation."""
        engine.input_digit("5")
        result = engine.set_operation("+")
        
        assert result == "0"
        assert engine.previous_value == 5.0
        assert engine.operation == "+"
        assert engine.current_value == "0"

    def test_set_operation_chain(self, engine):
        """Test chaining operations."""
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        engine.set_operation("*")
        
        # Should calculate 5 + 3 = 8, then set up for multiplication
        assert engine.previous_value == 8.0
        assert engine.operation == "*"

    def test_calculate_addition(self, engine):
        """Test addition calculation."""
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        
        result = engine.calculate()
        assert result == "8.0"
        assert engine.previous_value is None
        assert engine.operation is None

    def test_calculate_subtraction(self, engine):
        """Test subtraction calculation."""
        engine.input_digit("10")
        engine.set_operation("-")
        engine.input_digit("3")
        
        result = engine.calculate()
        assert result == "7.0"

    def test_calculate_multiplication(self, engine):
        """Test multiplication calculation."""
        engine.input_digit("5")
        engine.set_operation("*")
        engine.input_digit("4")
        
        result = engine.calculate()
        assert result == "20.0"

    def test_calculate_division(self, engine):
        """Test division calculation."""
        engine.input_digit("10")
        engine.set_operation("/")
        engine.input_digit("2")
        
        result = engine.calculate()
        assert result == "5.0"

    def test_calculate_division_by_zero(self, engine):
        """Test division by zero."""
        engine.input_digit("10")
        engine.set_operation("/")
        engine.input_digit("0")
        
        result = engine.calculate()
        assert result is None

    def test_calculate_decimal(self, engine):
        """Test calculation with decimal numbers."""
        engine.input_digit("5")
        engine.input_decimal()
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("2")
        engine.input_decimal()
        engine.input_digit("5")
        
        result = engine.calculate()
        assert result == "8.0"

    def test_calculate_no_operation(self, engine):
        """Test calculation without operation."""
        engine.input_digit("5")
        result = engine.calculate()
        assert result == "5"

    def test_calculate_adds_to_history(self, engine):
        """Test that calculations are added to history."""
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        engine.calculate()
        
        assert len(engine.history) == 1
        assert engine.history[0]["expression"] == "5.0 + 3.0"
        assert engine.history[0]["result"] == "8.0"
        assert "timestamp" in engine.history[0]

    def test_memory_add(self, engine):
        """Test memory add function."""
        engine.input_digit("5")
        engine.memory_add()
        assert engine.memory == 5.0
        
        engine.clear()
        engine.input_digit("3")
        engine.memory_add()
        assert engine.memory == 8.0

    def test_memory_subtract(self, engine):
        """Test memory subtract function."""
        engine.input_digit("10")
        engine.memory_add()
        engine.clear()
        engine.input_digit("3")
        engine.memory_subtract()
        assert engine.memory == 7.0

    def test_memory_recall(self, engine):
        """Test memory recall function."""
        engine.memory = 42.0
        result = engine.memory_recall()
        assert result == "42.0"
        assert engine.current_value == "42.0"

    def test_memory_clear(self, engine):
        """Test memory clear function."""
        engine.memory = 42.0
        engine.memory_clear()
        assert engine.memory == 0.0

    def test_get_history(self, engine):
        """Test getting history."""
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        engine.calculate()
        
        history = engine.get_history()
        assert len(history) == 1
        assert history[0]["result"] == "8.0"

    def test_clear_history(self, engine):
        """Test clearing history."""
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        engine.calculate()
        
        assert len(engine.history) == 1
        engine.clear_history()
        assert len(engine.history) == 0

    def test_multiple_calculations(self, engine):
        """Test multiple calculations."""
        # First calculation
        engine.input_digit("5")
        engine.set_operation("+")
        engine.input_digit("3")
        result1 = engine.calculate()
        assert result1 == "8.0"
        
        # Second calculation
        engine.set_operation("*")
        engine.input_digit("2")
        result2 = engine.calculate()
        assert result2 == "16.0"
        
        assert len(engine.history) == 2


class TestCalculatorGUI:
    """Test cases for CalculatorGUI class."""

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for testing."""
        config_content = """
gui:
  title: "Test Calculator"
  window_size: "300x400"
  resizable_width: false
  resizable_height: false

history:
  save_to_file: false
  file: "data/test_history.json"
  max_entries: 100

logging:
  level: "DEBUG"
  file: "logs/test.log"
  max_bytes: 10485760
  backup_count: 5
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_gui_init(self, temp_config_file):
        """Test GUI initialization."""
        try:
            from src.main import CalculatorGUI
            gui = CalculatorGUI(config_path=temp_config_file)
            assert gui.config is not None
            assert gui.engine is not None
            gui.root.destroy()
        except ImportError:
            pytest.skip("tkinter not available")

    def test_load_history(self, temp_config_file):
        """Test loading history from file."""
        try:
            from src.main import CalculatorGUI
            import tempfile
            
            # Create test history file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump({
                    "history": [
                        {
                            "expression": "5 + 3",
                            "result": "8",
                            "timestamp": "2024-01-01T00:00:00"
                        }
                    ]
                }, f)
                history_file = f.name
            
            # Update config to use test history file
            with open(temp_config_file, "r") as f:
                config = yaml.safe_load(f)
            config["history"]["file"] = history_file
            
            with open(temp_config_file, "w") as f:
                yaml.dump(config, f)
            
            gui = CalculatorGUI(config_path=temp_config_file)
            assert len(gui.engine.history) == 1
            gui.root.destroy()
            
            Path(history_file).unlink(missing_ok=True)
        except ImportError:
            pytest.skip("tkinter not available")
