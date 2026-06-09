# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：联系人缓存、fallback 合并、QQ 映射、联系人公开字段

import re
import time
from typing import Any

from nonebot.log import logger

from ..config import config
from ..data.fallback_contacts import FALLBACK_CONTACTS
from .notion import query_all_rows, row_to_contact

contacts_cache: dict[str, Any] = {"at": 0.0, "contacts": []}
qq_map: dict[str, list[str]] = {}


def normalize_text(value: Any) -> str:
    return str(value or "").replace(" ", "").replace("\n", "").replace("\t", "").lower()


def unique(items):
    return list(dict.fromkeys([x for x in items if x]))


def is_macau_contact(contact_item: dict[str, Any]) -> bool:
    return bool(re.search(
        r"陳國政|陈国政|诺斯|chan\s+k[uw]ok\s+cheng",
        f"{contact_item.get('name') or contact_item.get('姓名') or ''} {' '.join(contact_item.get('aliases') or [])}",
        re.I,
    ))


def contact_key(contact_item: dict[str, Any]) -> str:
    qq = str(contact_item.get("qq") or contact_item.get("QQ") or "").split(",")[0].strip()
    return qq or normalize_text(contact_item.get("name") or contact_item.get("姓名"))


def merge_contacts(primary: list[dict[str, Any]], fallback: list[dict[str, Any]]):
    by_key = {}
    for item in fallback:
        by_key[contact_key(item)] = item
    for item in primary:
        existing = by_key.get(contact_key(item), {})
        by_key[contact_key(item)] = {**existing, **item, "source": item.get("source") or "notion"}
    merged = []
    for c in by_key.values():
        if is_macau_contact(c):
            c["aliases"] = unique([*(c.get("aliases") or []), "陈国政", "陳國政", "诺斯", "Chan Kuok Cheng", "Chan Kwok Cheng"])
            c["macauRecipient"] = True
        merged.append(c)
    return merged


def to_legacy_contact(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": c.get("id", ""),
        "姓名": c.get("姓名") or c.get("name", ""),
        "电话": c.get("电话") or c.get("phone", ""),
        "邮箱": c.get("邮箱") or c.get("email", ""),
        "地址1": c.get("地址1") or c.get("address1", ""),
        "邮编1": c.get("邮编1") or c.get("postcode1", ""),
        "地址2": c.get("地址2") or c.get("address2", ""),
        "邮编2": c.get("邮编2") or c.get("postcode2", ""),
        "QQ": c.get("QQ") or c.get("qq", ""),
        "url": c.get("url", ""),
        "source": c.get("source", ""),
        "aliases": c.get("aliases", []),
        "macauRecipient": bool(c.get("macauRecipient")),
    }


def to_ai_contact(c: dict[str, Any]) -> dict[str, Any]:
    legacy = to_legacy_contact(c)
    return {
        "id": legacy["id"],
        "name": legacy["姓名"],
        "aliases": legacy.get("aliases") or [],
        "phone": legacy["电话"],
        "qq": legacy["QQ"],
        "postcode1": legacy["邮编1"],
        "address1": legacy["地址1"],
        "postcode2": legacy["邮编2"],
        "address2": legacy["地址2"],
        "source": legacy.get("source", ""),
        "macauRecipient": bool(legacy.get("macauRecipient")),
        "url": legacy.get("url", ""),
    }


def qqmap(data):
    qq_map.clear()
    for item in data:
        legacy = to_legacy_contact(item)
        id_ = legacy.get("id")
        qq_str = legacy.get("QQ", "")
        if qq_str:
            qq_map[id_] = [qq.strip() for qq in re.split(r"[,，;\s]+", qq_str) if qq.strip()]


async def get_contacts(force: bool = False):
    if not force and contacts_cache["contacts"] and time.time() - contacts_cache["at"] < 10 * 60:
        return contacts_cache["contacts"]
    notion_contacts = []
    if config.notion_token and config.contact_data_source_id:
        try:
            rows = await query_all_rows(config.contact_data_source_id)
            notion_contacts = [row_to_contact(row) for row in rows]
            notion_contacts = [c for c in notion_contacts if c.get("name") or c.get("qq") or c.get("phone")]
        except Exception as e:
            logger.warning(f"Notion contacts unavailable, using local fallback: {e}")
    merged = merge_contacts(notion_contacts, FALLBACK_CONTACTS)
    contacts = [to_legacy_contact(c) for c in merged]
    qqmap(contacts)
    contacts_cache.update({"at": time.time(), "contacts": contacts})
    return contacts


def get_key_by_qq(qq_str):
    for key, value in qq_map.items():
        if isinstance(value, list):
            if qq_str in value:
                return key
        else:
            if qq_str == value:
                return key
    return None


async def get_name_by_uuid(uuid, data_list=None):
    if data_list is None:
        data_list = await get_contacts()
    for item in data_list:
        if item["id"] == uuid:
            name = item["姓名"]
            if "蛋糕" in name:
                return "可恶的" + name
            return name
    return None


def public_contact(contact_item: dict[str, Any]) -> dict[str, Any]:
    c = to_ai_contact(contact_item)
    return {
        "id": c["id"],
        "name": c["name"],
        "phone": c["phone"],
        "qq": c["qq"],
        "postcode1": c["postcode1"],
        "address1": c["address1"],
        "postcode2": c["postcode2"],
        "address2": c["address2"],
        "source": c["source"],
        "aliases": c.get("aliases") or [],
    }
