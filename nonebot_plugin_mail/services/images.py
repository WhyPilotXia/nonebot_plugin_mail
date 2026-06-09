# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：群聊图片下载、压缩/转 base64、图片临时保存

import base64
import json
import time
from pathlib import Path
from typing import Any

import httpx
from nonebot.adapters.onebot.v11 import Bot, Event

from ..constants import DATA_DIR


def to_base64(img):
    with open(img, "rb") as im:
        img_bytes = im.read()
    base64_str = "base64://" + base64.b64encode(img_bytes).decode("utf-8")
    return base64_str


def extract_images(event_json: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(event_json)
        return [msg.get("data", {}) for msg in data.get("message", []) if msg.get("type") == "image"]
    except Exception:
        return []


async def _download_image(bot: Bot, image_data: dict[str, Any]) -> bytes:
    url = image_data.get("url")
    if not url and image_data.get("file"):
        try:
            info = await bot.get_image(file=image_data["file"])
            url = info.get("url") or info.get("file")
        except Exception:
            url = ""
    if not url:
        raise RuntimeError("未能获取图片地址")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _maybe_compress_jpeg(raw: bytes) -> tuple[bytes, str]:
    try:
        from io import BytesIO
        from PIL import Image

        image = Image.open(BytesIO(raw))
        image.thumbnail((2200, 2200))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        out = BytesIO()
        image.save(out, format="JPEG", quality=92, optimize=True)
        return out.getvalue(), "image/jpeg"
    except Exception:
        return raw, "image/jpeg"


async def collect_message_images(bot: Bot, event: Event) -> list[dict[str, str]]:
    images = []
    for index, image_data in enumerate(extract_images(event.json())):
        raw = await _download_image(bot, image_data)
        payload, mime = _maybe_compress_jpeg(raw)
        filename = f"mail_recognize_{int(time.time())}_{index}.jpg"
        path = Path(DATA_DIR) / filename
        path.write_bytes(payload)
        images.append({
            "name": filename,
            "path": str(path),
            "dataUrl": f"data:{mime};base64,{base64.b64encode(payload).decode('utf-8')}",
            "barcodeText": "",
        })
    return images
