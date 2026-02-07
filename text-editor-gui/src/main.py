"""Text Editor GUI - Simple text editor with GUI features.

This module provides a simple text editor with GUI featuring syntax highlighting,
find and replace, and multiple file tabs.
"""

import argparse
import logging
import logging.handlers
import os
import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SyntaxHighlighter:
    """Provides syntax highlighting for text editor."""

    def __init__(self, text_widget: tk.Text, config: Dict) -> None:
        """Initialize SyntaxHighlighter.

        Args:
            text_widget: Text widget to highlight.
            config: Configuration dictionary with syntax highlighting settings.
        """
        self.text_widget = text_widget
        self.config = config
        self.highlight_config = config.get("syntax_highlighting", {})

        # Define syntax patterns
        self.patterns = {
            "keyword": self.highlight_config.get("keywords", []),
            "string": self.highlight_config.get("string_patterns", []),
            "comment": self.highlight_config.get("comment_patterns", []),
            "number": self.highlight_config.get("number_patterns", []),
        }

        # Configure tags
        self._configure_tags()

    def _configure_tags(self) -> None:
        """Configure text tags for syntax highlighting."""
        tag_config = self.highlight_config.get("tags", {})

        # Keyword tag
        self.text_widget.tag_configure(
            "keyword",
            foreground=tag_config.get("keyword_color", "#0000FF"),
        )

        # String tag
        self.text_widget.tag_configure(
            "string",
            foreground=tag_config.get("string_color", "#008000"),
        )

        # Comment tag
        self.text_widget.tag_configure(
            "comment",
            foreground=tag_config.get("comment_color", "#808080"),
        )

        # Number tag
        self.text_widget.tag_configure(
            "number",
            foreground=tag_config.get("number_color", "#FF0000"),
        )

    def highlight_text(self, file_extension: str) -> None:
        """Highlight text based on file extension.

        Args:
            file_extension: File extension to determine syntax rules.
        """
        # Remove existing tags
        for tag in ["keyword", "string", "comment", "number"]:
            self.text_widget.tag_remove(tag, "1.0", tk.END)

        # Get file content
        content = self.text_widget.get("1.0", tk.END)

        # Highlight based on extension
        if file_extension in [".py", ".pyw"]:
            self._highlight_python(content)
        elif file_extension in [".js", ".jsx"]:
            self._highlight_javascript(content)
        elif file_extension in [".html", ".htm"]:
            self._highlight_html(content)
        elif file_extension in [".css"]:
            self._highlight_css(content)
        elif file_extension in [".json"]:
            self._highlight_json(content)

    def _highlight_python(self, content: str) -> None:
        """Highlight Python syntax.

        Args:
            content: Text content to highlight.
        """
        python_keywords = [
            "def", "class", "import", "from", "if", "else", "elif",
            "for", "while", "try", "except", "finally", "with",
            "return", "yield", "pass", "break", "continue", "lambda",
            "True", "False", "None", "and", "or", "not", "in", "is",
        ]

        # Highlight keywords
        for keyword in python_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            self._apply_tag(pattern, "keyword", content)

        # Highlight strings
        self._apply_tag(r'"[^"]*"', "string", content)
        self._apply_tag(r"'[^']*'", "string", content)
        self._apply_tag(r'"""[^"]*"""', "string", content)
        self._apply_tag(r"'''[^']*'''", "string", content)

        # Highlight comments
        self._apply_tag(r"#.*", "comment", content)

        # Highlight numbers
        self._apply_tag(r"\b\d+\.?\d*\b", "number", content)

    def _highlight_javascript(self, content: str) -> None:
        """Highlight JavaScript syntax.

        Args:
            content: Text content to highlight.
        """
        js_keywords = [
            "function", "var", "let", "const", "if", "else", "for",
            "while", "return", "class", "import", "export", "async",
            "await", "try", "catch", "finally", "true", "false", "null",
        ]

        for keyword in js_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            self._apply_tag(pattern, "keyword", content)

        self._apply_tag(r'"[^"]*"', "string", content)
        self._apply_tag(r"'[^']*'", "string", content)
        self._apply_tag(r"//.*", "comment", content)
        self._apply_tag(r"/\*.*?\*/", "comment", content)
        self._apply_tag(r"\b\d+\.?\d*\b", "number", content)

    def _highlight_html(self, content: str) -> None:
        """Highlight HTML syntax.

        Args:
            content: Text content to highlight.
        """
        self._apply_tag(r"<[^>]+>", "keyword", content)
        self._apply_tag(r'"[^"]*"', "string", content)
        self._apply_tag(r"<!--.*?-->", "comment", content)

    def _highlight_css(self, content: str) -> None:
        """Highlight CSS syntax.

        Args:
            content: Text content to highlight.
        """
        css_keywords = [
            "color", "background", "margin", "padding", "border",
            "width", "height", "display", "position", "float",
        ]

        for keyword in css_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            self._apply_tag(pattern, "keyword", content)

        self._apply_tag(r'"[^"]*"', "string", content)
        self._apply_tag(r"//.*", "comment", content)
        self._apply_tag(r"/\*.*?\*/", "comment", content)

    def _highlight_json(self, content: str) -> None:
        """Highlight JSON syntax.

        Args:
            content: Text content to highlight.
        """
        json_keywords = ["true", "false", "null"]

        for keyword in json_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            self._apply_tag(pattern, "keyword", content)

        self._apply_tag(r'"[^"]*"', "string", content)
        self._apply_tag(r"\b\d+\.?\d*\b", "number", content)

    def _apply_tag(self, pattern: str, tag: str, content: str) -> None:
        """Apply tag to matching patterns in text.

        Args:
            pattern: Regex pattern to match.
            tag: Tag name to apply.
            content: Text content to search.
        """
        for match in re.finditer(pattern, content, re.MULTILINE):
            start_line = content[: match.start()].count("\n") + 1
            start_col = match.start() - content.rfind("\n", 0, match.start()) - 1
            end_line = content[: match.end()].count("\n") + 1
            end_col = match.end() - content.rfind("\n", 0, match.end()) - 1

            start = f"{start_line}.{start_col}"
            end = f"{end_line}.{end_col}"

            self.text_widget.tag_add(tag, start, end)


class TextEditorTab:
    """Represents a single tab in the text editor."""

    def __init__(
        self, notebook: ttk.Notebook, file_path: Optional[Path] = None
    ) -> None:
        """Initialize TextEditorTab.

        Args:
            notebook: Notebook widget to add tab to.
            file_path: Optional path to file to open.
        """
        self.notebook = notebook
        self.file_path = file_path
        self.is_modified = False

        # Create frame for tab
        self.frame = ttk.Frame(notebook)

        # Create text widget with scrollbar
        self.text_widget = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, undo=True
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Bind text modification
        self.text_widget.bind("<KeyRelease>", self._on_text_change)
        self.text_widget.bind("<Button-1>", self._on_text_change)

        # Add tab to notebook
        tab_name = self._get_tab_name()
        self.notebook.add(self.frame, text=tab_name)

        # Load file if provided
        if file_path and file_path.exists():
            self.load_file(file_path)

    def _get_tab_name(self) -> str:
        """Get name for tab.

        Returns:
            Tab name string.
        """
        if self.file_path:
            name = self.file_path.name
        else:
            name = "Untitled"

        if self.is_modified:
            name += " *"

        return name

    def _on_text_change(self, event: Optional[tk.Event] = None) -> None:
        """Handle text change event.

        Args:
            event: Optional event object.
        """
        if not self.is_modified:
            self.is_modified = True
            self._update_tab_name()

    def _update_tab_name(self) -> None:
        """Update tab name to reflect modification status."""
        tab_index = self.notebook.index(self.frame)
        self.notebook.tab(tab_index, text=self._get_tab_name())

    def load_file(self, file_path: Path) -> None:
        """Load file into text widget.

        Args:
            file_path: Path to file to load.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", content)
            self.file_path = file_path
            self.is_modified = False
            self._update_tab_name()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_file(self, file_path: Optional[Path] = None) -> bool:
        """Save file from text widget.

        Args:
            file_path: Optional path to save to. Uses current file_path if not provided.

        Returns:
            True if saved successfully, False otherwise.
        """
        if not file_path:
            file_path = self.file_path

        if not file_path:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[
                    ("All Files", "*.*"),
                    ("Text Files", "*.txt"),
                    ("Python Files", "*.py"),
                    ("JavaScript Files", "*.js"),
                ],
            )
            if not file_path:
                return False
            file_path = Path(file_path)

        try:
            content = self.text_widget.get("1.0", tk.END)
            # Remove trailing newline added by text widget
            if content.endswith("\n"):
                content = content[:-1]

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.file_path = file_path
            self.is_modified = False
            self._update_tab_name()
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")
            return False

    def get_content(self) -> str:
        """Get text content from widget.

        Returns:
            Text content string.
        """
        return self.text_widget.get("1.0", tk.END)

    def get_text_widget(self) -> scrolledtext.ScrolledText:
        """Get text widget.

        Returns:
            Text widget.
        """
        return self.text_widget


class TextEditor:
    """Main text editor application."""

    def __init__(self, config: Dict) -> None:
        """Initialize TextEditor.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.editor_config = config.get("editor", {})

        # Setup logging
        self._setup_logging()

        # Create main window
        self.root = tk.Tk()
        self.root.title(self.editor_config.get("title", "Text Editor"))
        self.root.geometry(self.editor_config.get("geometry", "800x600"))

        # Store tabs
        self.tabs: List[TextEditorTab] = []
        self.current_tab_index = 0

        # Create UI
        self._create_menu()
        self._create_toolbar()
        self._create_notebook()
        self._create_statusbar()

        # Create initial tab
        self.new_file()

        # Bind keyboard shortcuts
        self._bind_shortcuts()

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/editor.log")

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
            ],
        )

    def _create_menu(self) -> None:
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(
            label="Open", command=self.open_file, accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="Save", command=self.save_file, accelerator="Ctrl+S"
        )
        file_menu.add_command(
            label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_editor)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="Find", command=self.find_text, accelerator="Ctrl+F"
        )
        edit_menu.add_command(
            label="Replace", command=self.replace_text, accelerator="Ctrl+H"
        )
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")

    def _create_toolbar(self) -> None:
        """Create toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Find", command=self.find_text).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Replace", command=self.replace_text).pack(side=tk.LEFT, padx=2)

    def _create_notebook(self) -> None:
        """Create notebook for tabs."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _create_statusbar(self) -> None:
        """Create status bar."""
        self.statusbar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_as_file())
        self.root.bind("<Control-f>", lambda e: self.find_text())
        self.root.bind("<Control-h>", lambda e: self.replace_text())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())

    def _on_tab_change(self, event: Optional[tk.Event] = None) -> None:
        """Handle tab change event.

        Args:
            event: Optional event object.
        """
        selected = self.notebook.index(self.notebook.select())
        if 0 <= selected < len(self.tabs):
            self.current_tab_index = selected

    def _get_current_tab(self) -> Optional[TextEditorTab]:
        """Get currently selected tab.

        Returns:
            Current tab or None.
        """
        if 0 <= self.current_tab_index < len(self.tabs):
            return self.tabs[self.current_tab_index]
        return None

    def new_file(self) -> None:
        """Create new file tab."""
        tab = TextEditorTab(self.notebook)
        self.tabs.append(tab)
        self.current_tab_index = len(self.tabs) - 1
        self.notebook.select(self.current_tab_index)

    def open_file(self) -> None:
        """Open file in new tab."""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("Python Files", "*.py"),
                ("JavaScript Files", "*.js"),
                ("HTML Files", "*.html"),
                ("CSS Files", "*.css"),
            ]
        )

        if file_path:
            tab = TextEditorTab(self.notebook, Path(file_path))
            self.tabs.append(tab)
            self.current_tab_index = len(self.tabs) - 1
            self.notebook.select(self.current_tab_index)

            # Apply syntax highlighting
            self._apply_syntax_highlighting(tab)

    def save_file(self) -> None:
        """Save current file."""
        tab = self._get_current_tab()
        if tab:
            tab.save_file()

    def save_as_file(self) -> None:
        """Save current file with new name."""
        tab = self._get_current_tab()
        if tab:
            tab.save_file(None)  # Will prompt for filename

    def find_text(self) -> None:
        """Open find dialog."""
        tab = self._get_current_tab()
        if not tab:
            return

        # Create find dialog
        find_window = tk.Toplevel(self.root)
        find_window.title("Find")
        find_window.geometry("400x150")

        ttk.Label(find_window, text="Find:").pack(pady=5)
        find_entry = ttk.Entry(find_window, width=40)
        find_entry.pack(pady=5)
        find_entry.focus()

        def do_find() -> None:
            search_text = find_entry.get()
            if search_text:
                text_widget = tab.get_text_widget()
                start = text_widget.search(search_text, "1.0", tk.END)
                if start:
                    end = f"{start}+{len(search_text)}c"
                    text_widget.tag_remove(tk.SEL, "1.0", tk.END)
                    text_widget.tag_add(tk.SEL, start, end)
                    text_widget.mark_set(tk.INSERT, start)
                    text_widget.see(start)

        ttk.Button(find_window, text="Find", command=do_find).pack(pady=5)
        find_entry.bind("<Return>", lambda e: do_find())

    def replace_text(self) -> None:
        """Open replace dialog."""
        tab = self._get_current_tab()
        if not tab:
            return

        # Create replace dialog
        replace_window = tk.Toplevel(self.root)
        replace_window.title("Find and Replace")
        replace_window.geometry("400x200")

        ttk.Label(replace_window, text="Find:").pack(pady=5)
        find_entry = ttk.Entry(replace_window, width=40)
        find_entry.pack(pady=5)

        ttk.Label(replace_window, text="Replace:").pack(pady=5)
        replace_entry = ttk.Entry(replace_window, width=40)
        replace_entry.pack(pady=5)

        def do_replace() -> None:
            find_text = find_entry.get()
            replace_text = replace_entry.get()
            if find_text:
                text_widget = tab.get_text_widget()
                content = text_widget.get("1.0", tk.END)
                new_content = content.replace(find_text, replace_text)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", new_content)
                tab.is_modified = True
                tab._update_tab_name()

        ttk.Button(replace_window, text="Replace All", command=do_replace).pack(pady=5)

    def undo(self) -> None:
        """Undo last action."""
        tab = self._get_current_tab()
        if tab:
            try:
                tab.get_text_widget().edit_undo()
            except tk.TclError:
                pass

    def redo(self) -> None:
        """Redo last action."""
        tab = self._get_current_tab()
        if tab:
            try:
                tab.get_text_widget().edit_redo()
            except tk.TclError:
                pass

    def _apply_syntax_highlighting(self, tab: TextEditorTab) -> None:
        """Apply syntax highlighting to tab.

        Args:
            tab: Tab to apply highlighting to.
        """
        if not tab.file_path:
            return

        file_extension = tab.file_path.suffix.lower()
        highlighter = SyntaxHighlighter(tab.get_text_widget(), self.config)
        highlighter.highlight_text(file_extension)

    def quit_editor(self) -> None:
        """Quit editor, checking for unsaved changes."""
        unsaved = []
        for tab in self.tabs:
            if tab.is_modified:
                unsaved.append(tab._get_tab_name())

        if unsaved:
            msg = f"Unsaved changes in: {', '.join(unsaved)}\nQuit anyway?"
            if not messagebox.askyesno("Unsaved Changes", msg):
                return

        self.root.quit()
        self.root.destroy()

    def run(self) -> None:
        """Run the editor."""
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
        description="Simple text editor with GUI featuring syntax highlighting, "
        "find and replace, and multiple file tabs"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Files to open in editor",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        # Use default config if file doesn't exist
        config = {}
    except yaml.YAMLError as e:
        logger.error(str(e))
        sys.exit(1)

    editor = TextEditor(config)

    # Open files if provided
    for file_path in args.files:
        if file_path.exists():
            tab = TextEditorTab(editor.notebook, file_path)
            editor.tabs.append(tab)
            editor._apply_syntax_highlighting(tab)

    editor.run()


if __name__ == "__main__":
    main()
