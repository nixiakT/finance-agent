"""Helpers for multimodal user messages.

The agent keeps the internal message shape close to Anthropic content blocks:
text blocks and image blocks can appear together in a user message. Backends
that speak OpenAI-compatible APIs can pass the list through unchanged when the
selected model supports vision.
"""
from __future__ import annotations

import base64
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Any


MAX_IMAGE_EDGE = 1568


def image_block(path: str | Path, media_type: str | None = None) -> dict[str, Any]:
    """Encode one local image as a base64 content block.

    If Pillow is available, large images are resized so the longest edge is at
    most ``MAX_IMAGE_EDGE`` pixels. Without Pillow the original bytes are used.
    """
    image_path = Path(path)
    data, detected_type = _read_image_bytes(image_path)
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type or detected_type,
            "data": base64.b64encode(data).decode("ascii"),
        },
    }


def user_content_blocks(text: str, image_paths: list[str | Path] | None = None) -> list[dict[str, Any]]:
    """Build mixed text/image content for one user message."""
    blocks: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for image_path in image_paths or []:
        blocks.append(image_block(image_path))
    return blocks


def _read_image_bytes(path: Path) -> tuple[bytes, str]:
    if not path.exists():
        raise FileNotFoundError(f"image not found: {path}")
    if not path.is_file():
        raise ValueError(f"image path is not a file: {path}")

    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    raw = path.read_bytes()
    try:
        from PIL import Image  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 - Pillow is optional for this project
        return raw, media_type

    try:
        with Image.open(BytesIO(raw)) as image:
            width, height = image.size
            longest = max(width, height)
            if longest <= MAX_IMAGE_EDGE:
                return raw, media_type

            scale = MAX_IMAGE_EDGE / longest
            resized = image.resize((max(1, int(width * scale)), max(1, int(height * scale))))
            output = BytesIO()
            fmt = image.format or _format_from_media_type(media_type)
            if fmt.upper() == "JPEG" and resized.mode in {"RGBA", "P"}:
                resized = resized.convert("RGB")
            resized.save(output, format=fmt)
            return output.getvalue(), media_type
    except Exception:  # noqa: BLE001 - corrupted/unsupported images should fall back to raw bytes
        return raw, media_type


def _format_from_media_type(media_type: str) -> str:
    if media_type == "image/jpeg":
        return "JPEG"
    if media_type == "image/webp":
        return "WEBP"
    return "PNG"
