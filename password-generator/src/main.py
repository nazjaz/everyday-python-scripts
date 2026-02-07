"""Password Generator - GUI tool for generating secure passwords.

This module provides a graphical user interface for generating customizable
passwords with options for length, character sets, and clipboard integration.
"""

import argparse
import logging
import logging.handlers
import os
import secrets
import string
import sys
from pathlib import Path
from typing import Dict, Optional, Set

import yaml
from dotenv import load_dotenv

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print("Error: tkinter is not available. Please install Python with tkinter support.")
    sys.exit(1)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PasswordGenerator:
    """Generates secure passwords with customizable options."""

    def __init__(self, config: Dict) -> None:
        """Initialize PasswordGenerator.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.char_config = config.get("characters", {})
        self.defaults = config.get("defaults", {})
        self.security_config = config.get("security", {})

    def get_character_set(
        self,
        lowercase: bool = True,
        uppercase: bool = True,
        digits: bool = True,
        symbols: bool = True,
        exclude_similar: bool = True,
        exclude_ambiguous: bool = False,
    ) -> str:
        """Build character set based on options.

        Args:
            lowercase: Include lowercase letters.
            uppercase: Include uppercase letters.
            digits: Include digits.
            symbols: Include symbols.
            exclude_similar: Exclude similar-looking characters.
            exclude_ambiguous: Exclude ambiguous characters.

        Returns:
            String containing all allowed characters.

        Raises:
            ValueError: If no character sets are selected.
        """
        chars = ""

        if lowercase:
            chars += self.char_config.get("lowercase", string.ascii_lowercase)

        if uppercase:
            chars += self.char_config.get("uppercase", string.ascii_uppercase)

        if digits:
            chars += self.char_config.get("digits", string.digits)

        if symbols:
            chars += self.char_config.get("symbols", string.punctuation)

        if not chars:
            raise ValueError("At least one character set must be selected")

        # Remove similar characters
        if exclude_similar:
            similar = self.char_config.get("similar_chars", "0OIl1")
            chars = "".join(c for c in chars if c not in similar)

        # Remove ambiguous characters
        if exclude_ambiguous:
            ambiguous = self.char_config.get("ambiguous_chars", "{}[]()/\\'\"`~,;:.<>")
            chars = "".join(c for c in chars if c not in ambiguous)

        return chars

    def generate_password(
        self,
        length: int,
        lowercase: bool = True,
        uppercase: bool = True,
        digits: bool = True,
        symbols: bool = True,
        exclude_similar: bool = True,
        exclude_ambiguous: bool = False,
    ) -> str:
        """Generate a secure password.

        Args:
            length: Password length.
            lowercase: Include lowercase letters.
            uppercase: Include uppercase letters.
            digits: Include digits.
            symbols: Include symbols.
            exclude_similar: Exclude similar-looking characters.
            exclude_ambiguous: Exclude ambiguous characters.

        Returns:
            Generated password string.

        Raises:
            ValueError: If length is invalid or no character sets selected.
        """
        min_length = self.defaults.get("min_length", 4)
        max_length = self.defaults.get("max_length", 128)

        if length < min_length or length > max_length:
            raise ValueError(
                f"Password length must be between {min_length} and {max_length}"
            )

        char_set = self.get_character_set(
            lowercase, uppercase, digits, symbols, exclude_similar, exclude_ambiguous
        )

        if len(char_set) == 0:
            raise ValueError("Character set is empty after exclusions")

        use_secure = self.security_config.get("use_secure_random", True)

        if use_secure:
            password = "".join(secrets.choice(char_set) for _ in range(length))
        else:
            import random
            password = "".join(random.choice(char_set) for _ in range(length))

        logger.info(f"Generated password (length: {length})")

        return password

    def calculate_entropy(self, password: str, char_set_size: int) -> float:
        """Calculate password entropy in bits.

        Args:
            password: Password string.
            char_set_size: Size of character set used.

        Returns:
            Entropy in bits.
        """
        length = len(password)
        if length == 0 or char_set_size == 0:
            return 0.0

        import math
        return length * math.log2(char_set_size)


class PasswordGeneratorGUI:
    """Graphical user interface for password generator."""

    def __init__(self, config: Dict) -> None:
        """Initialize GUI.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.generator = PasswordGenerator(config)
        self.gui_config = config.get("gui", {})

        self.root = tk.Tk()
        self.root.title(self.gui_config.get("title", "Password Generator"))

        # Window size
        width = self.gui_config.get("window_width", 500)
        height = self.gui_config.get("window_height", 600)
        self.root.geometry(f"{width}x{height}")

        # Center window
        self._center_window()

        # Variables
        self.password_var = tk.StringVar()
        self.length_var = tk.IntVar(
            value=self.config.get("defaults", {}).get("length", 16)
        )
        self.lowercase_var = tk.BooleanVar(
            value=self.config.get("defaults", {}).get("character_sets", {}).get(
                "lowercase", True
            )
        )
        self.uppercase_var = tk.BooleanVar(
            value=self.config.get("defaults", {}).get("character_sets", {}).get(
                "uppercase", True
            )
        )
        self.digits_var = tk.BooleanVar(
            value=self.config.get("defaults", {}).get("character_sets", {}).get(
                "digits", True
            )
        )
        self.symbols_var = tk.BooleanVar(
            value=self.config.get("defaults", {}).get("character_sets", {}).get(
                "symbols", True
            )
        )
        self.exclude_similar_var = tk.BooleanVar(
            value=self.config.get("defaults", {}).get("character_sets", {}).get(
                "exclude_similar", True
            )
        )
        self.exclude_ambiguous_var = tk.BooleanVar(
            value=self.config.get("defaults", {}).get("character_sets", {}).get(
                "exclude_ambiguous", False
            )
        )

        self._create_widgets()

    def _center_window(self) -> None:
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create and layout GUI widgets."""
        font_family = self.gui_config.get("font_family", "Arial")
        font_size = self.gui_config.get("font_size", 10)
        font_size_large = self.gui_config.get("font_size_large", 12)
        font_size_title = self.gui_config.get("font_size_title", 14)

        # Title
        title_label = tk.Label(
            self.root,
            text="Password Generator",
            font=(font_family, font_size_title, "bold"),
        )
        title_label.pack(pady=10)

        # Password display frame
        password_frame = ttk.Frame(self.root, padding=10)
        password_frame.pack(fill=tk.X, padx=10, pady=5)

        password_label = tk.Label(password_frame, text="Generated Password:")
        password_label.pack(anchor=tk.W)

        password_entry = tk.Entry(
            password_frame,
            textvariable=self.password_var,
            font=(font_family, font_size),
            state="readonly",
        )
        password_entry.pack(fill=tk.X, pady=5)

        # Buttons frame
        buttons_frame = ttk.Frame(self.root, padding=10)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)

        generate_button = tk.Button(
            buttons_frame,
            text="Generate Password",
            command=self._generate_password,
            font=(font_family, font_size),
        )
        generate_button.pack(side=tk.LEFT, padx=5)

        copy_button = tk.Button(
            buttons_frame,
            text="Copy to Clipboard",
            command=self._copy_to_clipboard,
            font=(font_family, font_size),
        )
        copy_button.pack(side=tk.LEFT, padx=5)

        # Length frame
        length_frame = ttk.LabelFrame(self.root, text="Password Length", padding=10)
        length_frame.pack(fill=tk.X, padx=10, pady=5)

        min_length = self.config.get("defaults", {}).get("min_length", 4)
        max_length = self.config.get("defaults", {}).get("max_length", 128)

        length_label = tk.Label(length_frame, text="Length:")
        length_label.pack(side=tk.LEFT, padx=5)

        length_scale = tk.Scale(
            length_frame,
            from_=min_length,
            to=max_length,
            orient=tk.HORIZONTAL,
            variable=self.length_var,
            font=(font_family, font_size),
        )
        length_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        length_value_label = tk.Label(
            length_frame, textvariable=self.length_var, font=(font_family, font_size)
        )
        length_value_label.pack(side=tk.LEFT, padx=5)

        # Update length display when scale changes
        self.length_var.trace_add("write", lambda *args: length_value_label.config(text=str(self.length_var.get())))

        # Character sets frame
        chars_frame = ttk.LabelFrame(self.root, text="Character Sets", padding=10)
        chars_frame.pack(fill=tk.X, padx=10, pady=5)

        lowercase_check = tk.Checkbutton(
            chars_frame,
            text="Lowercase (a-z)",
            variable=self.lowercase_var,
            font=(font_family, font_size),
        )
        lowercase_check.pack(anchor=tk.W, pady=2)

        uppercase_check = tk.Checkbutton(
            chars_frame,
            text="Uppercase (A-Z)",
            variable=self.uppercase_var,
            font=(font_family, font_size),
        )
        uppercase_check.pack(anchor=tk.W, pady=2)

        digits_check = tk.Checkbutton(
            chars_frame,
            text="Digits (0-9)",
            variable=self.digits_var,
            font=(font_family, font_size),
        )
        digits_check.pack(anchor=tk.W, pady=2)

        symbols_check = tk.Checkbutton(
            chars_frame,
            text="Symbols (!@#$%...)",
            variable=self.symbols_var,
            font=(font_family, font_size),
        )
        symbols_check.pack(anchor=tk.W, pady=2)

        # Options frame
        options_frame = ttk.LabelFrame(self.root, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        exclude_similar_check = tk.Checkbutton(
            options_frame,
            text="Exclude similar characters (0, O, l, I, 1)",
            variable=self.exclude_similar_var,
            font=(font_family, font_size),
        )
        exclude_similar_check.pack(anchor=tk.W, pady=2)

        exclude_ambiguous_check = tk.Checkbutton(
            options_frame,
            text="Exclude ambiguous characters ({, }, [, ], etc.)",
            variable=self.exclude_ambiguous_var,
            font=(font_family, font_size),
        )
        exclude_ambiguous_check.pack(anchor=tk.W, pady=2)

        # Info frame
        info_frame = ttk.Frame(self.root, padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        info_text = tk.Text(
            info_frame,
            height=6,
            wrap=tk.WORD,
            font=(font_family, font_size - 1),
            state=tk.DISABLED,
        )
        info_text.pack(fill=tk.BOTH, expand=True)

        info_text.config(state=tk.NORMAL)
        info_text.insert(
            tk.END,
            "Tips:\n"
            "- Select at least one character set\n"
            "- Longer passwords are more secure\n"
            "- Use all character types for maximum security\n"
            "- Exclude similar characters to avoid confusion",
        )
        info_text.config(state=tk.DISABLED)

        self.info_text = info_text

    def _generate_password(self) -> None:
        """Generate a new password and display it."""
        try:
            password = self.generator.generate_password(
                length=self.length_var.get(),
                lowercase=self.lowercase_var.get(),
                uppercase=self.uppercase_var.get(),
                digits=self.digits_var.get(),
                symbols=self.symbols_var.get(),
                exclude_similar=self.exclude_similar_var.get(),
                exclude_ambiguous=self.exclude_ambiguous_var.get(),
            )

            self.password_var.set(password)

            # Calculate and log entropy
            try:
                char_set = self.generator.get_character_set(
                    self.lowercase_var.get(),
                    self.uppercase_var.get(),
                    self.digits_var.get(),
                    self.symbols_var.get(),
                    self.exclude_similar_var.get(),
                    self.exclude_ambiguous_var.get(),
                )
                entropy = self.generator.calculate_entropy(password, len(char_set))
                logger.info(f"Password entropy: {entropy:.2f} bits")
            except Exception as e:
                logger.debug(f"Could not calculate entropy: {e}")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
            logger.error(f"Password generation error: {e}")

    def _copy_to_clipboard(self) -> None:
        """Copy password to clipboard."""
        password = self.password_var.get()

        if not password:
            messagebox.showwarning("Warning", "No password to copy. Generate one first.")
            return

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            self.root.update()
            messagebox.showinfo("Success", "Password copied to clipboard!")
            logger.info("Password copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            logger.error(f"Clipboard error: {e}")

    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/password_generator.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Password Generator with GUI")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Generate password from command line (non-GUI mode)",
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        help="Password length (CLI mode only)",
    )
    parser.add_argument(
        "--no-lowercase",
        action="store_true",
        help="Exclude lowercase letters (CLI mode only)",
    )
    parser.add_argument(
        "--no-uppercase",
        action="store_true",
        help="Exclude uppercase letters (CLI mode only)",
    )
    parser.add_argument(
        "--no-digits",
        action="store_true",
        help="Exclude digits (CLI mode only)",
    )
    parser.add_argument(
        "--no-symbols",
        action="store_true",
        help="Exclude symbols (CLI mode only)",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        if args.cli:
            # CLI mode
            generator = PasswordGenerator(config)
            length = args.length or config.get("defaults", {}).get("length", 16)

            password = generator.generate_password(
                length=length,
                lowercase=not args.no_lowercase,
                uppercase=not args.no_uppercase,
                digits=not args.no_digits,
                symbols=not args.no_symbols,
            )

            print(password)
            logger.info("Password generated via CLI")

        else:
            # GUI mode
            app = PasswordGeneratorGUI(config)
            app.run()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
