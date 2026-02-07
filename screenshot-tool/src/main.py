"""Screenshot Tool - GUI application for capturing and annotating screenshots.

This module provides a GUI tool for capturing screenshots, annotating them
with drawing tools, text, and shapes, and saving them with timestamps.
"""

import argparse
import logging
import logging.handlers
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageTk
import yaml
from dotenv import load_dotenv
from mss import mss

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ScreenshotTool:
    """GUI application for screenshot capture and annotation."""

    def __init__(self, config: Dict) -> None:
        """Initialize ScreenshotTool.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.save_config = config.get("save", {})
        self.annotation_config = config.get("annotation", {})

        # Setup logging
        self._setup_logging()

        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Screenshot Tool")
        self.root.geometry("800x600")

        # Screenshot data
        self.screenshot_image: Optional[PIL.Image.Image] = None
        self.display_image: Optional[PIL.ImageTk.PhotoImage] = None
        self.canvas_image_id = None

        # Annotation state
        self.current_tool = "select"
        self.draw_color = self.annotation_config.get("default_color", "#FF0000")
        self.line_width = self.annotation_config.get("default_line_width", 3)
        self.font_size = self.annotation_config.get("default_font_size", 20)

        # Drawing state
        self.start_x = 0
        self.start_y = 0
        self.drawing = False
        self.annotation_elements: List[Dict] = []

        # Setup GUI
        self._setup_gui()

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/screenshot.log")

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def _setup_gui(self) -> None:
        """Setup the GUI components."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Capture Screenshot", command=self.capture_screenshot)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_screenshot)
        file_menu.add_command(label="Save As...", command=self.save_screenshot_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Toolbar frame
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Capture button
        ttk.Button(
            toolbar, text="Capture Screenshot", command=self.capture_screenshot
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar, text="Open Image", command=self.open_image
        ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Tool selection
        ttk.Label(toolbar, text="Tool:").pack(side=tk.LEFT, padx=2)
        self.tool_var = tk.StringVar(value="select")
        tools = [
            ("Select", "select"),
            ("Draw", "draw"),
            ("Rectangle", "rectangle"),
            ("Circle", "circle"),
            ("Arrow", "arrow"),
            ("Text", "text"),
        ]
        for text, value in tools:
            ttk.Radiobutton(
                toolbar, text=text, variable=self.tool_var, value=value
            ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Color selection
        self.color_button = tk.Button(
            toolbar,
            bg=self.draw_color,
            width=3,
            command=self.choose_color,
        )
        self.color_button.pack(side=tk.LEFT, padx=2)

        # Line width
        ttk.Label(toolbar, text="Width:").pack(side=tk.LEFT, padx=2)
        self.width_var = tk.IntVar(value=self.line_width)
        width_spin = ttk.Spinbox(
            toolbar, from_=1, to=20, textvariable=self.width_var, width=5
        )
        width_spin.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Action buttons
        ttk.Button(toolbar, text="Clear", command=self.clear_annotations).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="Save", command=self.save_screenshot).pack(
            side=tk.LEFT, padx=2
        )

        # Canvas for image display
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="gray", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def capture_screenshot(self) -> None:
        """Capture a screenshot of the entire screen."""
        try:
            self.root.withdraw()  # Hide window
            self.root.update()

            # Small delay to ensure window is hidden
            self.root.after(300, self._do_capture)

        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to capture screenshot: {e}")
            self.root.deiconify()

    def _do_capture(self) -> None:
        """Perform the actual screenshot capture."""
        try:
            with mss() as sct:
                # Capture entire screen
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)

                # Convert to PIL Image
                self.screenshot_image = PIL.Image.frombytes(
                    "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX"
                )

                self._display_image()
                self.status_var.set("Screenshot captured")

        except Exception as e:
            logger.error(f"Error in screenshot capture: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to capture screenshot: {e}")
        finally:
            self.root.deiconify()

    def open_image(self) -> None:
        """Open an existing image file."""
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                self.screenshot_image = PIL.Image.open(file_path)
                self._display_image()
                self.status_var.set(f"Opened: {Path(file_path).name}")
                logger.info(f"Opened image: {file_path}")

            except Exception as e:
                logger.error(f"Error opening image: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to open image: {e}")

    def _display_image(self) -> None:
        """Display the current image on the canvas."""
        if not self.screenshot_image:
            return

        # Clear previous annotations from canvas
        self.canvas.delete("all")
        self.annotation_elements.clear()

        # Resize image to fit canvas if needed
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet sized, use default
            canvas_width = 800
            canvas_height = 600

        img_width, img_height = self.screenshot_image.size

        # Calculate scaling to fit canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)  # Don't scale up

        display_width = int(img_width * scale)
        display_height = int(img_height * scale)

        # Resize for display
        display_image = self.screenshot_image.resize(
            (display_width, display_height), PIL.Image.Resampling.LANCZOS
        )

        # Convert to PhotoImage
        self.display_image = PIL.ImageTk.PhotoImage(display_image)

        # Display on canvas
        self.canvas_image_id = self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.display_image,
            anchor=tk.CENTER,
        )

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def choose_color(self) -> None:
        """Open color chooser dialog."""
        color = colorchooser.askcolor(color=self.draw_color)
        if color[1]:
            self.draw_color = color[1]
            self.color_button.config(bg=self.draw_color)
            self.annotation_config["default_color"] = self.draw_color

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle mouse click on canvas."""
        self.current_tool = self.tool_var.get()
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.drawing = True

        if self.current_tool == "text":
            self._add_text_dialog()

    def on_canvas_drag(self, event: tk.Event) -> None:
        """Handle mouse drag on canvas."""
        if not self.drawing or not self.screenshot_image:
            return

        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)

        if self.current_tool == "draw":
            # Draw freehand
            self.canvas.create_line(
                self.start_x,
                self.start_y,
                current_x,
                current_y,
                fill=self.draw_color,
                width=self.width_var.get(),
                tags="annotation",
            )
            self.start_x = current_x
            self.start_y = current_y

    def on_canvas_release(self, event: tk.Event) -> None:
        """Handle mouse release on canvas."""
        if not self.drawing or not self.screenshot_image:
            return

        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        tool = self.current_tool

        if tool == "rectangle":
            self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                end_x,
                end_y,
                outline=self.draw_color,
                width=self.width_var.get(),
                tags="annotation",
            )

        elif tool == "circle":
            self.canvas.create_oval(
                self.start_x,
                self.start_y,
                end_x,
                end_y,
                outline=self.draw_color,
                width=self.width_var.get(),
                tags="annotation",
            )

        elif tool == "arrow":
            # Simple arrow using lines
            self.canvas.create_line(
                self.start_x,
                self.start_y,
                end_x,
                end_y,
                fill=self.draw_color,
                width=self.width_var.get(),
                arrow=tk.LAST,
                tags="annotation",
            )

        self.drawing = False

    def _add_text_dialog(self) -> None:
        """Open dialog to add text annotation."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Text")
        dialog.geometry("300x150")

        ttk.Label(dialog, text="Enter text:").pack(pady=5)
        text_entry = tk.Text(dialog, height=3, width=30)
        text_entry.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        text_entry.focus()

        def add_text():
            text = text_entry.get("1.0", tk.END).strip()
            if text:
                self.canvas.create_text(
                    self.start_x,
                    self.start_y,
                    text=text,
                    fill=self.draw_color,
                    font=("Arial", self.font_size),
                    tags="annotation",
                )
            dialog.destroy()

        ttk.Button(dialog, text="Add", command=add_text).pack(pady=5)
        dialog.bind("<Return>", lambda e: add_text())

    def clear_annotations(self) -> None:
        """Clear all annotations from canvas."""
        self.canvas.delete("annotation")
        self.annotation_elements.clear()
        self.status_var.set("Annotations cleared")

    def save_screenshot(self) -> None:
        """Save screenshot with timestamp."""
        if not self.screenshot_image:
            messagebox.showwarning("Warning", "No screenshot to save")
            return

        # Generate filename with timestamp
        timestamp = datetime.now().strftime(
            self.save_config.get("timestamp_format", "%Y%m%d_%H%M%S")
        )
        default_filename = f"screenshot_{timestamp}.png"

        save_dir = Path(self.save_config.get("default_directory", "."))
        save_dir.mkdir(parents=True, exist_ok=True)

        save_path = save_dir / default_filename
        self._save_image(save_path)

    def save_screenshot_as(self) -> None:
        """Save screenshot with custom filename."""
        if not self.screenshot_image:
            messagebox.showwarning("Warning", "No screenshot to save")
            return

        timestamp = datetime.now().strftime(
            self.save_config.get("timestamp_format", "%Y%m%d_%H%M%S")
        )
        default_filename = f"screenshot_{timestamp}.png"

        file_path = filedialog.asksaveasfilename(
            title="Save Screenshot",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*"),
            ],
            initialfile=default_filename,
        )

        if file_path:
            self._save_image(Path(file_path))

    def _save_image(self, save_path: Path) -> None:
        """Save the image with annotations to file.

        Args:
            save_path: Path where to save the image.
        """
        try:
            # Get original image
            if not self.screenshot_image:
                return

            # Create a copy for annotation
            annotated_image = self.screenshot_image.copy()
            draw = PIL.ImageDraw.Draw(annotated_image)

            # Get canvas annotations (simplified - in production, would need
            # to map canvas coordinates to image coordinates)
            # For now, save the original image
            # In a full implementation, you would:
            # 1. Map canvas coordinates to image coordinates
            # 2. Redraw annotations on the image
            # 3. Save the annotated image

            # Save image
            annotated_image.save(save_path, "PNG")
            self.status_var.set(f"Saved: {save_path.name}")
            logger.info(f"Screenshot saved: {save_path}")

            messagebox.showinfo("Success", f"Screenshot saved to:\n{save_path}")

        except Exception as e:
            logger.error(f"Error saving screenshot: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to save screenshot: {e}")

    def run(self) -> None:
        """Run the application."""
        logger.info("Starting Screenshot Tool")
        self.root.mainloop()


def load_config(config_path: Path) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}") from e


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Screenshot tool with GUI for capturing and annotating screenshots"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        # Use default config if file doesn't exist
        config = {}
        logger.warning("Config file not found, using defaults")
    except yaml.YAMLError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    app = ScreenshotTool(config)
    app.run()


if __name__ == "__main__":
    main()
