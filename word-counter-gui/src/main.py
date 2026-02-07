"""Word Counter GUI.

A Python script that creates a simple word counter application with GUI,
analyzing text files for word frequency, character count, and reading time estimates.
"""

import argparse
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/counter.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    logger.error("tkinter is not available. Please install python3-tk package.")
    sys.exit(1)


class WordCounter:
    """Analyzes text for word frequency, character count, and reading time."""

    AVERAGE_READING_SPEED = 200
    AVERAGE_READING_SPEED_SLOW = 150
    AVERAGE_READING_SPEED_FAST = 250

    def __init__(self, text: str = "") -> None:
        """Initialize the word counter with text.

        Args:
            text: Text to analyze
        """
        self.text = text

    def analyze(self) -> Dict[str, Any]:
        """Analyze the text and return statistics.

        Returns:
            Dictionary containing analysis results
        """
        if not self.text:
            return {
                "word_count": 0,
                "character_count": 0,
                "character_count_no_spaces": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "word_frequency": {},
                "reading_time": 0,
                "reading_time_slow": 0,
                "reading_time_fast": 0,
            }

        word_count = len(self._extract_words())
        character_count = len(self.text)
        character_count_no_spaces = len(self.text.replace(" ", ""))
        sentence_count = self._count_sentences()
        paragraph_count = self._count_paragraphs()
        word_frequency = self._calculate_word_frequency()

        word_count_for_time = word_count if word_count > 0 else 1
        reading_time = word_count_for_time / self.AVERAGE_READING_SPEED
        reading_time_slow = word_count_for_time / self.AVERAGE_READING_SPEED_SLOW
        reading_time_fast = word_count_for_time / self.AVERAGE_READING_SPEED_FAST

        return {
            "word_count": word_count,
            "character_count": character_count,
            "character_count_no_spaces": character_count_no_spaces,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "word_frequency": word_frequency,
            "reading_time": reading_time,
            "reading_time_slow": reading_time_slow,
            "reading_time_fast": reading_time_fast,
        }

    def _extract_words(self) -> List[str]:
        """Extract words from text.

        Returns:
            List of words
        """
        words = re.findall(r"\b\w+\b", self.text.lower())
        return words

    def _count_sentences(self) -> int:
        """Count sentences in text.

        Returns:
            Number of sentences
        """
        sentences = re.split(r"[.!?]+\s+", self.text.strip())
        sentences = [s for s in sentences if s.strip()]
        return len(sentences) if sentences else 0

    def _count_paragraphs(self) -> int:
        """Count paragraphs in text.

        Returns:
            Number of paragraphs
        """
        paragraphs = [p for p in self.text.split("\n\n") if p.strip()]
        return len(paragraphs) if paragraphs else 0

    def _calculate_word_frequency(self, top_n: int = 10) -> Dict[str, int]:
        """Calculate word frequency.

        Args:
            top_n: Number of top words to return

        Returns:
            Dictionary of word frequencies
        """
        words = self._extract_words()
        if not words:
            return {}

        word_counter = Counter(words)
        top_words = word_counter.most_common(top_n)

        return dict(top_words)

    def format_reading_time(self, minutes: float) -> str:
        """Format reading time as human-readable string.

        Args:
            minutes: Reading time in minutes

        Returns:
            Formatted string
        """
        if minutes < 1:
            seconds = int(minutes * 60)
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        elif minutes < 60:
            mins = int(minutes)
            secs = int((minutes - mins) * 60)
            if secs > 0:
                return f"{mins} minute{'s' if mins != 1 else ''} {secs} second{'s' if secs != 1 else ''}"
            else:
                return f"{mins} minute{'s' if mins != 1 else ''}"
        else:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            return f"{hours} hour{'s' if hours != 1 else ''} {mins} minute{'s' if mins != 1 else ''}"


class WordCounterGUI:
    """GUI application for word counter."""

    def __init__(self, config: Dict = None) -> None:
        """Initialize the GUI application.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.counter = WordCounter()
        self.current_file = None

        self.root = tk.Tk()
        self.root.title("Word Counter")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(file_frame, text="Open File", command=self.open_file).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(file_frame, text="Clear", command=self.clear_text).grid(
            row=0, column=1, padx=5
        )

        self.file_label = ttk.Label(file_frame, text="No file loaded")
        self.file_label.grid(row=0, column=2, padx=10, sticky=tk.W)

        text_label = ttk.Label(main_frame, text="Text Input:")
        text_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.text_area = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, width=60, height=20
        )
        self.text_area.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.text_area.bind("<KeyRelease>", self.on_text_change)

        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        stats_frame.columnconfigure(1, weight=1)

        self.stats_labels = {}

        stats = [
            ("Word Count:", "word_count"),
            ("Character Count:", "character_count"),
            ("Characters (no spaces):", "character_count_no_spaces"),
            ("Sentences:", "sentence_count"),
            ("Paragraphs:", "paragraph_count"),
        ]

        for i, (label, key) in enumerate(stats):
            ttk.Label(stats_frame, text=label).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            value_label = ttk.Label(stats_frame, text="0", font=("TkDefaultFont", 10, "bold"))
            value_label.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.stats_labels[key] = value_label

        reading_frame = ttk.LabelFrame(main_frame, text="Reading Time", padding="10")
        reading_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        reading_stats = [
            ("Average (200 wpm):", "reading_time"),
            ("Slow (150 wpm):", "reading_time_slow"),
            ("Fast (250 wpm):", "reading_time_fast"),
        ]

        for i, (label, key) in enumerate(reading_stats):
            ttk.Label(reading_frame, text=label).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            value_label = ttk.Label(reading_frame, text="0 seconds", font=("TkDefaultFont", 10))
            value_label.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.stats_labels[key] = value_label

        frequency_frame = ttk.LabelFrame(main_frame, text="Top 10 Most Frequent Words", padding="10")
        frequency_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.frequency_text = scrolledtext.ScrolledText(
            frequency_frame, wrap=tk.WORD, width=60, height=8, state=tk.DISABLED
        )
        self.frequency_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.update_statistics()

    def open_file(self) -> None:
        """Open a text file and load its content."""
        file_path = filedialog.askopenfilename(
            title="Open Text File",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.current_file = Path(file_path)
                self.file_label.config(text=f"File: {self.current_file.name}")

                self.update_statistics()

                logger.info(f"Loaded file: {file_path}")

            except UnicodeDecodeError:
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()

                    self.text_area.delete("1.0", tk.END)
                    self.text_area.insert("1.0", content)
                    self.current_file = Path(file_path)
                    self.file_label.config(text=f"File: {self.current_file.name}")

                    self.update_statistics()

                except Exception as e:
                    messagebox.showerror("Error", f"Could not read file: {e}")
                    logger.error(f"Error reading file {file_path}: {e}")

            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")
                logger.error(f"Error opening file {file_path}: {e}")

    def clear_text(self) -> None:
        """Clear the text area."""
        self.text_area.delete("1.0", tk.END)
        self.current_file = None
        self.file_label.config(text="No file loaded")
        self.update_statistics()

    def on_text_change(self, event=None) -> None:
        """Handle text change event."""
        self.update_statistics()

    def update_statistics(self) -> None:
        """Update all statistics displays."""
        text = self.text_area.get("1.0", tk.END).rstrip("\n")
        self.counter.text = text
        stats = self.counter.analyze()

        self.stats_labels["word_count"].config(text=str(stats["word_count"]))
        self.stats_labels["character_count"].config(text=str(stats["character_count"]))
        self.stats_labels["character_count_no_spaces"].config(
            text=str(stats["character_count_no_spaces"])
        )
        self.stats_labels["sentence_count"].config(text=str(stats["sentence_count"]))
        self.stats_labels["paragraph_count"].config(text=str(stats["paragraph_count"]))

        self.stats_labels["reading_time"].config(
            text=self.counter.format_reading_time(stats["reading_time"])
        )
        self.stats_labels["reading_time_slow"].config(
            text=self.counter.format_reading_time(stats["reading_time_slow"])
        )
        self.stats_labels["reading_time_fast"].config(
            text=self.counter.format_reading_time(stats["reading_time_fast"])
        )

        self.frequency_text.config(state=tk.NORMAL)
        self.frequency_text.delete("1.0", tk.END)

        if stats["word_frequency"]:
            frequency_lines = []
            for word, count in stats["word_frequency"].items():
                frequency_lines.append(f"{word}: {count}")

            self.frequency_text.insert("1.0", "\n".join(frequency_lines))
        else:
            self.frequency_text.insert("1.0", "No words found")

        self.frequency_text.config(state=tk.DISABLED)

    def run(self) -> None:
        """Start the GUI application."""
        self.root.mainloop()


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(description="Word Counter GUI Application")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        config = {}
        if args.config:
            config = load_config(Path(args.config))

        app = WordCounterGUI(config=config)
        app.run()

        return 0

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        messagebox.showerror("Error", f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
