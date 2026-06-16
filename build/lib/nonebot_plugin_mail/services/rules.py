# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：AI 结果归一化：日期、邮件类型、条码、澳门收件人、错误项

import datetime
import re
import uuid
from typing import Any

from .contacts import is_macau_contact, normalize_text, to_ai_contact, unique
from .matcher import match_contact


def normalize_mail_type(type_text: str) -> str:
    type_text = str(type_text or "").strip()
    if "挂" in type_text:
        if "包" in type_text or "刷" in type_text:
            return "挂号印刷品小包"
        elif "简" in type_text or "簡" in type_text:
            return "挂号邮简"
        elif "片" in type_text:
            return "挂号明信片"
        elif "约投" in type_text:
            return "约投挂号"
        else:
            return "挂号信"
    elif "片" in type_text:
        if "给据" in type_text:
            if "际" in type_text:
                return "国际给据明信片"
            else:
                return "给据明信片"
        else:
            return "明信片"
    elif "简" in type_text or "簡" in type_text:
        return "邮简"
    elif "信" in type_text or "邮" in type_text or "郵" in type_text:
        if "国际" in type_text:
            return type_text
        return "平信"
    elif "刷" in type_text:
        return "平常印刷品"
    elif "保价" in type_text:
        return "保价回执信函"
    elif type_text == "平":
        return "平信"
    else:
        return type_text


def normalize_tracking_token(token: str):
    token = str(token or "").strip().lower()
    no_words = {"无", "没", "no", "冇", "🈚", "-", "na", "n/a", "null", "none"}
    if not token:
        return None
    if any(word in token for word in no_words):
        return None
    return token


def normalize_tracking(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if re.match(r"^(无|没|no|none|冇|-|na|n/a|null)$", text, re.I):
        return ""
    return re.sub(r"\s+", "", text).upper()


def normalize_date(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if not match:
        return ""
    yyyy, mm, dd = match.group(1), match.group(2).zfill(2), match.group(3).zfill(2)
    try:
        datetime.date(int(yyyy), int(mm), int(dd))
    except ValueError:
        return ""
    return f"{yyyy}-{mm}-{dd}"


def today_shanghai() -> str:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()


def infer_mail_type(tracking_no: str, evidence: dict[str, Any], looks_macau: bool) -> str:
    code = str(tracking_no or "").upper()
    color = str(evidence.get("barcodeColor") or "")
    if looks_macau and not code:
        return "国际平信"
    if looks_macau and code.startswith("R"):
        return "国际挂号信"
    if code.startswith("SA") or re.search(r"棕|黄|咖啡|褐", color):
        return "挂号印刷品小包"
    if re.match(r"^X[ABCD]", code) or "绿" in color:
        return "挂号信"
    if re.match(r"^(7000|7120)", code) or "黑白" in color:
        return "平信"
    return ""


def validate_party(party: dict[str, Any] | None, contacts: list[dict[str, Any]], fallback_text: str = ""):
    party = party or {}
    contact_id = party.get("contactId") or ""
    found = next((c for c in contacts if c.get("id") == contact_id), None)
    fallback = None if found else match_contact(fallback_text or party.get("matchedText") or "", contacts)
    return {
        "contactId": contact_id if found else (fallback.get("id") if fallback else ""),
        "matchedText": str(party.get("matchedText") or ""),
        "confidence": float(party.get("confidence") or 0) if found else (fallback.get("score") if fallback else 0),
    }


def normalize_ai_record(raw: dict[str, Any], image_name: str, contacts: list[dict[str, Any]], image: dict[str, Any] | None = None):
    image = image or {}
    evidence = raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}
    sender_text = " ".join(filter(None, [raw.get("sender", {}).get("matchedText") if isinstance(raw.get("sender"), dict) else "", evidence.get("senderText")]))
    recipient_text = " ".join(filter(None, [
        raw.get("recipient", {}).get("matchedText") if isinstance(raw.get("recipient"), dict) else "",
        evidence.get("recipientText"),
        evidence.get("destinationText"),
    ]))
    sender = validate_party(raw.get("sender"), contacts, sender_text)
    recipient = validate_party(raw.get("recipient"), contacts, recipient_text)
    tracking_no = normalize_tracking(image.get("barcodeText") or raw.get("trackingNo") or "")
    looks_macau = bool(re.search(r"澳门|澳門|macau", " ".join(str(x or "") for x in [
        evidence.get("destinationText"), evidence.get("recipientText"), raw.get("note"), raw.get("mailType")
    ]), re.I))

    recipient_contact_id = recipient["contactId"]
    if looks_macau or re.search(r"chan\s+k[uw]ok\s+cheng", str(evidence.get("recipientText") or ""), re.I):
        macau_contact = next((c for c in contacts if to_ai_contact(c).get("macauRecipient") or is_macau_contact(c)), None)
        if macau_contact:
            recipient_contact_id = macau_contact["id"]

    send_date = normalize_date(raw.get("sendDate") or "") or today_shanghai()
    mail_type = normalize_mail_type(raw.get("mailType") or infer_mail_type(tracking_no, evidence, looks_macau))
    raw_note = str(raw.get("note") or "").strip()
    note = f"仅供参考：{raw_note}" if raw_note else "仅供参考"
    errors = [str(x) for x in raw.get("errors", []) if x] if isinstance(raw.get("errors"), list) else []
    if not sender["contactId"]:
        errors.append("寄件人未能匹配联系人，请手动选择")
    if not recipient_contact_id:
        errors.append("收件人未能匹配联系人，请手动选择")
    if not raw.get("sendDate"):
        errors.append("未识别到清晰邮戳日期，已默认使用当天 UTC+8")

    return {
        "clientId": str(uuid.uuid4()),
        "imageName": image_name,
        "trackingNo": tracking_no,
        "senderId": sender["contactId"] or "",
        "recipientId": recipient_contact_id or "",
        "sendDate": send_date,
        "mailType": mail_type,
        "note": note,
        "confidence": {"sender": sender["confidence"], "recipient": recipient["confidence"]},
        "evidence": evidence,
        "barcode": {"source": "group-image-ai", "values": []},
        "errors": unique(errors),
    }
