"""QR Code Generator - Simple GUI application for generating QR codes.

This module provides a graphical user interface for generating QR codes from
text, URLs, or contact information (vCard format). Users can generate QR
codes, preview them, and save them to files.
"""

import logging
import logging.handlers
from io import BytesIO
from pathlib import Path
from tkinter import (
    Button,
    Canvas,
    Entry,
    Frame,
    Label,
    OptionMenu,
    StringVar,
    Text,
    filedialog,
    messagebox,
)
from typing import Any, Dict, Optional

import qrcode
import yaml
from dotenv import load_dotenv
from PIL import Image, ImageTk

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """GUI application for generating QR codes."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize QRCodeGenerator with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.current_qr_image: Optional[Image.Image] = None
        self._create_gui()

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

    def _create_gui(self) -> None:
        """Create and configure the GUI interface."""
        from tkinter import Tk

        self.root = Tk()
        self.root.title("QR Code Generator")
        window_width = self.config.get("window", {}).get("width", 600)
        window_height = self.config.get("window", {}).get("height", 700)
        self.root.geometry(f"{window_width}x{window_height}")

        # Main container
        main_frame = Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Type selection
        type_frame = Frame(main_frame)
        type_frame.pack(fill="x", pady=(0, 10))

        Label(
            type_frame, text="QR Code Type:", font=("Arial", 12, "bold")
        ).pack(anchor="w")

        self.qr_type = StringVar(value="text")
        type_options = ["text", "url", "contact"]
        type_menu = OptionMenu(type_frame, self.qr_type, *type_options)
        type_menu.pack(anchor="w", pady=5)
        self.qr_type.trace("w", self._on_type_change)

        # Input section
        input_frame = Frame(main_frame)
        input_frame.pack(fill="both", expand=True, pady=(0, 10))

        Label(
            input_frame, text="Input:", font=("Arial", 12, "bold")
        ).pack(anchor="w")

        # Text input (for text and URL)
        self.text_input_frame = Frame(input_frame)
        self.text_input_frame.pack(fill="x", pady=5)

        Label(self.text_input_frame, text="Text/URL:").pack(anchor="w")
        self.text_entry = Text(
            self.text_input_frame, height=3, wrap="word"
        )
        self.text_entry.pack(fill="x", pady=2)

        # Contact input fields
        self.contact_frame = Frame(input_frame)
        self.contact_frame.pack(fill="x", pady=5)

        Label(self.contact_frame, text="Name:").pack(anchor="w")
        self.name_entry = Entry(self.contact_frame)
        self.name_entry.pack(fill="x", pady=2)

        Label(self.contact_frame, text="Phone:").pack(anchor="w")
        self.phone_entry = Entry(self.contact_frame)
        self.phone_entry.pack(fill="x", pady=2)

        Label(self.contact_frame, text="Email:").pack(anchor="w")
        self.email_entry = Entry(self.contact_frame)
        self.email_entry.pack(fill="x", pady=2)

        Label(self.contact_frame, text="Organization:").pack(anchor="w")
        self.org_entry = Entry(self.contact_frame)
        self.org_entry.pack(fill="x", pady=2)

        # Initially show text input, hide contact
        self._show_text_input()

        # Generate button
        button_frame = Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        Button(
            button_frame,
            text="Generate QR Code",
            command=self._generate_qr_code,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5,
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=5)

        Button(
            button_frame,
            text="Save QR Code",
            command=self._save_qr_code,
            bg="#2196F3",
            fg="white",
            padx=10,
            pady=5,
        ).pack(side="left", padx=5)

        # QR Code display
        display_frame = Frame(main_frame)
        display_frame.pack(fill="both", expand=True, pady=(10, 0))

        Label(
            display_frame, text="QR Code Preview:", font=("Arial", 12, "bold")
        ).pack(anchor="w")

        self.qr_canvas = Canvas(
            display_frame, width=300, height=300, bg="white", relief="solid", borderwidth=2
        )
        self.qr_canvas.pack(pady=10)

        # Status label
        self.status_label = Label(
            main_frame, text="Ready to generate QR code", fg="gray"
        )
        self.status_label.pack(pady=5)

        logger.info("GUI initialized successfully")

    def _on_type_change(self, *args: Any) -> None:
        """Handle QR code type change."""
        qr_type = self.qr_type.get()
        if qr_type == "contact":
            self._show_contact_input()
        else:
            self._show_text_input()

    def _show_text_input(self) -> None:
        """Show text input, hide contact input."""
        self.text_input_frame.pack(fill="x", pady=5)
        self.contact_frame.pack_forget()

    def _show_contact_input(self) -> None:
        """Show contact input, hide text input."""
        self.contact_frame.pack(fill="x", pady=5)
        self.text_input_frame.pack_forget()

    def _format_vcard(self) -> str:
        """Format contact information as vCard.

        Returns:
            vCard formatted string.
        """
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        org = self.org_entry.get().strip()

        vcard = "BEGIN:VCARD\nVERSION:3.0\n"
        if name:
            vcard += f"FN:{name}\nN:{name};;;;\n"
        if phone:
            vcard += f"TEL:{phone}\n"
        if email:
            vcard += f"EMAIL:{email}\n"
        if org:
            vcard += f"ORG:{org}\n"
        vcard += "END:VCARD"

        return vcard

    def _generate_qr_code(self) -> None:
        """Generate QR code from input."""
        qr_type = self.qr_type.get()

        try:
            if qr_type == "contact":
                data = self._format_vcard()
                if not any(
                    [
                        self.name_entry.get().strip(),
                        self.phone_entry.get().strip(),
                        self.email_entry.get().strip(),
                    ]
                ):
                    messagebox.showwarning(
                        "Empty Fields",
                        "Please fill in at least one contact field.",
                    )
                    return
            else:
                data = self.text_entry.get("1.0", "end-1.0").strip()
                if not data:
                    messagebox.showwarning(
                        "Empty Input", "Please enter text or URL."
                    )
                    return

            # QR code configuration
            qr_config = self.config.get("qr_code", {})
            box_size = qr_config.get("box_size", 10)
            border = qr_config.get("border", 4)
            error_correction = qr_config.get("error_correction", "M")

            error_map = {
                "L": qrcode.constants.ERROR_CORRECT_L,
                "M": qrcode.constants.ERROR_CORRECT_M,
                "Q": qrcode.constants.ERROR_CORRECT_Q,
                "H": qrcode.constants.ERROR_CORRECT_H,
            }

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create image
            self.current_qr_image = qr.make_image(
                fill_color=qr_config.get("fill_color", "black"),
                back_color=qr_config.get("back_color", "white"),
            )

            # Resize for display
            display_size = 300
            img_resized = self.current_qr_image.resize(
                (display_size, display_size), Image.Resampling.LANCZOS
            )

            # Display on canvas
            self.qr_canvas.delete("all")
            photo = ImageTk.PhotoImage(img_resized)
            self.qr_canvas.create_image(
                display_size // 2, display_size // 2, image=photo
            )
            self.qr_canvas.image = photo

            self.status_label.config(
                text=f"QR code generated successfully ({qr_type})", fg="green"
            )
            logger.info(f"QR code generated: type={qr_type}")

        except Exception as e:
            error_msg = f"Error generating QR code: {e}"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg, exc_info=True)
            self.status_label.config(text="Error generating QR code", fg="red")

    def _save_qr_code(self) -> None:
        """Save QR code to file."""
        if not self.current_qr_image:
            messagebox.showwarning(
                "No QR Code", "Please generate a QR code first."
            )
            return

        try:
            default_dir = self.config.get("save", {}).get(
                "default_directory", "."
            )
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*"),
                ],
                initialdir=default_dir,
                title="Save QR Code",
            )

            if filename:
                # Save original size image
                self.current_qr_image.save(filename)
                self.status_label.config(
                    text=f"QR code saved to {Path(filename).name}", fg="green"
                )
                logger.info(f"QR code saved to {filename}")

        except Exception as e:
            error_msg = f"Error saving QR code: {e}"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg, exc_info=True)

    def run(self) -> None:
        """Start the GUI application main loop."""
        logger.info("Starting QR Code Generator application")
        self.root.mainloop()


def main() -> None:
    """Main entry point for the application."""
    import argparse

    parser = argparse.ArgumentParser(
        description="QR Code Generator - GUI application for generating QR codes"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = QRCodeGenerator(config_path=args.config)
        app.run()
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
