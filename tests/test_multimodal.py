from __future__ import annotations

import base64

from backend.multimodal import image_block, user_content_blocks


def test_image_block_encodes_local_image(tmp_path) -> None:  # noqa: ANN001
    image = tmp_path / "chart.png"
    image.write_bytes(b"fake-image-bytes")

    block = image_block(image)

    assert block["type"] == "image"
    assert block["source"]["type"] == "base64"
    assert block["source"]["media_type"] == "image/png"
    assert base64.b64decode(block["source"]["data"]) == b"fake-image-bytes"


def test_user_content_blocks_mix_text_and_images(tmp_path) -> None:  # noqa: ANN001
    image = tmp_path / "screen.jpeg"
    image.write_bytes(b"jpeg-ish")

    blocks = user_content_blocks("看这张图", [image])

    assert blocks[0] == {"type": "text", "text": "看这张图"}
    assert blocks[1]["type"] == "image"
    assert blocks[1]["source"]["media_type"] == "image/jpeg"
