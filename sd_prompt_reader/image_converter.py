__author__ = "receyuki"
__filename__ = "image_converter.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

"""Format conversion that preserves the generation metadata (prompt).

Strategy
--------
* PNG -> PNG     : every text chunk is copied verbatim (perfect fidelity).
* anything -> PNG: every text chunk of the source is copied; when the source has
                   no recognisable prompt chunk, an A1111 style ``parameters``
                   chunk is synthesised so the prompt stays readable.
* -> JPG / WEBP  : the prompt is written into the EXIF ``UserComment`` exactly
                   the way A1111 does it, which is what every reader expects.
"""

from pathlib import Path

import piexif
import piexif.helper
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from .image_data_reader import ImageDataReader

# Export target -> (file extension, Pillow format string)
EXPORT_FORMATS = {
    "JPG": (".jpg", "JPEG"),
    "PNG": (".png", "PNG"),
    "WEBP": (".webp", "WEBP"),
}

# Text chunks that already contain a prompt, so a synthetic one is not needed.
_PROMPT_CHUNKS = (
    "parameters",
    "prompt",
    "workflow",
    "Comment",
    "Description",
    "invokeai_metadata",
    "sd-metadata",
)


def is_plain_parameters(text: str) -> bool:
    """True when ``text`` is an A1111 style parameter string (not JSON)."""
    if not text:
        return False
    stripped = text.lstrip()
    return not stripped.startswith(("{", "["))


def collect_metadata(path) -> dict:
    """Read the metadata of an image without decoding it into memory twice."""
    metadata = {"format": None, "text": {}, "exif": None, "icc_profile": None}
    with Image.open(path) as image:
        metadata["format"] = image.format
        info = dict(image.info)
        text = {}
        if image.format == "PNG":
            try:
                text.update(image.text)
            except Exception:
                pass
        for key, value in info.items():
            if isinstance(value, str) and value:
                text[key] = value
        metadata["text"] = text
        exif = info.get("exif")
        if exif:
            metadata["exif"] = exif
        icc = info.get("icc_profile")
        if icc:
            metadata["icc_profile"] = icc
    return metadata


def read_prompt_text(path) -> str:
    """Best-effort plain text prompt for formats that only have one text slot."""
    try:
        with open(path, "rb") as f:
            reader = ImageDataReader(f)
        raw = reader.raw or ""
        if is_plain_parameters(raw):
            return raw
        # JSON payloads (ComfyUI, Easy Diffusion, ...) do not survive the trip
        # into an EXIF UserComment, so rebuild an A1111 style string instead.
        return ImageDataReader.construct_data(
            reader.positive, reader.negative, reader.setting
        )
    except Exception:
        return ""


def build_exif(metadata: dict, prompt_text: str):
    """Return EXIF bytes as produced by :func:`piexif.dump`, or ``None``.

    The ``Exif\\0\\0`` APP1 header is deliberately *not* included: Pillow adds it
    when saving a JPEG, and adding it twice corrupts the segment.
    """
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    if metadata.get("exif"):
        try:
            loaded = piexif.load(metadata["exif"])
            if loaded:
                exif_dict = loaded
        except Exception:
            pass
    if prompt_text:
        try:
            exif_dict.setdefault("Exif", {})
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
                piexif.helper.UserComment.dump(prompt_text, encoding="unicode")
            )
        except Exception:
            pass
    try:
        return piexif.dump(exif_dict)
    except Exception:
        return None


def prepare_mode(image: Image.Image, target: str) -> Image.Image:
    """Convert the pixel mode when the target format cannot store it."""
    if target == "JPG":
        if image.mode in ("RGBA", "LA", "PA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            background = Image.new("RGB", image.size, (255, 255, 255))
            rgba = image.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        if image.mode not in ("RGB", "L", "CMYK"):
            return image.convert("RGB")
        return image
    if target == "WEBP" and image.mode == "P":
        return image.convert("RGBA" if "transparency" in image.info else "RGB")
    return image


def convert_image(
    src,
    dst,
    target: str,
    jpeg_quality: int = 95,
    png_compress_level: int = 6,
    webp_quality: int = 90,
    webp_lossless: bool = False,
):
    """Convert ``src`` to ``dst`` keeping the prompt metadata.

    Raises on failure so the caller can report which file went wrong.
    """
    target = str(target).upper()
    if target not in EXPORT_FORMATS:
        raise ValueError(f"Unsupported target format: {target}")

    src = Path(src)
    dst = Path(dst)
    if src.resolve() == dst.resolve():
        raise ValueError("Source and destination are the same file")

    metadata = collect_metadata(src)
    prompt_text = read_prompt_text(src)

    dst.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(src) as image:
        image.load()
        output = prepare_mode(image, target)

        save_kwargs = {}
        if metadata.get("icc_profile"):
            save_kwargs["icc_profile"] = metadata["icc_profile"]

        if target == "PNG":
            chunks = dict(metadata["text"])
            # Only synthesise a prompt chunk when the source has none, otherwise
            # a perfectly good ComfyUI/Fooocus/InvokeAI chunk would be masked by
            # an A1111 style one.
            existing = {str(key).lower() for key, value in chunks.items() if value}
            if prompt_text and not any(
                name.lower() in existing for name in _PROMPT_CHUNKS
            ):
                chunks["parameters"] = prompt_text
            png_info = PngInfo()
            for key, value in chunks.items():
                try:
                    png_info.add_text(str(key), value)
                except Exception:
                    continue
            save_kwargs["pnginfo"] = png_info
            save_kwargs["compress_level"] = max(0, min(9, int(png_compress_level)))
        else:
            exif_bytes = build_exif(metadata, prompt_text)
            if exif_bytes:
                save_kwargs["exif"] = exif_bytes
            if target == "JPG":
                save_kwargs["quality"] = max(1, min(100, int(jpeg_quality)))
                save_kwargs["optimize"] = True
            else:
                save_kwargs["quality"] = max(1, min(100, int(webp_quality)))
                save_kwargs["lossless"] = bool(webp_lossless)

        output.save(dst, EXPORT_FORMATS[target][1], **save_kwargs)

    return dst


def convert_folder(
    paths,
    export_dir,
    target: str,
    jpeg_quality: int = 95,
    png_compress_level: int = 6,
    webp_quality: int = 90,
    webp_lossless: bool = False,
    progress=None,
    should_stop=None,
):
    """Convert every path into ``export_dir``.

    ``progress`` is called as ``progress(done, total)`` after each file and
    ``should_stop`` as ``should_stop()`` before each file, so a caller can run
    this on a worker thread and still report progress / cancel.

    Returns ``(succeeded, [(path, error), ...])``. Never raises.
    """
    extension = EXPORT_FORMATS[str(target).upper()][0]
    export_dir = Path(export_dir)
    succeeded = 0
    failures = []
    total = len(paths)

    for index, path in enumerate(paths):
        if should_stop is not None and should_stop():
            break
        path = Path(path)
        destination = export_dir / (path.stem + extension)
        if destination.resolve() == path.resolve():
            destination = export_dir / (path.stem + "_converted" + extension)
        try:
            convert_image(
                path,
                destination,
                target,
                jpeg_quality=jpeg_quality,
                png_compress_level=png_compress_level,
                webp_quality=webp_quality,
                webp_lossless=webp_lossless,
            )
        except Exception as error:  # noqa: BLE001 - report, never abort the batch
            failures.append((path, error))
        else:
            succeeded += 1
        if progress:
            progress(index + 1, total)

    return succeeded, failures
