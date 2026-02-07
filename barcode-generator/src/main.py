"""Barcode Generator - GUI application for generating barcodes.

This module provides a graphical user interface for generating barcodes in
various formats from product codes or identifiers. Supports multiple barcode
formats including EAN-13, Code128, Code39, EAN-8, and more.
"""

import logging
import logging.handlers
from pathlib import Path
from tkinter import (
    Button,
    Entry,
    Frame,
    Label,
    LabelFrame,
    OptionMenu,
    StringVar,
    Tk,
    filedialog,
    messagebox,
    ttk,
)
from typing import Any, Dict, List, Optional

import yaml
from barcode import Code128, Code39, EAN13, EAN8, get_barcode_class
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from PIL import Image, ImageTk

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BarcodeGeneratorApp:
    """GUI application for generating barcodes."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize BarcodeGeneratorApp with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.supported_formats = self._load_supported_formats()
        self.root = Tk()
        self._setup_window()
        self._create_widgets()
        self.current_barcode_image: Optional[Image.Image] = None

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary containing configuration settings.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if not config:
                raise ValueError("Configuration file is empty")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            raise

    def _setup_logging(self) -> None:
        """Configure logging based on configuration settings."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/app.log")
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(message)s"
        )

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(),
            ],
        )

    def _load_supported_formats(self) -> Dict[str, Any]:
        """Load supported barcode formats from configuration.

        Returns:
            Dictionary mapping format names to barcode classes.
        """
        formats = {
            "EAN-13": EAN13,
            "EAN-8": EAN8,
            "Code128": Code128,
            "Code39": Code39,
        }

        # Try to load additional formats
        additional_formats = self.config.get("barcode", {}).get(
            "additional_formats", []
        )
        for format_name in additional_formats:
            try:
                barcode_class = get_barcode_class(format_name)
                formats[format_name] = barcode_class
            except Exception as e:
                logger.warning(
                    f"Could not load barcode format {format_name}: {e}"
                )

        return formats

    def _setup_window(self) -> None:
        """Configure main window properties."""
        self.root.title("Barcode Generator")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create and arrange GUI widgets."""
        # Main container
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Input section
        input_frame = LabelFrame(
            main_frame, text="Barcode Input", padx=10, pady=10
        )
        input_frame.pack(fill="x", pady=(0, 10))

        # Format selection
        format_label = Label(input_frame, text="Format:")
        format_label.grid(row=0, column=0, sticky="w", pady=5)

        self.format_var = StringVar(value=list(self.supported_formats.keys())[0])
        format_menu = OptionMenu(
            input_frame,
            self.format_var,
            *self.supported_formats.keys(),
        )
        format_menu.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        input_frame.grid_columnconfigure(1, weight=1)

        # Code input
        code_label = Label(input_frame, text="Code/Identifier:")
        code_label.grid(row=1, column=0, sticky="w", pady=5)

        self.code_entry = Entry(input_frame, width=30)
        self.code_entry.grid(
            row=1, column=1, sticky="ew", pady=5, padx=(10, 0)
        )
        self.code_entry.bind("<Return>", lambda e: self.generate_barcode())

        # Generate button
        generate_button = Button(
            input_frame,
            text="Generate Barcode",
            command=self.generate_barcode,
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5,
        )
        generate_button.grid(
            row=2, column=0, columnspan=2, pady=10, sticky="ew"
        )

        # Preview section
        preview_frame = LabelFrame(
            main_frame, text="Barcode Preview", padx=10, pady=10
        )
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.preview_label = Label(
            preview_frame,
            text="Enter a code and click 'Generate Barcode'",
            bg="white",
            relief="sunken",
            width=50,
            height=10,
        )
        self.preview_label.pack(fill="both", expand=True, padx=5, pady=5)

        # Actions section
        actions_frame = Frame(main_frame)
        actions_frame.pack(fill="x")

        save_button = Button(
            actions_frame,
            text="Save Barcode",
            command=self.save_barcode,
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=5,
        )
        save_button.pack(side="left", padx=5)

        clear_button = Button(
            actions_frame,
            text="Clear",
            command=self.clear_preview,
            bg="#f44336",
            fg="white",
            padx=20,
            pady=5,
        )
        clear_button.pack(side="left", padx=5)

        # Status bar
        self.status_var = StringVar(value="Ready")
        status_bar = Label(
            main_frame,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padx=5,
            pady=2,
        )
        status_bar.pack(fill="x", pady=(10, 0))

    def _validate_code(self, code: str, format_name: str) -> bool:
        """Validate code for selected barcode format.

        Args:
            code: Code/identifier to validate.
            format_name: Name of barcode format.

        Returns:
            True if code is valid, False otherwise.
        """
        if not code.strip():
            return False

        # Basic validation for common formats
        if format_name == "EAN-13":
            return code.isdigit() and len(code) == 13
        elif format_name == "EAN-8":
            return code.isdigit() and len(code) == 8
        elif format_name == "Code39":
            # Code39 supports alphanumeric and some special chars
            return len(code) > 0 and all(
                c.isalnum() or c in "-. $/%+"
                for c in code
            )
        elif format_name == "Code128":
            # Code128 supports ASCII characters
            return len(code) > 0 and all(ord(c) < 128 for c in code)

        return True

    def generate_barcode(self) -> None:
        """Generate barcode from input code."""
        code = self.code_entry.get().strip()
        format_name = self.format_var.get()

        if not code:
            messagebox.showwarning(
                "Input Required", "Please enter a code or identifier."
            )
            return

        # Validate code
        if not self._validate_code(code, format_name):
            messagebox.showerror(
                "Invalid Code",
                f"Code '{code}' is not valid for format {format_name}.\n"
                f"Please check the format requirements.",
            )
            self.status_var.set(f"Error: Invalid code for {format_name}")
            return

        try:
            # Get barcode class
            barcode_class = self.supported_formats[format_name]

            # Generate barcode
            barcode = barcode_class(code, writer=ImageWriter())

            # Get writer options from config
            writer_options = self.config.get("barcode", {}).get(
                "writer_options", {}
            )

            # Create temporary file for barcode image
            temp_path = Path("temp_barcode.png")
            barcode.save(temp_path, options=writer_options)

            # Load and display image
            barcode_image = Image.open(temp_path)
            self.current_barcode_image = barcode_image.copy()

            # Resize for preview (maintain aspect ratio)
            preview_width = 400
            preview_height = int(
                preview_width
                * (barcode_image.height / barcode_image.width)
            )
            barcode_image = barcode_image.resize(
                (preview_width, preview_height), Image.Resampling.LANCZOS
            )

            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(barcode_image)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # Keep a reference

            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

            self.status_var.set(
                f"Generated {format_name} barcode for code: {code}"
            )
            logger.info(
                f"Generated {format_name} barcode for code: {code}",
                extra={"format": format_name, "code": code},
            )

        except Exception as e:
            error_msg = f"Error generating barcode: {str(e)}"
            logger.error(error_msg, exc_info=True)
            messagebox.showerror("Generation Error", error_msg)
            self.status_var.set("Error generating barcode")

    def save_barcode(self) -> None:
        """Save generated barcode to file."""
        if self.current_barcode_image is None:
            messagebox.showwarning(
                "No Barcode", "Please generate a barcode first."
            )
            return

        # Get save location
        default_filename = f"barcode_{self.code_entry.get()}.png"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*"),
            ],
            initialfile=default_filename,
        )

        if file_path:
            try:
                # Save image
                self.current_barcode_image.save(file_path)
                self.status_var.set(f"Barcode saved to: {file_path}")
                logger.info(f"Barcode saved to: {file_path}")
                messagebox.showinfo(
                    "Success", f"Barcode saved to:\n{file_path}"
                )
            except Exception as e:
                error_msg = f"Error saving barcode: {str(e)}"
                logger.error(error_msg, exc_info=True)
                messagebox.showerror("Save Error", error_msg)
                self.status_var.set("Error saving barcode")

    def clear_preview(self) -> None:
        """Clear barcode preview."""
        self.preview_label.config(image="", text="Enter a code and click 'Generate Barcode'")
        self.preview_label.image = None
        self.current_barcode_image = None
        self.code_entry.delete(0, "end")
        self.status_var.set("Ready")

    def run(self) -> None:
        """Start the GUI application."""
        logger.info("Starting Barcode Generator application")
        self.root.mainloop()


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GUI application for generating barcodes in various formats"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = BarcodeGeneratorApp(config_path=args.config)
        app.run()
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
