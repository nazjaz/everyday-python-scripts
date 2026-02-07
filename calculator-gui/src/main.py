"""Calculator GUI - Simple calculator application with GUI.

This module provides a calculator application with graphical user interface,
supporting basic arithmetic operations, history tracking, and memory functions.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CalculatorEngine:
    """Calculator engine for performing calculations."""

    def __init__(self) -> None:
        """Initialize calculator engine."""
        self.memory = 0.0
        self.current_value = "0"
        self.previous_value = None
        self.operation = None
        self.history: List[Dict[str, str]] = []

    def input_digit(self, digit: str) -> str:
        """Input a digit.

        Args:
            digit: Digit string (0-9).

        Returns:
            Current display value.
        """
        if self.current_value == "0":
            self.current_value = digit
        else:
            self.current_value += digit
        return self.current_value

    def input_decimal(self) -> str:
        """Input decimal point.

        Returns:
            Current display value.
        """
        if "." not in self.current_value:
            self.current_value += "."
        return self.current_value

    def clear(self) -> str:
        """Clear current value.

        Returns:
            Current display value ("0").
        """
        self.current_value = "0"
        self.previous_value = None
        self.operation = None
        return self.current_value

    def clear_entry(self) -> str:
        """Clear current entry only.

        Returns:
            Current display value ("0").
        """
        self.current_value = "0"
        return self.current_value

    def set_operation(self, operation: str) -> Optional[str]:
        """Set operation to perform.

        Args:
            operation: Operation symbol (+, -, *, /).

        Returns:
            Current display value or None if operation should be performed.
        """
        if self.operation and self.previous_value is not None:
            result = self._perform_calculation()
            if result is None:
                return None
            self.current_value = str(result)
            self.previous_value = float(self.current_value)
        else:
            self.previous_value = float(self.current_value)

        self.operation = operation
        self.current_value = "0"
        return self.current_value

    def calculate(self) -> Optional[str]:
        """Perform calculation.

        Returns:
            Result as string or None if error.
        """
        if self.operation and self.previous_value is not None:
            result = self._perform_calculation()
            if result is None:
                return None

            # Add to history
            expression = f"{self.previous_value} {self.operation} {float(self.current_value)}"
            self.history.append({
                "expression": expression,
                "result": str(result),
                "timestamp": datetime.now().isoformat(),
            })

            self.current_value = str(result)
            self.previous_value = None
            self.operation = None
            return self.current_value

        return self.current_value

    def _perform_calculation(self) -> Optional[float]:
        """Perform the current calculation.

        Returns:
            Calculation result or None if error.
        """
        if self.operation is None or self.previous_value is None:
            return None

        try:
            current = float(self.current_value)

            if self.operation == "+":
                result = self.previous_value + current
            elif self.operation == "-":
                result = self.previous_value - current
            elif self.operation == "*":
                result = self.previous_value * current
            elif self.operation == "/":
                if current == 0:
                    logger.error("Division by zero")
                    return None
                result = self.previous_value / current
            else:
                return None

            return result

        except (ValueError, TypeError) as e:
            logger.error(f"Calculation error: {e}")
            return None

    def memory_add(self) -> None:
        """Add current value to memory."""
        try:
            self.memory += float(self.current_value)
            logger.debug(f"Memory add: {self.memory}")
        except ValueError:
            logger.error("Invalid value for memory operation")

    def memory_subtract(self) -> None:
        """Subtract current value from memory."""
        try:
            self.memory -= float(self.current_value)
            logger.debug(f"Memory subtract: {self.memory}")
        except ValueError:
            logger.error("Invalid value for memory operation")

    def memory_recall(self) -> str:
        """Recall value from memory.

        Returns:
            Memory value as string.
        """
        self.current_value = str(self.memory)
        return self.current_value

    def memory_clear(self) -> None:
        """Clear memory."""
        self.memory = 0.0
        logger.debug("Memory cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """Get calculation history.

        Returns:
            List of history entries.
        """
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()
        logger.debug("History cleared")


class CalculatorGUI:
    """Calculator GUI application."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize calculator GUI.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.engine = CalculatorEngine()
        self.history_window = None
        self._setup_gui()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
        """
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("HISTORY_FILE"):
            config["history"]["file"] = os.getenv("HISTORY_FILE")
        if os.getenv("SAVE_HISTORY"):
            config["history"]["save_to_file"] = os.getenv("SAVE_HISTORY").lower() == "true"

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/calculator.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _setup_gui(self) -> None:
        """Set up the GUI."""
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox, scrolledtext
        except ImportError:
            logger.error("tkinter not available. Install tkinter for GUI support.")
            raise ImportError("tkinter is required for the GUI")

        self.root = tk.Tk()
        self.root.title(self.config.get("gui", {}).get("title", "Calculator"))
        
        gui_config = self.config.get("gui", {})
        window_size = gui_config.get("window_size", "300x400")
        self.root.geometry(window_size)
        self.root.resizable(
            gui_config.get("resizable_width", False),
            gui_config.get("resizable_height", False),
        )

        # Display
        self.display_var = tk.StringVar(value="0")
        display_frame = tk.Frame(self.root)
        display_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        display = tk.Entry(
            display_frame,
            textvariable=self.display_var,
            font=("Arial", 16),
            justify=tk.RIGHT,
            state="readonly",
        )
        display.pack(fill=tk.BOTH, expand=True)

        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Button layout
        buttons = [
            ["MC", "MR", "M+", "M-"],
            ["C", "CE", "/", "*"],
            ["7", "8", "9", "-"],
            ["4", "5", "6", "+"],
            ["1", "2", "3", "="],
            ["0", ".", "H", ""],
        ]

        for row_idx, row in enumerate(buttons):
            for col_idx, label in enumerate(row):
                if not label:  # Skip empty cells
                    continue
                if label == "=" and row_idx == 4:
                    # Make = button span 2 columns (rows 4 and 5, columns 3 and 4)
                    btn = tk.Button(
                        button_frame,
                        text=label,
                        command=lambda l=label: self._button_click(l),
                        font=("Arial", 12),
                        height=2,
                    )
                    btn.grid(row=row_idx, column=col_idx, rowspan=2, sticky="nsew", padx=2, pady=2)
                elif label == "0" and row_idx == 5:
                    # Make 0 button span 2 columns
                    btn = tk.Button(
                        button_frame,
                        text=label,
                        command=lambda l=label: self._button_click(l),
                        font=("Arial", 12),
                        height=2,
                    )
                    btn.grid(row=row_idx, column=col_idx, columnspan=2, sticky="nsew", padx=2, pady=2)
                else:
                    btn = tk.Button(
                        button_frame,
                        text=label,
                        command=lambda l=label: self._button_click(l),
                        font=("Arial", 12),
                        height=2,
                    )
                    btn.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)

        # Configure grid weights
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)
        for i in range(6):
            button_frame.grid_rowconfigure(i, weight=1)

        # Load history if enabled
        if self.config.get("history", {}).get("save_to_file", True):
            self._load_history()

        logger.info("GUI initialized successfully")

    def _button_click(self, label: str) -> None:
        """Handle button click.

        Args:
            label: Button label.
        """
        if label.isdigit():
            value = self.engine.input_digit(label)
            self.display_var.set(value)
        elif label == ".":
            value = self.engine.input_decimal()
            self.display_var.set(value)
        elif label == "C":
            value = self.engine.clear()
            self.display_var.set(value)
        elif label == "CE":
            value = self.engine.clear_entry()
            self.display_var.set(value)
        elif label in ["+", "-", "*", "/"]:
            value = self.engine.set_operation(label)
            if value:
                self.display_var.set(value)
        elif label == "=":
            result = self.engine.calculate()
            if result:
                self.display_var.set(result)
            else:
                self.display_var.set("Error")
                logger.error("Calculation error")
        elif label == "MC":
            self.engine.memory_clear()
        elif label == "MR":
            value = self.engine.memory_recall()
            self.display_var.set(value)
        elif label == "M+":
            self.engine.memory_add()
        elif label == "M-":
            self.engine.memory_subtract()
        elif label == "H":
            self._show_history()

    def _show_history(self) -> None:
        """Show calculation history window."""
        try:
            import tkinter as tk
            from tkinter import scrolledtext, messagebox
        except ImportError:
            return

        if self.history_window is not None:
            self.history_window.destroy()

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Calculation History")
        self.history_window.geometry("400x300")

        # History text area
        history_text = scrolledtext.ScrolledText(
            self.history_window,
            wrap=tk.WORD,
            font=("Courier", 10),
        )
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Populate history
        history = self.engine.get_history()
        if not history:
            history_text.insert(tk.END, "No history available.\n")
        else:
            for entry in reversed(history):
                history_text.insert(
                    tk.END,
                    f"{entry['expression']} = {entry['result']}\n"
                    f"  ({entry['timestamp']})\n\n",
                )

        history_text.config(state=tk.DISABLED)

        # Buttons
        button_frame = tk.Frame(self.history_window)
        button_frame.pack(pady=10)

        clear_btn = tk.Button(
            button_frame,
            text="Clear History",
            command=self._clear_history,
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.history_window.destroy,
        )
        close_btn.pack(side=tk.LEFT, padx=5)

    def _clear_history(self) -> None:
        """Clear calculation history."""
        self.engine.clear_history()
        if self.history_window:
            self.history_window.destroy()
            self.history_window = None
        logger.info("History cleared by user")

    def _load_history(self) -> None:
        """Load history from file."""
        history_config = self.config.get("history", {})
        history_file = history_config.get("file", "data/calculator_history.json")

        history_path = Path(history_file)
        if not history_path.is_absolute():
            project_root = Path(__file__).parent.parent
            history_path = project_root / history_file

        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.engine.history = data.get("history", [])
                logger.info(f"Loaded {len(self.engine.history)} history entries")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading history: {e}")

    def _save_history(self) -> None:
        """Save history to file."""
        if not self.config.get("history", {}).get("save_to_file", True):
            return

        history_config = self.config.get("history", {})
        history_file = history_config.get("file", "data/calculator_history.json")

        history_path = Path(history_file)
        if not history_path.is_absolute():
            project_root = Path(__file__).parent.parent
            history_path = project_root / history_file

        history_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "history": self.engine.history,
                        "saved_at": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
            logger.debug("History saved to file")
        except IOError as e:
            logger.error(f"Error saving history: {e}")

    def run(self) -> None:
        """Run the calculator application."""
        try:
            # Save history on exit
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error running GUI: {e}", exc_info=True)

    def _on_closing(self) -> None:
        """Handle window closing event."""
        self._save_history()
        self.root.destroy()


def main() -> int:
    """Main entry point for calculator GUI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Simple calculator application with GUI"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = CalculatorGUI(config_path=args.config)
        app.run()
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except ImportError as e:
        logger.error(f"GUI library error: {e}")
        print("Error: tkinter is required for the GUI.")
        print("On Linux, install with: sudo apt-get install python3-tk")
        print("On macOS, tkinter should be included with Python.")
        print("On Windows, tkinter should be included with Python.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
