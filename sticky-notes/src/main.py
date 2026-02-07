"""Sticky Notes Manager - Desktop sticky notes application.

This module provides a GUI application for creating and managing sticky notes
on the desktop with color coding and category organization.
"""

import logging
import logging.handlers
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import (
    Button,
    Canvas,
    Checkbutton,
    Entry,
    Frame,
    Label,
    Listbox,
    Menu,
    Message,
    OptionMenu,
    Scrollbar,
    StringVar,
    Text,
    Tk,
    Toplevel,
    ttk,
)
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class StickyNotesManager:
    """Manages sticky notes with GUI interface."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize StickyNotesManager with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_database()
        self.notes: Dict[int, Dict] = {}
        self.root: Optional[Tk] = None
        self.auto_save_thread: Optional[threading.Thread] = None
        self.auto_save_running = False

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
        if os.getenv("DATABASE_FILE"):
            config["database"]["file"] = os.getenv("DATABASE_FILE")
        if os.getenv("AUTO_SAVE_INTERVAL"):
            config["auto_save"]["interval"] = int(os.getenv("AUTO_SAVE_INTERVAL"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/sticky_notes.log")

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

    def _setup_database(self) -> None:
        """Set up SQLite database and create tables if needed."""
        db_file = self.config["database"]["file"]
        db_path = Path(db_file)
        if not db_path.is_absolute():
            project_root = Path(__file__).parent.parent
            db_path = project_root / db_file

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

        if self.config["database"].get("create_tables", True):
            self._create_tables()

        logger.info(f"Database initialized: {db_path}")

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                color TEXT,
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                position_x INTEGER DEFAULT 100,
                position_y INTEGER DEFAULT 100,
                width INTEGER,
                height INTEGER
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def _load_notes(self) -> None:
        """Load notes from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, content, color, category, created_at, updated_at,
                   position_x, position_y, width, height
            FROM notes
            ORDER BY updated_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        self.notes = {}
        for row in rows:
            note_id = row[0]
            self.notes[note_id] = {
                "id": note_id,
                "title": row[1],
                "content": row[2] or "",
                "color": row[3] or self.config["defaults"]["default_color"],
                "category": row[4] or self.config["defaults"]["default_category"],
                "created_at": row[5],
                "updated_at": row[6],
                "position_x": row[7] or 100,
                "position_y": row[8] or 100,
                "width": row[9] or self.config["defaults"]["width"],
                "height": row[10] or self.config["defaults"]["height"],
            }

        logger.info(f"Loaded {len(self.notes)} note(s) from database")

    def _save_note(
        self,
        note_id: Optional[int],
        title: str,
        content: str,
        color: str,
        category: str,
        position_x: int = 100,
        position_y: int = 100,
        width: int = 300,
        height: int = 200,
    ) -> int:
        """Save note to database.

        Args:
            note_id: Note ID (None for new note).
            title: Note title.
            content: Note content.
            color: Note color code.
            category: Note category.
            position_x: X position on screen.
            position_y: Y position on screen.
            width: Note width.
            height: Note height.

        Returns:
            Note ID.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        if note_id is None:
            # Insert new note
            cursor.execute("""
                INSERT INTO notes 
                (title, content, color, category, created_at, updated_at,
                 position_x, position_y, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, content, color, category, now, now, position_x, position_y, width, height))
            note_id = cursor.lastrowid
        else:
            # Update existing note
            cursor.execute("""
                UPDATE notes
                SET title = ?, content = ?, color = ?, category = ?,
                    updated_at = ?, position_x = ?, position_y = ?,
                    width = ?, height = ?
                WHERE id = ?
            """, (title, content, color, category, now, position_x, position_y, width, height, note_id))

        conn.commit()
        conn.close()

        logger.info(f"Saved note: {note_id} - {title}")
        return note_id

    def _delete_note(self, note_id: int) -> bool:
        """Delete note from database.

        Args:
            note_id: Note ID to delete.

        Returns:
            True if deleted successfully.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted note: {note_id}")
            if note_id in self.notes:
                del self.notes[note_id]

        return deleted

    def _auto_save_loop(self) -> None:
        """Auto-save loop for periodic saving."""
        interval = self.config.get("auto_save", {}).get("interval", 5)

        while self.auto_save_running:
            time.sleep(interval)
            if self.auto_save_running:
                try:
                    # Auto-save is handled by individual note windows
                    # This thread can be used for other periodic tasks
                    pass
                except Exception as e:
                    logger.error(f"Error in auto-save loop: {e}")

    def _create_note_editor(
        self, note_id: Optional[int] = None, parent_window=None
    ) -> None:
        """Create note editor window.

        Args:
            note_id: Note ID to edit (None for new note).
            parent_window: Parent window reference.
        """
        editor = Toplevel(parent_window or self.root)
        editor.title("Edit Note" if note_id else "New Note")
        editor.geometry("500x400")

        # Get note data if editing
        note_data = self.notes.get(note_id) if note_id else None

        # Title field
        title_frame = Frame(editor)
        title_frame.pack(fill="x", padx=10, pady=5)
        Label(title_frame, text="Title:").pack(side="left")
        title_var = StringVar(value=note_data["title"] if note_data else "")
        title_entry = Entry(title_frame, textvariable=title_var, width=40)
        title_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Content field
        content_frame = Frame(editor)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        Label(content_frame, text="Content:").pack(anchor="w")
        content_text = Text(content_frame, wrap="word", height=10)
        content_text.pack(fill="both", expand=True)
        if note_data:
            content_text.insert("1.0", note_data["content"])

        # Color selection
        color_frame = Frame(editor)
        color_frame.pack(fill="x", padx=10, pady=5)
        Label(color_frame, text="Color:").pack(side="left")
        color_var = StringVar(
            value=note_data["color"] if note_data else self.config["defaults"]["default_color"]
        )
        color_menu = OptionMenu(
            color_frame,
            color_var,
            *[color["code"] for color in self.config["colors"]],
        )
        color_menu.pack(side="left", padx=5)

        # Category selection
        category_frame = Frame(editor)
        category_frame.pack(fill="x", padx=10, pady=5)
        Label(category_frame, text="Category:").pack(side="left")
        category_var = StringVar(
            value=note_data["category"] if note_data else self.config["defaults"]["default_category"]
        )
        category_menu = OptionMenu(
            category_frame,
            category_var,
            *self.config["categories"],
        )
        category_menu.pack(side="left", padx=5)

        # Buttons
        button_frame = Frame(editor)
        button_frame.pack(fill="x", padx=10, pady=10)

        def save_note():
            title = title_var.get().strip()
            content = content_text.get("1.0", "end-1c").strip()
            color = color_var.get()
            category = category_var.get()

            if not title:
                # Use first line of content as title if title is empty
                title = content.split("\n")[0][:50] if content else "Untitled Note"

            saved_id = self._save_note(
                note_id, title, content, color, category
            )

            # Update local notes dict
            self.notes[saved_id] = {
                "id": saved_id,
                "title": title,
                "content": content,
                "color": color,
                "category": category,
                "created_at": note_data["created_at"] if note_data else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "position_x": note_data.get("position_x", 100) if note_data else 100,
                "position_y": note_data.get("position_y", 100) if note_data else 100,
                "width": note_data.get("width", 300) if note_data else 300,
                "height": note_data.get("height", 200) if note_data else 200,
            }

            editor.destroy()
            self._refresh_note_list()

        def delete_note():
            if note_id:
                if self._delete_note(note_id):
                    editor.destroy()
                    self._refresh_note_list()

        Button(button_frame, text="Save", command=save_note).pack(side="left", padx=5)
        if note_id:
            Button(button_frame, text="Delete", command=delete_note, fg="red").pack(
                side="left", padx=5
            )
        Button(button_frame, text="Cancel", command=editor.destroy).pack(
            side="right", padx=5
        )

    def _refresh_note_list(self) -> None:
        """Refresh the note list display."""
        if not hasattr(self, "note_listbox"):
            return

        self.note_listbox.delete(0, "end")
        self.notes = {}
        self._load_notes()

        for note_id, note in self.notes.items():
            display_text = f"[{note['category']}] {note['title']}"
            self.note_listbox.insert("end", display_text)
            self.note_listbox.itemconfig("end", {"bg": note["color"]})

    def _create_main_window(self) -> None:
        """Create main application window."""
        self.root = Tk()
        gui_config = self.config.get("gui", {})
        self.root.title(gui_config.get("window_title", "Sticky Notes Manager"))
        self.root.geometry(
            f"{gui_config.get('window_width', 800)}x{gui_config.get('window_height', 600)}"
        )

        # Menu bar
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Note", command=lambda: self._create_note_editor())
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Main frame
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Note list
        left_panel = Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        Label(left_panel, text="Notes", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))

        # Filter frame
        filter_frame = Frame(left_panel)
        filter_frame.pack(fill="x", pady=(0, 5))

        Label(filter_frame, text="Category:").pack(side="left", padx=(0, 5))
        self.filter_var = StringVar(value="All")
        filter_menu = OptionMenu(
            filter_frame, self.filter_var, "All", *self.config["categories"], command=self._filter_notes
        )
        filter_menu.pack(side="left")

        # Note list with scrollbar
        list_frame = Frame(left_panel)
        list_frame.pack(fill="both", expand=True)

        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.note_listbox = Listbox(
            list_frame, yscrollcommand=scrollbar.set, selectmode="single"
        )
        self.note_listbox.pack(side="left", fill="both", expand=True)
        self.note_listbox.bind("<Double-Button-1>", self._on_note_double_click)
        self.note_listbox.bind("<<ListboxSelect>>", self._on_note_select)
        scrollbar.config(command=self.note_listbox.yview)

        # Buttons
        button_frame = Frame(left_panel)
        button_frame.pack(fill="x", pady=(10, 0))

        Button(button_frame, text="New Note", command=lambda: self._create_note_editor()).pack(
            side="left", padx=2
        )
        Button(button_frame, text="Edit", command=self._edit_selected_note).pack(
            side="left", padx=2
        )
        Button(button_frame, text="Delete", command=self._delete_selected_note, fg="red").pack(
            side="left", padx=2
        )

        # Right panel - Note preview
        right_panel = Frame(main_frame, relief="sunken", borderwidth=2)
        right_panel.pack(side="right", fill="both", expand=True)

        Label(right_panel, text="Note Preview", font=("Arial", 12, "bold")).pack(
            anchor="w", pady=5, padx=5
        )

        self.preview_frame = Frame(right_panel)
        self.preview_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Initialize filter
        self._current_filter = "All"

        # Load and display notes
        self._load_notes()
        self._refresh_note_list()

        logger.info("Main window created")

    def _filter_notes(self, category: str) -> None:
        """Filter notes by category.

        Args:
            category: Category to filter by ("All" for all categories).
        """
        self._current_filter = category
        self.note_listbox.delete(0, "end")

        for note_id, note in self.notes.items():
            if category == "All" or note["category"] == category:
                display_text = f"[{note['category']}] {note['title']}"
                self.note_listbox.insert("end", display_text)
                self.note_listbox.itemconfig("end", {"bg": note["color"]})

    def _on_note_double_click(self, event) -> None:
        """Handle double-click on note list item.

        Args:
            event: Mouse event.
        """
        self._edit_selected_note()

    def _on_note_select(self, event) -> None:
        """Handle selection change in note list.

        Args:
            event: Selection event.
        """
        selection = self.note_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        note_list = list(self.notes.values())
        if self._current_filter != "All":
            note_list = [n for n in note_list if n["category"] == self._current_filter]

        if index < len(note_list):
            note = note_list[index]
            self._show_note_preview(note["id"])

    def _edit_selected_note(self) -> None:
        """Edit the selected note."""
        selection = self.note_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        note_list = list(self.notes.values())
        if category_filter := getattr(self, "_current_filter", "All"):
            if category_filter != "All":
                note_list = [n for n in note_list if n["category"] == category_filter]

        if index < len(note_list):
            note = note_list[index]
            self._create_note_editor(note["id"])

    def _delete_selected_note(self) -> None:
        """Delete the selected note."""
        selection = self.note_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        note_list = list(self.notes.values())
        if category_filter := getattr(self, "_current_filter", "All"):
            if category_filter != "All":
                note_list = [n for n in note_list if n["category"] == category_filter]

        if index < len(note_list):
            note = note_list[index]
            if self._delete_note(note["id"]):
                self._refresh_note_list()
                # Clear preview
                for widget in self.preview_frame.winfo_children():
                    widget.destroy()

    def _show_note_preview(self, note_id: int) -> None:
        """Show note preview in right panel.

        Args:
            note_id: Note ID to preview.
        """
        if note_id not in self.notes:
            return

        note = self.notes[note_id]

        # Clear preview
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # Create preview container
        preview_container = Frame(self.preview_frame, bg=note["color"], relief="raised", borderwidth=2)
        preview_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Title
        title_label = Label(
            preview_container,
            text=note["title"],
            font=("Arial", 12, "bold"),
            bg=note["color"],
            wraplength=300,
        )
        title_label.pack(pady=5, padx=5, anchor="w")

        # Content
        content_frame = Frame(preview_container, bg=note["color"])
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        content_text = Text(
            content_frame, wrap="word", height=8, bg=note["color"], relief="flat", borderwidth=0
        )
        content_text.pack(fill="both", expand=True)
        content_text.insert("1.0", note["content"])
        content_text.config(state="disabled")

        # Category and metadata
        meta_frame = Frame(preview_container, bg=note["color"])
        meta_frame.pack(fill="x", padx=5, pady=5)

        Label(
            meta_frame,
            text=f"Category: {note['category']}",
            bg=note["color"],
            font=("Arial", 8),
        ).pack(side="left")

        if note.get("updated_at"):
            Label(
                meta_frame,
                text=f"Updated: {note['updated_at'][:10]}",
                bg=note["color"],
                font=("Arial", 8),
            ).pack(side="right")

    def run(self) -> None:
        """Run the sticky notes application."""
        self._create_main_window()

        # Start auto-save thread if enabled
        if self.config.get("auto_save", {}).get("enabled", True):
            self.auto_save_running = True
            self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
            self.auto_save_thread.start()

        logger.info("Starting sticky notes application")
        self.root.mainloop()

        # Stop auto-save thread
        self.auto_save_running = False
        logger.info("Sticky notes application closed")


def main() -> int:
    """Main entry point for sticky notes manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Sticky Notes Manager")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        manager = StickyNotesManager(config_path=args.config)
        manager.run()
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
