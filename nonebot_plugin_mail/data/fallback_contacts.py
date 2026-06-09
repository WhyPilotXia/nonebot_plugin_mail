# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：叶恩杰项目 FALLBACK_CONTACTS 转 Python

import hashlib
from typing import Any


def contact(
    name: str,
    phone: str,
    postcode1: str,
    address1: str,
    postcode2: str,
    address2: str,
    qq: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extra = extra or {}
    local_id = hashlib.sha1(f"{name}|{qq}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": extra.get("id") or f"local-{local_id}",
        "name": name,
        "phone": phone,
        "email": "",
        "postcode1": postcode1,
        "address1": address1,
        "postcode2": postcode2,
        "address2": address2,
        "qq": qq,
        "url": "",
        "source": "fallback",
        "aliases": extra.get("aliases", []),
        "macauRecipient": bool(extra.get("macauRecipient", False)),
    }

try:
    from .fallback_contacts_privacy import FALLBACK_CONTACTS as FALLBACK_CONTACTS
except ImportError:    # 此为示例，按此格式增加你的通讯录
    FALLBACK_CONTACTS = [
            contact("王xx（工亚xxx）", "153xxx", "730xxx", "甘肃省兰州市xxxx校区", "", "", "192xxxx"),
            contact("陳xx（诺x）", "172xxx", "43xxx", "湖北省武xxx", "",
                    "澳门地址：AI 识别到澳门或 Chan Kuok Cheng 时匹配此联系人", "90xxx", {
                        "aliases": ["陈国政", "陳國政", "诺斯", "Chan Kuok Cheng", "Chan Kwok Cheng"],
                        "macauRecipient": True,     # 硬编码示例
                    }),
    ]
