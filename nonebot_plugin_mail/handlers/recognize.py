# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：新增：群内发送信件图片触发智能识别、人工确认、提交 Notion

import re

import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.params import ArgStr
from nonebot.typing import T_State
from nonebot.log import logger

from .utils import At, MsgText
from ..config import config
from ..services.contacts import get_contacts, get_key_by_qq, get_name_by_uuid, qqmap
from ..services.images import collect_message_images
from ..services.notion import mail_record
from ..services.recognizer import AiRecognizeError, recognize_images
from ..services.render import render_recognition_text
from ..services.rules import normalize_date, normalize_mail_type, normalize_tracking

recognize = on_command("识别信件", priority=5, block=True, aliases={"智能寄信", "信件识别", "识别邮件"})


def _apply_sender_fallback(records: list[dict], sender_id: str):
    if not sender_id:
        return
    for record in records:
        if not record.get("senderId"):
            record["senderId"] = sender_id
            record["errors"] = [
                error
                for error in record.get("errors", [])
                if error != "寄件人未能匹配联系人，请手动选择"
            ]


@recognize.handle()
async def _(state: T_State, bot: Bot, event: GroupMessageEvent):
    try:
        await bot.call_api('set_msg_emoji_like', group_id=event.group_id, message_id=event.message_id, emoji_id='294',
                       set=True)
    except Exception as e:
        logger.opt(exception=e).warning("贴表情失败")
    contacts = await get_contacts()
    qqmap(contacts)
    state["contacts"] = contacts
    state["sender_qq"] = event.get_user_id()
    await recognize.send("请发送至少一张信封图片，我会识别收件人、寄件人、邮戳日期和邮件类型。")


@recognize.got("images")
async def _(state: T_State, bot: Bot, event: Event):
    contacts = state["contacts"]
    images = await collect_message_images(bot, event)
    if not images:
        await recognize.reject("请发送至少一张信封图片")
    await recognize.send("收到图片，正在识别信封信息，请稍等。")
    try:
        result = await recognize_images(images, contacts)
    except AiRecognizeError as e:
        await recognize.finish(str(e))
    except Exception as e:
        await recognize.finish(f"识别失败：{e}")
    records = result["records"]
    sender_id = get_key_by_qq(state.get("sender_qq", ""))
    _apply_sender_fallback(records, sender_id)
    state["records"] = records
    preview = await render_recognition_text(records, contacts)
    await recognize.send(preview)


@recognize.got("confirm")
async def _(state: T_State, bot: Bot, event: Event, text: str = ArgStr("confirm")):
    contacts = state["contacts"]
    records = state["records"]
    msgtext = MsgText(event.json()) or text
    if msgtext.strip() not in {"确认", "提交", "ok", "OK", "好的"}:
        apply_corrections(records, contacts, event, msgtext)
        preview = await render_recognition_text(records, contacts)
        await recognize.reject(preview)

    contact_ids = {c["id"] for c in contacts}
    for index, record in enumerate(records, 1):
        if record.get("senderId") not in contact_ids:
            await recognize.reject(f"第 {index} 条寄件人未匹配，请手动选择")
        if record.get("recipientId") not in contact_ids:
            await recognize.reject(f"第 {index} 条收件人未匹配，请手动选择")
        if str(record.get("senderId", "")).startswith("local-") or str(record.get("recipientId", "")).startswith("local-"):
            await recognize.reject(f"第 {index} 条联系人只来自本地参考表，缺少 Notion 页面 id。请确认 NOTION_TOKEN 可读取联系人表后重试")

    results = []
    try:
        for record in records:
            created = await mail_record(
                DATABASE_ID=config.ras_database_id,
                SENDER_ID=record["senderId"],
                ADDRESSEE_ID=record["recipientId"],
                SEND_DATE=normalize_date(record.get("sendDate") or "") or record.get("sendDate"),
                TRACKING_NO=normalize_tracking(record.get("trackingNo") or ""),
                TYPE=normalize_mail_type(record.get("mailType") or "平信"),
                title="由AI识图提交",
            )
            results.append(created)
    except httpx.ConnectError as e:
        await recognize.finish(f"Notion 请求异常，请重试: {e}")
        return
    except Exception as e:
        await recognize.finish(f"提交失败：{e}")
        return

    lines = ["登记成功！"]
    for index, res in enumerate(results, 1):
        lines.append(f"第 {index} 条：{res['url']}")
    await recognize.finish("\n".join(lines))


def apply_corrections(records: list[dict], contacts: list[dict], event: Event, text: str):
    if not records:
        return
    index = 0
    match_index = re.search(r"第\s*(\d+)", text)
    if match_index:
        index = max(0, min(len(records) - 1, int(match_index.group(1)) - 1))
    record = records[index]
    at = At(event.json())
    if "寄件人" in text and at:
        uuid = get_key_by_qq(str(at[0]))
        if uuid:
            record["senderId"] = uuid
    if "收件人" in text and at:
        uuid = get_key_by_qq(str(at[-1]))
        if uuid:
            record["recipientId"] = uuid
    date_match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", text)
    if date_match:
        date = normalize_date(date_match.group(1))
        if date:
            record["sendDate"] = date
    type_match = re.search(r"类型\s*[:： ]\s*([^\s]+)", text)
    if not type_match:
        type_match = re.search(r"类别\s*[:： ]\s*([^\s]+)", text)
    if type_match:
        record["mailType"] = normalize_mail_type(type_match.group(1))
    tracking_match = re.search(r"编号\s*[:： ]\s*([A-Za-z0-9\-]+)", text)
    if tracking_match:
        record["trackingNo"] = normalize_tracking(tracking_match.group(1))
    record["errors"] = []
