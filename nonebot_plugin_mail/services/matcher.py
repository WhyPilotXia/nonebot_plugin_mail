# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：联系人匹配：电话、QQ、姓名/别名、地址片段评分
# 匹配内容	    分数	    优先级
# 电话号码	    0.98	最高
# QQ 号	        0.90	很高
# 完整姓名 / 昵称	0.86	高
# 地址前 12 字符	0.82	中等
# 纯姓名（无昵称）	0.76	最低合格线
import re
from typing import Any

from .contacts import normalize_text, to_ai_contact, unique


def match_contact(text: str, contacts: list[dict[str, Any]]):
    haystack = normalize_text(text)
    if not haystack:
        return None

    candidates = []
    for raw_contact in contacts:
        contact_item = to_ai_contact(raw_contact)
        score = 0.0
        names = unique([contact_item.get("name"), *(contact_item.get("aliases") or [])])
        for name in names:
            normalized_name = normalize_text(name)
            if normalized_name and normalized_name in haystack:
                score = max(score, 0.86)
            plain_name = re.sub(r"[（(].*?[）)]", "", normalized_name)
            if plain_name and len(plain_name) >= 2 and plain_name in haystack:
                score = max(score, 0.76)

        for phone in re.split(r"[;,，\s]+", str(contact_item.get("phone") or "")):
            if len(phone) >= 7 and normalize_text(phone) in haystack:
                score = max(score, 0.98)

        for qq in re.split(r"[;,，\s]+", str(contact_item.get("qq") or "")):
            if len(qq) >= 5 and normalize_text(qq) in haystack:
                score = max(score, 0.9)

        for value in [contact_item.get("address1"), contact_item.get("address2")]:
            normalized_address = normalize_text(value)
            if normalized_address and len(normalized_address) >= 8:
                if normalized_address[:12] in haystack or haystack[:12] in normalized_address:
                    score = max(score, 0.82)

        if score >= 0.76:
            candidates.append({"contact": raw_contact, "score": score})

    candidates.sort(key=lambda item: item["score"], reverse=True)
    if not candidates:
        return None
    if len(candidates) > 1 and candidates[0]["score"] == candidates[1]["score"]:
        return None
    return {**candidates[0]["contact"], "score": candidates[0]["score"]}
