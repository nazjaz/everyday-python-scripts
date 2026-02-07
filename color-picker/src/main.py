"""Color Picker - Simple GUI application for color selection and palette management.

This module provides a graphical user interface for selecting colors, viewing
hex codes, and managing color palettes. Users can pick colors, save palettes,
and load previously saved color collections.
"""

import json
import logging
import logging.handlers
from pathlib import Path
from tkinter import (
    Button,
    Canvas,
    Entry,
    Frame,
    Label,
    Listbox,
    Scrollbar,
    Tk,
    colorchooser,
    messagebox,
)
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ColorPicker:
    """GUI application for color selection and palette management."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ColorPicker with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.current_color: Optional[str] = None
        self.palette: List[Dict[str, str]] = []
        self.palette_file = Path(
            self.config.get("palette", {}).get(
                "save_file", "palettes.json"
            )
        )
        self._load_palettes()
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
        self.root = Tk()
        self.root.title("Color Picker")
        window_width = self.config.get("window", {}).get("width", 600)
        window_height = self.config.get("window", {}).get("height", 500)
        self.root.geometry(f"{window_width}x{window_height}")

        # Main container
        main_frame = Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Color selection section
        color_frame = Frame(main_frame)
        color_frame.pack(fill="x", pady=(0, 10))

        Label(
            color_frame, text="Selected Color:", font=("Arial", 12, "bold")
        ).pack(anchor="w")

        # Color display canvas
        self.color_canvas = Canvas(
            color_frame, width=200, height=100, relief="solid", borderwidth=2
        )
        self.color_canvas.pack(pady=5)

        # Hex code display
        hex_frame = Frame(color_frame)
        hex_frame.pack(fill="x", pady=5)

        Label(hex_frame, text="Hex Code:").pack(side="left")
        self.hex_entry = Entry(hex_frame, width=10, font=("Courier", 12))
        self.hex_entry.pack(side="left", padx=5)
        self.hex_entry.bind("<KeyRelease>", self._on_hex_change)

        # RGB display
        rgb_frame = Frame(color_frame)
        rgb_frame.pack(fill="x", pady=5)

        Label(rgb_frame, text="RGB:").pack(side="left")
        self.rgb_label = Label(
            rgb_frame, text="(0, 0, 0)", font=("Courier", 10)
        )
        self.rgb_label.pack(side="left", padx=5)

        # Buttons frame
        button_frame = Frame(color_frame)
        button_frame.pack(fill="x", pady=10)

        Button(
            button_frame,
            text="Pick Color",
            command=self._pick_color,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5,
        ).pack(side="left", padx=5)

        Button(
            button_frame,
            text="Add to Palette",
            command=self._add_to_palette,
            bg="#2196F3",
            fg="white",
            padx=10,
            pady=5,
        ).pack(side="left", padx=5)

        # Palette section
        palette_frame = Frame(main_frame)
        palette_frame.pack(fill="both", expand=True)

        Label(
            palette_frame,
            text="Color Palette:",
            font=("Arial", 12, "bold"),
        ).pack(anchor="w")

        # Palette listbox with scrollbar
        listbox_frame = Frame(palette_frame)
        listbox_frame.pack(fill="both", expand=True, pady=5)

        scrollbar = Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")

        self.palette_listbox = Listbox(
            listbox_frame, yscrollcommand=scrollbar.set, height=8
        )
        self.palette_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.palette_listbox.yview)
        self.palette_listbox.bind("<Double-Button-1>", self._select_from_palette)

        # Palette management buttons
        palette_button_frame = Frame(palette_frame)
        palette_button_frame.pack(fill="x", pady=5)

        Button(
            palette_button_frame,
            text="Remove Selected",
            command=self._remove_from_palette,
            bg="#f44336",
            fg="white",
            padx=10,
            pady=5,
        ).pack(side="left", padx=5)

        Button(
            palette_button_frame,
            text="Clear Palette",
            command=self._clear_palette,
            bg="#FF9800",
            fg="white",
            padx=10,
            pady=5,
        ).pack(side="left", padx=5)

        Button(
            palette_button_frame,
            text="Save Palette",
            command=self._save_palette,
            bg="#9C27B0",
            fg="white",
            padx=10,
            pady=5,
        ).pack(side="left", padx=5)

        Button(
            palette_button_frame,
            text="Load Palette",
            command=self._load_palette,
            bg="#607D8B",
            fg="white",
            padx=10,
            pady=5,
        ).pack(side="left", padx=5)

        self._update_palette_display()

        logger.info("GUI initialized successfully")

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (with or without #).

        Returns:
            Tuple of (R, G, B) values.
        """
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return (0, 0, 0)
        try:
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return (0, 0, 0)

    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB values to hex color string.

        Args:
            r: Red value (0-255).
            g: Green value (0-255).
            b: Blue value (0-255).

        Returns:
            Hex color string with # prefix.
        """
        return f"#{r:02x}{g:02x}{b:02x}".upper()

    def _update_color_display(self, hex_color: str) -> None:
        """Update color display canvas and hex/RGB labels.

        Args:
            hex_color: Hex color string to display.
        """
        self.current_color = hex_color
        self.color_canvas.delete("all")
        self.color_canvas.create_rectangle(
            0, 0, 200, 100, fill=hex_color, outline="black"
        )

        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, hex_color)

        rgb = self._hex_to_rgb(hex_color)
        self.rgb_label.config(text=f"({rgb[0]}, {rgb[1]}, {rgb[2]})")

        logger.debug(f"Color display updated: {hex_color}")

    def _pick_color(self) -> None:
        """Open color picker dialog and update display."""
        color = colorchooser.askcolor(title="Pick a Color")
        if color[1]:
            hex_color = color[1].upper()
            self._update_color_display(hex_color)
            logger.info(f"Color picked: {hex_color}")

    def _on_hex_change(self, event: Any) -> None:
        """Handle hex code entry change.

        Args:
            event: Tkinter event object.
        """
        hex_value = self.hex_entry.get().strip()
        if hex_value and not hex_value.startswith("#"):
            hex_value = "#" + hex_value

        if len(hex_value) == 7 and hex_value.startswith("#"):
            try:
                self._update_color_display(hex_value.upper())
            except Exception as e:
                logger.warning(f"Invalid hex color entered: {hex_value} - {e}")

    def _add_to_palette(self) -> None:
        """Add current color to palette."""
        if not self.current_color:
            messagebox.showwarning(
                "No Color Selected", "Please select a color first."
            )
            return

        color_entry = {
            "hex": self.current_color,
            "rgb": str(self._hex_to_rgb(self.current_color)),
        }
        self.palette.append(color_entry)
        self._update_palette_display()
        logger.info(f"Added color to palette: {self.current_color}")

    def _remove_from_palette(self) -> None:
        """Remove selected color from palette."""
        selection = self.palette_listbox.curselection()
        if not selection:
            messagebox.showwarning(
                "No Selection", "Please select a color to remove."
            )
            return

        index = selection[0]
        removed_color = self.palette.pop(index)
        self._update_palette_display()
        logger.info(f"Removed color from palette: {removed_color['hex']}")

    def _clear_palette(self) -> None:
        """Clear all colors from palette."""
        if not self.palette:
            return

        if messagebox.askyesno(
            "Clear Palette", "Are you sure you want to clear the palette?"
        ):
            self.palette.clear()
            self._update_palette_display()
            logger.info("Palette cleared")

    def _select_from_palette(self, event: Any) -> None:
        """Select color from palette on double-click.

        Args:
            event: Tkinter event object.
        """
        selection = self.palette_listbox.curselection()
        if selection:
            index = selection[0]
            color_entry = self.palette[index]
            self._update_color_display(color_entry["hex"])
            logger.debug(f"Selected color from palette: {color_entry['hex']}")

    def _update_palette_display(self) -> None:
        """Update palette listbox display."""
        self.palette_listbox.delete(0, "end")
        for i, color_entry in enumerate(self.palette):
            display_text = f"{i+1}. {color_entry['hex']} - RGB{color_entry['rgb']}"
            self.palette_listbox.insert("end", display_text)

    def _save_palette(self) -> None:
        """Save current palette to file."""
        if not self.palette:
            messagebox.showwarning(
                "Empty Palette", "Palette is empty. Nothing to save."
            )
            return

        try:
            # Load existing palettes
            palettes_data = self._load_palettes_data()

            # Get palette name from user
            palette_name = self._get_palette_name()
            if not palette_name:
                return

            palettes_data["palettes"][palette_name] = {
                "colors": self.palette,
            }

            # Save to file
            self.palette_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.palette_file, "w", encoding="utf-8") as f:
                json.dump(palettes_data, f, indent=2)

            messagebox.showinfo(
                "Palette Saved", f"Palette '{palette_name}' saved successfully."
            )
            logger.info(f"Palette saved: {palette_name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save palette: {e}")
            logger.error(f"Failed to save palette: {e}", exc_info=True)

    def _load_palette(self) -> None:
        """Load a saved palette from file."""
        try:
            palettes_data = self._load_palettes_data()
            available_palettes = list(palettes_data.get("palettes", {}).keys())

            if not available_palettes:
                messagebox.showinfo(
                    "No Palettes", "No saved palettes found."
                )
                return

            # Simple selection dialog
            selected = self._select_palette_name(available_palettes)
            if not selected:
                return

            self.palette = palettes_data["palettes"][selected]["colors"].copy()
            self._update_palette_display()
            messagebox.showinfo(
                "Palette Loaded",
                f"Palette '{selected}' loaded successfully.",
            )
            logger.info(f"Palette loaded: {selected}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load palette: {e}")
            logger.error(f"Failed to load palette: {e}", exc_info=True)

    def _load_palettes(self) -> None:
        """Load palettes from file on startup."""
        try:
            if self.palette_file.exists():
                palettes_data = self._load_palettes_data()
                default_palette = palettes_data.get("default_palette")
                if default_palette:
                    self.palette = (
                        palettes_data["palettes"][default_palette]["colors"].copy()
                    )
                    logger.info(f"Loaded default palette: {default_palette}")
        except Exception as e:
            logger.warning(f"Failed to load palettes on startup: {e}")

    def _load_palettes_data(self) -> dict:
        """Load palettes data from JSON file.

        Returns:
            Dictionary containing palettes data.
        """
        if self.palette_file.exists():
            try:
                with open(self.palette_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading palettes file: {e}")
        return {"palettes": {}, "default_palette": None}

    def _get_palette_name(self) -> Optional[str]:
        """Get palette name from user via dialog.

        Returns:
            Palette name string or None if cancelled.
        """
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "Palette Name", "Enter a name for this palette:"
        )
        return name.strip() if name else None

    def _select_palette_name(self, available: List[str]) -> Optional[str]:
        """Select palette name from list via dialog.

        Args:
            available: List of available palette names.

        Returns:
            Selected palette name or None if cancelled.
        """
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "Load Palette",
            f"Enter palette name:\nAvailable: {', '.join(available)}",
        )
        return name.strip() if name and name in available else None

    def run(self) -> None:
        """Start the GUI application main loop."""
        logger.info("Starting Color Picker application")
        self.root.mainloop()


def main() -> None:
    """Main entry point for the application."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Color Picker - GUI application for color selection "
        "and palette management"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = ColorPicker(config_path=args.config)
        app.run()
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
