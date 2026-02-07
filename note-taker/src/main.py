"""Note Taker - Simple note-taking application with GUI.

This module provides a GUI-based note-taking application with markdown
formatting support, tags, search functionality, and export options.
"""

import json
import logging
import logging.handlers
import os
import re
from datetime import datetime
from pathlib import Path
from tkinter import (
    END,
    INSERT,
    Button,
    Entry,
    Frame,
    Label,
    Listbox,
    Menu,
    Message,
    Scrollbar,
    Text,
    Tk,
    filedialog,
    messagebox,
    ttk,
)
from typing import Any, Dict, List, Optional, Set

import markdown
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class NoteTakerApp:
    """GUI application for note-taking with markdown support."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize NoteTakerApp with configuration.

        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.data_directory = self._get_data_directory()
        self.notes: Dict[str, Dict[str, Any]] = {}
        self.current_note_id: Optional[str] = None
        self.filtered_notes: List[str] = []

        # Initialize GUI
        self.root = Tk()
        self._setup_gui()
        self._load_notes()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.
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
            # Use default configuration
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {
                "data": {"directory": "data"},
                "app": {"title": "Note Taker", "window_size": "1000x700"},
                "logging": {"level": "INFO", "file": "logs/note_taker.log"},
            }

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables
        if os.getenv("DATA_DIRECTORY"):
            config["data"]["directory"] = os.getenv("DATA_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/note_taker.log")

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
            maxBytes=10485760,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        logger.info("Logging configured successfully")

    def _get_data_directory(self) -> Path:
        """Get data directory path.

        Returns:
            Path to data directory.
        """
        data_dir = self.config.get("data", {}).get("directory", "data")
        data_path = Path(data_dir)

        if not data_path.is_absolute():
            project_root = Path(__file__).parent.parent
            data_path = project_root / data_dir

        data_path.mkdir(parents=True, exist_ok=True)
        return data_path

    def _setup_gui(self) -> None:
        """Set up the GUI interface."""
        app_title = self.config.get("app", {}).get("title", "Note Taker")
        self.root.title(app_title)

        window_size = self.config.get("app", {}).get("window_size", "1000x700")
        self.root.geometry(window_size)

        # Create menu bar
        self._create_menu_bar()

        # Main container
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Note list and search
        left_panel = Frame(main_frame, width=250)
        left_panel.pack(side="left", fill="both", padx=(0, 5))

        # Search frame
        search_frame = Frame(left_panel)
        search_frame.pack(fill="x", pady=(0, 5))

        Label(search_frame, text="Search:").pack(side="left")
        self.search_entry = Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Tags filter
        tags_frame = Frame(left_panel)
        tags_frame.pack(fill="x", pady=(0, 5))

        Label(tags_frame, text="Filter by tag:").pack(anchor="w")
        self.tag_filter = ttk.Combobox(tags_frame, state="readonly")
        self.tag_filter.pack(fill="x")
        self.tag_filter.bind("<<ComboboxSelected>>", self._on_tag_filter)

        # Note list
        list_frame = Frame(left_panel)
        list_frame.pack(fill="both", expand=True)

        Label(list_frame, text="Notes:").pack(anchor="w")
        scrollbar_list = Scrollbar(list_frame)
        scrollbar_list.pack(side="right", fill="y")

        self.note_listbox = Listbox(list_frame, yscrollcommand=scrollbar_list.set)
        self.note_listbox.pack(side="left", fill="both", expand=True)
        self.note_listbox.bind("<<ListboxSelect>>", self._on_note_select)
        scrollbar_list.config(command=self.note_listbox.yview)

        # Right panel - Note editor
        right_panel = Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # Note title
        title_frame = Frame(right_panel)
        title_frame.pack(fill="x", pady=(0, 5))

        Label(title_frame, text="Title:").pack(side="left")
        self.title_entry = Entry(title_frame)
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Tags entry
        tags_entry_frame = Frame(right_panel)
        tags_entry_frame.pack(fill="x", pady=(0, 5))

        Label(tags_entry_frame, text="Tags (comma-separated):").pack(side="left")
        self.tags_entry = Entry(tags_entry_frame)
        self.tags_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Editor tabs
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill="both", expand=True)

        # Edit tab
        edit_frame = Frame(notebook)
        notebook.add(edit_frame, text="Edit")

        scrollbar_edit = Scrollbar(edit_frame)
        scrollbar_edit.pack(side="right", fill="y")

        self.content_text = Text(edit_frame, yscrollcommand=scrollbar_edit.set, wrap="word")
        self.content_text.pack(side="left", fill="both", expand=True)
        scrollbar_edit.config(command=self.content_text.yview)

        # Preview tab
        preview_frame = Frame(notebook)
        notebook.add(preview_frame, text="Preview")

        scrollbar_preview = Scrollbar(preview_frame)
        scrollbar_preview.pack(side="right", fill="y")

        self.preview_text = Text(
            preview_frame, yscrollcommand=scrollbar_preview.set, wrap="word", state="disabled"
        )
        self.preview_text.pack(side="left", fill="both", expand=True)
        scrollbar_preview.config(command=self.preview_text.yview)

        # Bind content change for preview
        self.content_text.bind("<KeyRelease>", self._update_preview)

        # Buttons
        button_frame = Frame(right_panel)
        button_frame.pack(fill="x", pady=(5, 0))

        Button(button_frame, text="New Note", command=self._new_note).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Save", command=self._save_note).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Delete", command=self._delete_note).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Export", command=self._export_note).pack(side="left")

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Note", command=self._new_note)
        file_menu.add_command(label="Save", command=self._save_note)
        file_menu.add_separator()
        file_menu.add_command(label="Export...", command=self._export_note)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Delete Note", command=self._delete_note)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _generate_note_id(self) -> str:
        """Generate unique note ID.

        Returns:
            Unique note identifier.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"note_{timestamp}"

    def _load_notes(self) -> None:
        """Load notes from data directory."""
        notes_file = self.data_directory / "notes.json"

        if notes_file.exists():
            try:
                with open(notes_file, "r", encoding="utf-8") as f:
                    self.notes = json.load(f)
                logger.info(f"Loaded {len(self.notes)} note(s)")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading notes: {e}")
                self.notes = {}
        else:
            self.notes = {}

        self._refresh_note_list()

    def _save_notes(self) -> None:
        """Save notes to data directory."""
        notes_file = self.data_directory / "notes.json"

        try:
            with open(notes_file, "w", encoding="utf-8") as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.notes)} note(s)")
        except IOError as e:
            logger.error(f"Error saving notes: {e}")
            messagebox.showerror("Error", f"Failed to save notes: {e}")

    def _refresh_note_list(self) -> None:
        """Refresh the note list display."""
        self.note_listbox.delete(0, END)

        # Update tag filter
        all_tags = set()
        for note in self.notes.values():
            all_tags.update(note.get("tags", []))
        self.tag_filter["values"] = ["All"] + sorted(all_tags)
        if not self.tag_filter.get():
            self.tag_filter.set("All")

        # Filter notes
        search_term = self.search_entry.get().lower()
        selected_tag = self.tag_filter.get()

        self.filtered_notes = []
        for note_id, note in self.notes.items():
            # Search filter
            if search_term:
                title_match = search_term in note.get("title", "").lower()
                content_match = search_term in note.get("content", "").lower()
                tags_match = any(
                    search_term in tag.lower() for tag in note.get("tags", [])
                )
                if not (title_match or content_match or tags_match):
                    continue

            # Tag filter
            if selected_tag and selected_tag != "All":
                if selected_tag not in note.get("tags", []):
                    continue

            self.filtered_notes.append(note_id)
            title = note.get("title", "Untitled")
            self.note_listbox.insert(END, title)

    def _on_search(self, event: Any) -> None:
        """Handle search entry changes."""
        self._refresh_note_list()

    def _on_tag_filter(self, event: Any) -> None:
        """Handle tag filter changes."""
        self._refresh_note_list()

    def _on_note_select(self, event: Any) -> None:
        """Handle note selection from list."""
        selection = self.note_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.filtered_notes):
            note_id = self.filtered_notes[index]
            self._load_note(note_id)

    def _load_note(self, note_id: str) -> None:
        """Load note into editor.

        Args:
            note_id: Note identifier.
        """
        if note_id not in self.notes:
            return

        note = self.notes[note_id]
        self.current_note_id = note_id

        # Load title
        self.title_entry.delete(0, END)
        self.title_entry.insert(0, note.get("title", ""))

        # Load tags
        tags = note.get("tags", [])
        self.tags_entry.delete(0, END)
        self.tags_entry.insert(0, ", ".join(tags))

        # Load content
        self.content_text.delete("1.0", END)
        self.content_text.insert("1.0", note.get("content", ""))

        self._update_preview()

    def _new_note(self) -> None:
        """Create a new note."""
        self.current_note_id = None
        self.title_entry.delete(0, END)
        self.tags_entry.delete(0, END)
        self.content_text.delete("1.0", END)
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", END)
        self.preview_text.config(state="disabled")

    def _save_note(self) -> None:
        """Save current note."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Warning", "Please enter a title for the note.")
            return

        # Parse tags
        tags_str = self.tags_entry.get().strip()
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

        content = self.content_text.get("1.0", END).rstrip()

        # Create or update note
        if not self.current_note_id:
            self.current_note_id = self._generate_note_id()

        self.notes[self.current_note_id] = {
            "title": title,
            "content": content,
            "tags": tags,
            "created_at": self.notes.get(self.current_note_id, {}).get(
                "created_at", datetime.now().isoformat()
            ),
            "updated_at": datetime.now().isoformat(),
        }

        self._save_notes()
        self._refresh_note_list()
        messagebox.showinfo("Success", "Note saved successfully.")

    def _delete_note(self) -> None:
        """Delete current note."""
        if not self.current_note_id:
            messagebox.showwarning("Warning", "No note selected.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this note?"):
            del self.notes[self.current_note_id]
            self._save_notes()
            self._new_note()
            self._refresh_note_list()
            messagebox.showinfo("Success", "Note deleted successfully.")

    def _update_preview(self, event: Any = None) -> None:
        """Update markdown preview."""
        content = self.content_text.get("1.0", END)
        try:
            html = markdown.markdown(content, extensions=["extra", "codehilite"])
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", END)
            self.preview_text.insert("1.0", html)
            self.preview_text.config(state="disabled")
        except Exception as e:
            logger.error(f"Error updating preview: {e}")

    def _export_note(self) -> None:
        """Export current note."""
        if not self.current_note_id or self.current_note_id not in self.notes:
            messagebox.showwarning("Warning", "No note selected.")
            return

        note = self.notes[self.current_note_id]
        title = note.get("title", "Untitled")

        # Ask for export format
        export_type = messagebox.askyesno(
            "Export Format", "Export as HTML? (Yes) or Markdown? (No)"
        )

        if export_type:
            # Export as HTML
            filename = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                initialfile=f"{title}.html",
            )
            if filename:
                content = note.get("content", "")
                html = markdown.markdown(content, extensions=["extra", "codehilite"])
                full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {html}
</body>
</html>"""
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(full_html)
                messagebox.showinfo("Success", f"Note exported to {filename}")
        else:
            # Export as Markdown
            filename = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
                initialfile=f"{title}.md",
            )
            if filename:
                content = note.get("content", "")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n\n")
                    f.write(content)
                messagebox.showinfo("Success", f"Note exported to {filename}")

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Note Taker\n\n"
            "A simple note-taking application with markdown support, "
            "tags, search, and export functionality.\n\n"
            "Version 1.0",
        )

    def run(self) -> None:
        """Run the application."""
        logger.info("Starting Note Taker application")
        self.root.mainloop()


def main() -> int:
    """Main entry point for note taker application."""
    import argparse

    parser = argparse.ArgumentParser(description="Note-taking application with GUI")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = NoteTakerApp(config_path=args.config)
        app.run()
        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
