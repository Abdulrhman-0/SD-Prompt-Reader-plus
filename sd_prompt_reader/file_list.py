__author__ = "receyuki"
__filename__ = "file_list.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

"""A lightweight, scrollable list of image files.

Plain ``tkinter`` widgets are used for the rows (instead of CustomTkinter
widgets) because a folder can easily hold hundreds of images and CustomTkinter
widgets are comparatively expensive to create.
"""

import os
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk
from customtkinter import (
    CTkFrame,
    CTkScrollableFrame,
    ThemeManager,
    get_appearance_mode,
)

from .constants import SUPPORTED_FORMATS, COPY_FILE_L

# Safety valve so a mis-selected folder (e.g. a whole drive) can't hang the UI.
MAX_LISTED_FILES = 3000

# Rows are created in small batches (via ``after``) instead of all at once:
# building a few thousand widgets in a single callback freezes the window, which
# made clicks queue up and appear to be ignored on folders with hundreds of files.
RENDER_CHUNK_SIZE = 50
RENDER_CHUNK_DELAY_MS = 1

ICON_SIZE = (16, 16)
_HIGHLIGHT_COLOR = ("#3B8ED0", "#1F6AA5")
_HIGHLIGHT_TEXT = ("#FFFFFF", "#FFFFFF")

# The resized PIL icon is safe to share; the Tk photo image is not (it belongs to
# one Tk interpreter), so each list creates its own copy of it.
_PIL_ICON_CACHE = {}


def themed(color):
    """Collapse a CustomTkinter ``(light, dark)`` colour pair for plain Tk."""
    if isinstance(color, (tuple, list)) and len(color) == 2:
        return color[1] if get_appearance_mode() == "Dark" else color[0]
    return color


def _get_pil_icon():
    key = str(COPY_FILE_L[0])
    if key not in _PIL_ICON_CACHE:
        _PIL_ICON_CACHE[key] = Image.open(COPY_FILE_L[0]).resize(
            ICON_SIZE, Image.LANCZOS
        )
    return _PIL_ICON_CACHE[key]


def list_images(folder, recursive: bool = True):
    """Return the image files inside ``folder``, sorted by name.

    Never raises, and never throws away files it has already found: a single
    unreadable entry, a path that is too long, or a locked sub folder must not
    make a populated folder look empty (that is what used to happen when
    ``Path.rglob`` raised and the partial result was discarded).
    """
    try:
        root = Path(folder)
    except (TypeError, ValueError):
        return []

    if not root.is_dir():
        return []

    suffixes = {suffix.lower() for suffix in SUPPORTED_FORMATS}
    files = []
    pending = [root]

    while pending and len(files) < MAX_LISTED_FILES:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError:
            # Unreadable folder or a name Windows cannot address: skip it and
            # carry on with the rest of the tree.
            continue
        for entry in entries:
            if len(files) >= MAX_LISTED_FILES:
                break
            try:
                if entry.is_dir(follow_symlinks=False):
                    if recursive:
                        pending.append(Path(entry.path))
                    continue
                if not entry.is_file():
                    continue
            except OSError:
                # Broken link, deleted in the meantime, permission denied, ...
                continue
            if Path(entry.name).suffix.lower() in suffixes:
                files.append(Path(entry.path))

    files.sort(key=lambda path: (str(path.parent).lower(), path.name.lower()))
    return files


class ImageListFrame(CTkFrame):
    """Scrollable list of image names with a copy button and a context menu."""

    def __init__(
        self,
        master,
        app,
        on_click=None,
        show_extension: bool = False,
        copy_full_name: bool = True,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._on_click = on_click
        self._show_extension = show_extension
        self._copy_full_name = copy_full_name

        self._paths = []
        self._rows = {}
        self._selected = None
        self._wanted = None
        self._pending = []
        self._render_handle = None

        self._background = themed(ThemeManager.theme["CTkFrame"]["fg_color"])
        self._foreground = themed(("gray10", "#DCE4EE"))
        self._highlight = themed(_HIGHLIGHT_COLOR)
        self._highlight_text = themed(_HIGHLIGHT_TEXT)

        self._scroll = CTkScrollableFrame(self, fg_color=self._background)
        self._scroll.pack(fill="both", expand=True)
        # Kept on the instance so Tk does not garbage collect it.
        self._icon = ImageTk.PhotoImage(_get_pil_icon())

        self._menu = tk.Menu(self, tearoff=0)
        self._menu.add_command(label="Copy name", command=self._menu_copy_name)
        self._menu.add_command(label="Copy path", command=self._menu_copy_path)
        self._menu_path = None

    # ------------------------------------------------------------------ data
    @property
    def paths(self):
        return list(self._paths)

    def clear(self):
        self._stop_pending_render()
        for child in self._scroll.winfo_children():
            child.destroy()
        self._paths = []
        self._rows = {}
        self._selected = None
        self._pending = []

    def set_files(self, paths):
        self.clear()
        self._paths = list(paths)
        self._pending = [Path(path) for path in self._paths]
        self._render_next_chunk()

    def _render_next_chunk(self):
        self._render_handle = None
        chunk = self._pending[:RENDER_CHUNK_SIZE]
        del self._pending[:RENDER_CHUNK_SIZE]
        for path in chunk:
            self._add_row(path)
        if self._pending:
            self._render_handle = self.after(
                RENDER_CHUNK_DELAY_MS, self._render_next_chunk
            )

    def _stop_pending_render(self):
        if self._render_handle is not None:
            try:
                self.after_cancel(self._render_handle)
            except Exception:
                pass
            self._render_handle = None

    def highlight(self, path):
        """Mark ``path`` as selected; silently ignore unknown paths."""
        try:
            resolved = Path(path)
        except (TypeError, ValueError):
            return
        self._wanted = resolved

        key = resolved if resolved in self._rows else None
        if key is None:
            # Fall back to a case-insensitive comparison (Windows paths).
            for candidate in self._rows:
                if str(candidate).lower() == str(resolved).lower():
                    key = candidate
                    break
        if key is not None:
            self._select(key, self._rows[key])
        # Otherwise the row may still be waiting in the render queue; it will be
        # selected by _add_row once it exists.

    # ------------------------------------------------------------------ rows
    def _add_row(self, path: Path):
        text = path.name if self._show_extension else path.stem
        row = tk.Frame(self._scroll, bg=self._background, cursor="hand2")
        row.pack(fill="x")

        label = tk.Label(
            row,
            text=text,
            anchor="w",
            justify="left",
            bg=self._background,
            fg=self._foreground,
            cursor="hand2",
        )
        label.pack(side="left", fill="x", expand=True, padx=(6, 0), pady=2)

        copy_button = tk.Label(
            row,
            image=self._icon,
            bg=self._background,
            cursor="hand2",
        )
        copy_button.pack(side="right", padx=(2, 6))

        widgets = (row, label, copy_button)
        self._rows[path] = widgets

        if self._wanted is not None and str(path).lower() == str(self._wanted).lower():
            self._select(path, widgets)

        for widget in widgets:
            widget.bind("<Button-1>", lambda event, p=path: self._click(p))
            widget.bind("<Button-3>", lambda event, p=path: self._context(event, p))
            widget.bind("<Button-2>", lambda event, p=path: self._context(event, p))
            if widget is not copy_button:
                widget.bind(
                    "<Enter>", lambda event, p=path: self._hover(p, True)
                )
                widget.bind(
                    "<Leave>", lambda event, p=path: self._hover(p, False)
                )

        copy_button.bind(
            "<Button-1>", lambda event, p=path: self._copy_name(p)
        )

    def _click(self, path: Path):
        # Remember the choice so a still-pending render chunk cannot steal the
        # selection back when it catches up.
        self._wanted = path
        self._select(path, self._rows.get(path))
        if self._on_click:
            self._on_click(path)

    def _context(self, event, path: Path):
        self._menu_path = path
        self._click(path)
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _hover(self, path: Path, entering: bool):
        if path == self._selected:
            return
        widgets = self._rows.get(path)
        if not widgets:
            return
        color = themed(("gray86", "gray17")) if entering else self._background
        for widget in widgets:
            widget.configure(bg=color)

    def _paint(self, path: Path, background, foreground):
        widgets = self._rows.get(path)
        if not widgets:
            return
        for widget in widgets:
            widget.configure(bg=background)
        widgets[1].configure(fg=foreground)

    def _select(self, path: Path, widgets):
        if self._selected is not None:
            self._paint(self._selected, self._background, self._foreground)
        self._selected = None if widgets is None else path
        if widgets is None:
            return
        for widget in widgets:
            widget.configure(bg=self._highlight)
        widgets[1].configure(fg=self._highlight_text)

    # ------------------------------------------------------------- clipboard
    def _display_name(self, path: Path):
        if self._copy_full_name:
            return path.name
        return path.stem

    def _copy_name(self, path: Path):
        self._copy(str(self._display_name(path)))

    def _copy(self, content: str):
        from .utility import copy_to_clipboard

        copy_to_clipboard(self.app.status_bar, content)

    def _menu_copy_name(self):
        if self._menu_path is not None:
            self._copy_name(self._menu_path)

    def _menu_copy_path(self):
        if self._menu_path is not None:
            self._copy(str(self._menu_path))
