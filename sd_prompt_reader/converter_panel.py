__author__ = "receyuki"
__filename__ = "converter_panel.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

"""Right hand side panel: batch convert a folder of images to JPG/PNG/WEBP.

The prompt metadata is preserved during conversion (see ``image_converter``).
"""

from pathlib import Path
import queue
import threading

from customtkinter import (
    CTkButton,
    CTkEntry,
    CTkFrame,
    CTkLabel,
    CTkSegmentedButton,
    CTkSlider,
    CTkSwitch,
    filedialog,
)

from .button import STkButton
from .constants import ACCESSIBLE_GRAY, VIEW_TAB_FILE
from .file_list import ImageListFrame, list_images
from .image_converter import EXPORT_FORMATS, convert_folder

COLLAPSED_WIDTH = 46
EXPANDED_WIDTH = 258

# How often the main thread drains worker messages while converting.
POLL_INTERVAL_MS = 80

CONFIG_FOLDER = "convert_folder"
CONFIG_EXPORT = "convert_export_dir"
CONFIG_FORMAT = "convert_format"
CONFIG_OPEN = "convert_open"
CONFIG_QUALITY = "convert_jpeg_quality"
CONFIG_COMPRESSION = "convert_png_compression"
CONFIG_WEBP_QUALITY = "convert_webp_quality"
CONFIG_WEBP_LOSSLESS = "convert_webp_lossless"


class ConverterPanel(CTkFrame):
    def __init__(self, master, app, config, **kwargs):
        super().__init__(master, width=COLLAPSED_WIDTH, **kwargs)
        self.app = app
        self.config = config
        self._folder = None
        self._busy = False
        self._cancelled = None
        self._events = None
        self._worker = None
        self._poll_handle = None
        # False until the stored settings have been applied, so restoring the
        # panel does not immediately write the same values back to disk.
        self._ready = False

        self.grid_propagate(False)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._restore()

    # ----------------------------------------------------------------- header
    def _build_header(self):
        self.header = CTkFrame(self, fg_color="transparent", height=36)
        self.header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = CTkLabel(
            self.header,
            text="Convert",
            anchor="w",
            text_color=ACCESSIBLE_GRAY,
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.button_toggle = STkButton(
            self.header,
            width=30,
            height=30,
            text="",
            image=self.app.load_icon(VIEW_TAB_FILE, (20, 20)),
            command=self.toggle,
        )
        self.button_toggle.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------- body
    def _build_body(self):
        self.body = CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(6, 8))

        # --- folder
        self.folder_row = CTkFrame(self.body, fg_color="transparent")
        self.folder_row.pack(fill="x")

        self.button_add = CTkButton(
            self.folder_row, text="Add Folder", height=28, command=self.add_folder
        )
        self.button_add.pack(side="left", fill="x", expand=True)

        self.button_refresh = CTkButton(
            self.folder_row,
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
            self.body,
            text="No folder added",
            anchor="w",
            text_color=ACCESSIBLE_GRAY,
        )
        self.folder_label.pack(fill="x", pady=(2, 4))

        # --- image names (scrollable so the controls below always stay visible)
        self.list_frame = ImageListFrame(
            self.body,
            self.app,
            show_extension=True,
            copy_full_name=True,
            height=120,
        )
        self.list_frame.pack(fill="both", expand=True)

        # --- export folder
        self.export_label = CTkLabel(
            self.body,
            text="Export folder",
            anchor="w",
            text_color=ACCESSIBLE_GRAY,
        )
        self.export_label.pack(fill="x", pady=(6, 2))

        self.export_row = CTkFrame(self.body, fg_color="transparent")
        self.export_row.pack(fill="x")
        self.export_entry = CTkEntry(self.export_row, height=28, placeholder_text="")
        self.export_entry.pack(side="left", fill="x", expand=True)
        self.button_export_browse = CTkButton(
            self.export_row,
            text="...",
            width=30,
            height=28,
            command=self.select_export_dir,
        )
        self.button_export_browse.pack(side="left", padx=(4, 0))

        # --- format
        self.format_label = CTkLabel(
            self.body,
            text="Format",
            anchor="w",
            text_color=ACCESSIBLE_GRAY,
        )
        self.format_label.pack(fill="x", pady=(8, 2))

        self.format_box = CTkSegmentedButton(
            self.body,
            values=list(EXPORT_FORMATS.keys()),
            height=38,
            font=self.app.info_font,
            command=self._format_changed,
        )
        self.format_box.pack(fill="x")

        # --- options
        self.options = CTkFrame(self.body, fg_color="transparent")
        self.options.pack(fill="x", pady=(6, 0))

        self.jpeg_frame, self.jpeg_slider, self.jpeg_value = self._add_slider(
            "Quality", 1, 100, 95
        )
        self.png_frame, self.png_slider, self.png_value = self._add_slider(
            "Compression", 0, 9, 6
        )
        self.png_hint = CTkLabel(
            self.png_frame,
            text="0 = fastest / largest, 9 = smallest",
            anchor="w",
            text_color=ACCESSIBLE_GRAY,
        )
        self.png_hint.pack(fill="x")

        self.webp_frame, self.webp_slider, self.webp_value = self._add_slider(
            "Quality", 1, 100, 90
        )
        self.webp_lossless = CTkSwitch(
            self.webp_frame,
            text="Lossless",
            command=self._remember_options,
        )
        self.webp_lossless.pack(fill="x", pady=(2, 0))

        # --- convert
        self.button_convert = CTkButton(
            self.body,
            text="Convert",
            height=34,
            font=self.app.info_font,
            command=self.convert,
        )
        self.button_convert.pack(fill="x", pady=(10, 0))

    def _add_slider(self, text, minimum, maximum, default):
        frame = CTkFrame(self.options, fg_color="transparent")

        header = CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x")
        CTkLabel(header, text=text, anchor="w").pack(side="left")
        value_label = CTkLabel(header, text=str(default), anchor="e", width=36)
        value_label.pack(side="right")

        slider = CTkSlider(
            frame,
            from_=minimum,
            to=maximum,
            number_of_steps=maximum - minimum,
            command=lambda value, label=value_label: self._slider_changed(
                label, value
            ),
        )
        slider.set(default)
        slider.pack(fill="x")
        return frame, slider, value_label

    @staticmethod
    def _slider_changed(label, value):
        label.configure(text=str(int(round(float(value)))))

    # -------------------------------------------------------------- behaviour
    def toggle(self):
        self.set_expanded(not self.is_expanded())
        self.config.set(CONFIG_OPEN, self.is_expanded())

    def is_expanded(self):
        return bool(getattr(self, "_expanded", False))

    def set_expanded(self, expanded: bool):
        self._expanded = bool(expanded)
        if self._expanded:
            self.configure(width=EXPANDED_WIDTH)
            self.title_label.grid()
            self.body.grid()
        else:
            self.configure(width=COLLAPSED_WIDTH)
            self.title_label.grid_remove()
            self.body.grid_remove()

    def _restore(self):
        folder = self.config.get(CONFIG_FOLDER)
        if folder and Path(folder).is_dir():
            self.set_folder(folder, remember=False)
        else:
            self._sync_export_entry()

        export_dir = self.config.get(CONFIG_EXPORT)
        if export_dir:
            self.export_entry.delete(0, "end")
            self.export_entry.insert(0, export_dir)

        selected = str(self.config.get(CONFIG_FORMAT, "PNG")).upper()
        if selected not in EXPORT_FORMATS:
            selected = "PNG"
        self.format_box.set(selected)

        self.jpeg_slider.set(self._clamp(self.config.get(CONFIG_QUALITY), 1, 100, 95))
        self.png_slider.set(
            self._clamp(self.config.get(CONFIG_COMPRESSION), 0, 9, 6)
        )
        self.webp_slider.set(
            self._clamp(self.config.get(CONFIG_WEBP_QUALITY), 1, 100, 90)
        )
        if self.config.get(CONFIG_WEBP_LOSSLESS):
            self.webp_lossless.select()

        self._format_changed(selected)
        self.set_expanded(bool(self.config.get(CONFIG_OPEN, False)))
        self._ready = True

    @staticmethod
    def _clamp(value, minimum, maximum, default):
        try:
            return min(maximum, max(minimum, int(round(float(value)))))
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------------ folder
    def add_folder(self):
        folder = filedialog.askdirectory(title="Select a folder to convert")
        if folder:
            self.set_folder(folder)

    def refresh(self):
        """Re-scan the current folder for images added or removed since it was opened.

        Falls back to the Photos panel's folder when this panel has none of its
        own, mirroring what ``convert`` does.
        """
        if self._folder is None and not self.adopt_browser_folder():
            self.app.status_bar.warning("Add a folder before refreshing")
            return
        self.set_folder(self._folder, remember=False)
        count = len(self.list_frame.paths)
        name = self._shorten(self._folder.name or str(self._folder), 20)
        self.app.status_bar.success(f"Refreshed '{name}' ({count} image(s))")

    def set_folder(self, folder, remember: bool = True):
        self._folder = Path(folder)
        paths = list_images(self._folder)
        self.list_frame.set_files(paths)
        name = self._folder.name or str(self._folder)
        self.folder_label.configure(text=f"{self._shorten(name, 20)} ({len(paths)})")
        if remember:
            self.config.set(CONFIG_FOLDER, str(self._folder))
        self._sync_export_entry()

    def _default_export_dir(self):
        if self._folder is None:
            return None
        return self._folder / "converted"

    def _sync_export_entry(self):
        """Pre-fill the export folder when the user has not chosen one yet."""
        if self.export_entry.get().strip():
            return
        default = self._default_export_dir()
        if default is not None:
            self.export_entry.delete(0, "end")
            self.export_entry.insert(0, str(default))

    def select_export_dir(self):
        initial = self.export_entry.get().strip() or (
            str(self._folder) if self._folder else "/"
        )
        folder = filedialog.askdirectory(
            title="Select an export folder", initialdir=initial
        )
        if folder:
            self.export_entry.delete(0, "end")
            self.export_entry.insert(0, folder)
            self.config.set(CONFIG_EXPORT, folder)

    # ------------------------------------------------------------------ format
    def target_format(self) -> str:
        return str(self.format_box.get()).upper()

    def _format_changed(self, _value=None):
        target = self.target_format()
        self.jpeg_frame.pack_forget()
        self.png_frame.pack_forget()
        self.webp_frame.pack_forget()
        if target == "JPG":
            self.jpeg_frame.pack(fill="x")
        elif target == "PNG":
            self.png_frame.pack(fill="x")
        else:
            self.webp_frame.pack(fill="x")
        self._remember_options()

    def _remember_options(self, _value=None):
        if not self._ready:
            return
        self.config.update(
            {
                CONFIG_FORMAT: self.target_format(),
                CONFIG_QUALITY: int(round(self.jpeg_slider.get())),
                CONFIG_COMPRESSION: int(round(self.png_slider.get())),
                CONFIG_WEBP_QUALITY: int(round(self.webp_slider.get())),
                CONFIG_WEBP_LOSSLESS: bool(self.webp_lossless.get()),
            }
        )

    # ----------------------------------------------------------------- convert
    def adopt_browser_folder(self) -> bool:
        """Use the Photos panel's folder when this panel has none of its own.

        The two panels keep separate folders, which made "Add a folder before
        converting" show up even though a folder was already open on the left.
        """
        browser = getattr(self.app, "image_browser", None)
        if browser is None:
            return False
        folder = getattr(browser, "_folder", None)
        paths = browser.list_frame.paths
        if folder is None or not paths:
            return False
        self._folder = Path(folder)
        self.list_frame.set_files(paths)
        name = self._folder.name or str(self._folder)
        self.folder_label.configure(text=f"{self._shorten(name, 20)} ({len(paths)})")
        self.config.set(CONFIG_FOLDER, str(self._folder))
        self._sync_export_entry()
        return True

    def convert(self):
        if self._busy:
            return

        paths = self.list_frame.paths
        # Only borrow the Photos panel's folder when this panel has no folder of
        # its own. Without the ``_folder is None`` guard, a folder the user
        # actually picked that happens to be empty (or holds no images) was
        # silently ignored and the Photos folder was converted instead.
        if not paths and self._folder is None and self.adopt_browser_folder():
            paths = self.list_frame.paths
        if not paths:
            if self._folder is None:
                self.app.status_bar.warning("Add a folder before converting")
            else:
                # The folder exists but nothing in it was recognised, which is a
                # different problem from having no folder at all.
                name = self._shorten(self._folder.name or str(self._folder), 24)
                self.app.status_bar.warning(f"No images found in '{name}'")
            return

        export_dir = self.export_entry.get().strip()
        if not export_dir:
            default = self._default_export_dir()
            if default is None:
                self.app.status_bar.warning("Select an export folder")
                return
            export_dir = str(default)
            self.export_entry.delete(0, "end")
            self.export_entry.insert(0, export_dir)

        target = self.target_format()
        self.config.set(CONFIG_EXPORT, export_dir)
        self._remember_options()

        # Validate the destination before starting a batch that could be long.
        export_path = Path(export_dir)
        try:
            export_path.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self.app.status_bar.warning(f"Export folder unusable: {error}")
            return
        if not export_path.is_dir():
            self.app.status_bar.warning("Export folder is not a directory")
            return

        self._start_batch(paths, export_path, target)

    def _start_batch(self, paths, export_dir, target):
        """Convert on a worker thread so a big folder cannot freeze the window."""
        # Widgets are read here, on the main thread, and plain values are handed
        # to the worker: widgets must never be touched from another thread.
        options = {
            "jpeg_quality": int(round(self.jpeg_slider.get())),
            "png_compress_level": int(round(self.png_slider.get())),
            "webp_quality": int(round(self.webp_slider.get())),
            "webp_lossless": bool(self.webp_lossless.get()),
        }
        self._busy = True
        self._cancelled = threading.Event()
        self._events = queue.Queue()
        self.button_convert.configure(
            text=f"Cancel 0/{len(paths)}", command=self.cancel
        )
        self.app.status_bar.info(f"Converting {len(paths)} image(s) to {target}...")

        worker = threading.Thread(
            target=self._run_batch,
            args=(paths, export_dir, target, options),
            daemon=True,
        )
        self._worker = worker
        worker.start()
        self._poll_handle = self.after(POLL_INTERVAL_MS, self._poll_events)

    def _run_batch(self, paths, export_dir, target, options):
        """Worker thread: only touches the queue, never a widget."""
        try:
            result = convert_folder(
                paths,
                export_dir,
                target,
                jpeg_quality=options["jpeg_quality"],
                png_compress_level=options["png_compress_level"],
                webp_quality=options["webp_quality"],
                webp_lossless=options["webp_lossless"],
                progress=lambda done, total: self._events.put(
                    ("progress", done, total)
                ),
                should_stop=self._cancelled.is_set,
            )
        except Exception as error:  # noqa: BLE001 - never take the UI down
            self._events.put(("error", error))
        else:
            self._events.put(("done", result))

    def _reset_button(self):
        self.button_convert.configure(text="Convert", command=self.convert)

    def _poll_events(self):
        """Main thread: drain worker messages and refresh the UI.

        Wrapped so that a failure here can never leave the panel stuck in the
        busy state with a grey, unclickable button.
        """
        self._poll_handle = None
        try:
            self._drain_events()
        except Exception as error:  # noqa: BLE001
            print(f"Converter poll error: {error}")
            self._busy = False
            self._reset_button()

    def _drain_events(self):
        finished = None
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "progress":
                _, done, total = event
                self.button_convert.configure(text=f"Cancel {done}/{total}")
                self.app.status_bar.info(
                    f"Converting {done}/{total} image(s) to {self.target_format()}..."
                )
            else:
                finished = event

        if finished is None:
            self._poll_handle = self.after(POLL_INTERVAL_MS, self._poll_events)
            return

        cancelled = self._cancelled.is_set()
        self._busy = False
        self._reset_button()

        kind = finished[0]
        if kind == "error":
            self.app.status_bar.warning(f"Conversion failed: {finished[1]}")
            return

        succeeded, failures = finished[1]
        if cancelled:
            self.app.status_bar.warning(f"Cancelled after {succeeded} image(s)")
        elif failures:
            first_path, first_error = failures[0]
            self.app.status_bar.warning(
                f"{succeeded} converted, {len(failures)} failed "
                f"({first_path.name}: {first_error})"
            )
        else:
            self.app.status_bar.success(
                f"Converted {succeeded} image(s) to {self.target_format()}"
            )

    def cancel(self):
        if self._busy:
            self._cancelled.set()
            self.button_convert.configure(text="Cancelling...")

    # ------------------------------------------------------------------- misc
    @staticmethod
    def _shorten(text: str, limit: int = 24):
        return text if len(text) <= limit else text[: limit - 1] + "\u2026"
