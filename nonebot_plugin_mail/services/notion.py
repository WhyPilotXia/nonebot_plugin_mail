# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：Notion 联系人读取、邮件记录写入/查询/签收

import datetime
import time
from typing import Any

from notion_client import Client

from ..config import config

notion = Client(auth=config.notion_token)


def _read_property(prop: dict[str, Any] | None):
    prop = prop or {}
    t = prop.get("type")
    if t == "title":
        return "".join(x.get("plain_text", "") for x in prop.get("title", [])).strip()
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in prop.get("rich_text", [])).strip()
    if t == "phone_number":
        return prop.get("phone_number") or ""
    if t == "email":
        return prop.get("email") or ""
    if t == "url":
        return prop.get("url") or ""
    if t == "number":
        return prop.get("number")
    if t == "select":
        v = prop.get("select")
        return v.get("name", "") if v else ""
    if t == "multi_select":
        return [x.get("name", "") for x in prop.get("multi_select", [])]
    if t == "date":
        v = prop.get("date")
        return v.get("start", "") if v else ""
    if t == "checkbox":
        return prop.get("checkbox", False)
    if t == "relation":
        return [x.get("id") for x in prop.get("relation", [])]
    if t == "status":
        v = prop.get("status")
        return v.get("name", "") if v else ""
    return None


async def query_all_rows(data_source_id: str, page_size: int = 100):
    results = []
    start_cursor = None
    while True:
        kwargs = {"data_source_id": data_source_id, "page_size": page_size}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor
        for i in range(10):
            try:
                resp = notion.data_sources.query(**kwargs)
                break
            except Exception as e:
                if i >= 7:
                    print(e)
                time.sleep(1)
                if i >= 9:
                    raise
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        start_cursor = resp.get("next_cursor")
    return results


def query_latest_rows(data_source_id: str, limit: int):
    for i in range(10):
        try:
            resp = notion.data_sources.query(
                data_source_id=data_source_id,
                page_size=limit,
                sorts=[{"timestamp": "created_time", "direction": "descending"}],
            )
            break
        except Exception as e:
            if i >= 7:
                print(e)
            time.sleep(1)
            if i >= 9:
                raise
    return resp.get("results", [])


def row_to_contact(row: dict[str, Any]) -> dict[str, Any]:
    props = row.get("properties", {})
    return {
        "id": row.get("id", ""),
        "name": _read_property(props.get("姓名/昵称", {})) or "",
        "phone": _read_property(props.get("电话", {})) or "",
        "email": _read_property(props.get("电子邮箱", {})) or "",
        "address1": _read_property(props.get("地址1", {})) or "",
        "postcode1": _read_property(props.get("邮编1", {})) or "",
        "address2": _read_property(props.get("地址2", {})) or "",
        "postcode2": _read_property(props.get("邮编2", {})) or "",
        "qq": _read_property(props.get("QQ", {})) or "",
        "url": row.get("url", ""),
        "source": "notion",
        "aliases": [],
        "macauRecipient": False,
    }


def get_mail_records():
    rows = query_latest_rows(config.ras_data_source_id, 20)
    records = []
    for row in rows:
        props = row.get("properties", {})
        mail_type = _read_property(props.get("备注", {})) or ""
        tracking_no = _read_property(props.get("邮件编号", {})) or ""
        recipients = _read_property(props.get("收件人", {})) or []
        senders = _read_property(props.get("寄件人", {})) or []
        received = _read_property(props.get("签收", {})) or []
        records.append({
            "page_id": row.get("id", ""),
            "send_date": _read_property(props.get("寄出日期", {})) or "",
            "tracking_no": tracking_no,
            "recipient_ids": recipients,
            "sender_ids": senders,
            "note": mail_type,
            "mail_type": mail_type,
            "has_tracking_no": bool(tracking_no),
            "recipient_id": recipients[0] if recipients else "",
            "sender_id": senders[0] if senders else "",
            "received": received if received else False,
            "url": row.get("url", ""),
        })
    return records


def mail_record(DATABASE_ID, SENDER_ID, ADDRESSEE_ID, SEND_DATE, TRACKING_NO, TYPE, title: str = "由QQBot提交"):
    properties = {
        " ": {"title": [{"text": {"content": title}}]},
        "寄件人": {"relation": [{"id": SENDER_ID}]},
        "收件人": {"relation": [{"id": ADDRESSEE_ID}]},
        "寄出日期": {"date": {"start": SEND_DATE}},
        "备注": {"rich_text": [{"text": {"content": TYPE}}]},
        "签收": {"checkbox": False},
    }
    if TRACKING_NO:
        properties["邮件编号"] = {"rich_text": [{"text": {"content": TRACKING_NO}}]}
    for i in range(10):
        try:
            return notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
        except Exception as e:
            if i >= 7:
                print(e)
            time.sleep(1)
            if i >= 9:
                raise


def query_recent_mails_by_addressee(addressee_id: str, days: int, limit: int, rec):
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=int(days))).isoformat()
    filters = [{"property": "收件人", "relation": {"contains": addressee_id}}]
    if rec:
        filters.append({"property": "签收", "checkbox": {"equals": False}})
    else:
        filters.append({"property": "寄出日期", "date": {"on_or_after": start_date}})
    for i in range(10):
        try:
            return notion.data_sources.query(
                data_source_id=config.ras_data_source_id,
                filter={"and": filters},
                sorts=[{"property": "寄出日期", "direction": "descending"}],
                page_size=int(limit),
            )
        except Exception as e:
            if i >= 7:
                print(e)
            time.sleep(1)
            if i >= 9:
                raise


def simplify_mail_results(query_result: dict):
    rows = []
    for item in query_result.get("results", []):
        props = item["properties"]
        title_arr = props.get(" ", {}).get("title", [])
        title_text = "".join(t.get("plain_text", "") for t in title_arr) if title_arr else ""
        send_date = props.get("寄出日期", {}).get("date", {})
        send_date = send_date.get("start") if send_date else None
        remark_arr = props.get("备注", {}).get("rich_text", [])
        remark_text = "".join(t.get("plain_text", "") for t in remark_arr) if remark_arr else ""
        tracking_arr = props.get("邮件编号", {}).get("rich_text", [])
        tracking_no = "".join(t.get("plain_text", "") for t in tracking_arr) if tracking_arr else ""
        sender_rel = props.get("寄件人", {}).get("relation", [])
        sender_id = sender_rel[0]["id"] if sender_rel else None
        addressee_rel = props.get("收件人", {}).get("relation", [])
        addressee_id = addressee_rel[0]["id"] if addressee_rel else None
        rows.append({
            "page_id": item["id"],
            "url": item["url"],
            "title": title_text,
            "寄出日期": send_date,
            "备注": remark_text,
            "邮件编号": tracking_no,
            "寄件人_uuid": sender_id,
            "收件人_uuid": addressee_id,
        })
    return rows


def mark_signed_from_input(parse_letters, label_to_page_id):
    updated_pages = []
    for letter in parse_letters:
        page_id = label_to_page_id.get(letter)
        if page_id:
            for i in range(10):
                try:
                    notion.pages.update(page_id=page_id, properties={"签收": {"checkbox": True}})
                    break
                except Exception as e:
                    if i >= 7:
                        print(e)
                    time.sleep(1)
                    if i >= 9:
                        raise
            updated_pages.append(page_id)
    return updated_pages
