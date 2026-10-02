__author__ = "receyuki"
__filename__ = "__init__.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

"""Package level setup.

Windows consoles default to a legacy code page (cp1252/cp437), so printing a
path that contains Arabic, Japanese or emoji characters raised
``UnicodeEncodeError``. Because those prints happen inside Tk callbacks it could
abort the callback halfway and leave the window in a half-updated state.
Switching the streams to ``errors="replace"`` leaves the encoding untouched but
makes any diagnostic print harmless.
"""

import sys


def _make_console_unicode_safe() -> None:
    for stream in (getattr(sys, "stdout", None), getattr(sys, "stderr", None)):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="replace")
        except (OSError, ValueError):
            pass


_make_console_unicode_safe()
