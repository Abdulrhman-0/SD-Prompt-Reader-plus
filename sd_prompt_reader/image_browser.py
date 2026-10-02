__author__ = "receyuki"
__filename__ = "image_browser.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

"""Left hand side panel: browse a folder of images and open one on click."""

from pathlib import Path

from customtkinter import CTkButton, CTkFrame, CTkLabel, filedialog

from .constants import ACCESSIBLE_GRAY
from .file_list import ImageListFrame, list_images

BROWSER_WIDTH = 210
CONFIG_KEY = "browser_folder"


class ImageBrowser(CTkFrame):
    def __init__(self, master, app, config, width: int = BROWSER_WIDTH, **kwargs):
        super().__init__(master, width=width, **kwargs)
        self.app = app
        self.config = config
        self._folder = None

        # Keep the panel a fixed width regardless of the file names inside.
        self.pack_propagate(False)

        self.title_label = CTkLabel(
            self,
            text="Photos",
            anchor="w",
            height=24,
            text_color=ACCESSIBLE_GRAY,
        )
        self.title_label.pack(fill="x", padx=8, pady=(8, 0))

        self.button_frame = CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=8, pady=(4, 4))

        self.button_add = CTkButton(
            self.button_frame,
            text="Add Folder",
            height=28,
            command=self.add_folder,
        )
        self.button_add.pack(side="left", fill="x", expand=True)

        self.button_refresh = CTkButton(
            self.button_frame,
            text="Refresh",
            height=28,
            width=64,
            fg_color="transparent",
            border_width=1,
            text_color=ACCESSIBLE_GRAY,
            command=self.refresh,
        )
        self.button_refresh.pack(side="left", padx=(6, 0))

        self.folder_label = CTkLabel(
            self,
            text="No folder added",
            anchor="w",
            height=20,
            text_color=ACCESSIBLE_GRAY,
        )
        self.folder_label.pack(fill="x", padx=8, pady=(0, 4))

        self.list_frame = ImageListFrame(
            self,
            app,
            on_click=self._open,
            show_extension=False,
            copy_full_name=False,
        )
        self.list_frame.pack(fill="both", expand=True, padx=(2, 2), pady=(0, 8))

        self.restore()

    # ------------------------------------------------------------------ folder
    def restore(self):
        """Re-open the folder remembered from the previous session."""
        folder = self.config.get(CONFIG_KEY)
        if not folder:
            return
        if Path(folder).is_dir():
            self.set_folder(folder, remember=False, silent=True)
        else:
            self.folder_label.configure(text="Last folder is unavailable")

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select a folder of images")
        if folder:
            self.set_folder(folder)

    def refresh(self):
        if self._folder:
            self.set_folder(self._folder, remember=False)

    def set_folder(self, folder, remember: bool = True, silent: bool = False):
        self._folder = Path(folder)
        paths = list_images(self._folder)
        self.list_frame.set_files(paths)

        self.title_label.configure(text=f"Photos ({len(paths)})")
        name = self._folder.name or str(self._folder)
        self.folder_label.configure(text=self._shorten(name))

        if remember:
            self.config.set(CONFIG_KEY, str(self._folder))
        if not silent:
            self.app.status_bar.success(f"Loaded {len(paths)} image(s)")

    def _shorten(self, text: str, limit: int = 26):
        return text if len(text) <= limit else text[: limit - 1] + "\u2026"

    # -------------------------------------------------------------------- open
    def _open(self, path: Path):
        self.app.display_info(str(path), is_selected=True)

    def highlight(self, path):
        """Highlight the currently displayed image, if it belongs to this folder."""
        if self._folder is None:
            return
        try:
            resolved = Path(path).resolve()
        except (TypeError, ValueError):
            return
        if resolved in self.list_frame.paths:
            self.list_frame.highlight(resolved)
