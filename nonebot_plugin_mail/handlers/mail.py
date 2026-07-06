# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：/mail contacts、/mail records、/mail @某人

from __future__ import annotations

import re

from nonebot import get_driver
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.rule import Rule
from nonebot import logger
from .utils import At
from ..services.contacts import get_contacts, get_key_by_qq, get_name_by_uuid, qqmap
from ..services.notion import (
    archive_mail_record,
    normalize_contact_field,
    query_recent_mails_by_sender,
    simplify_mail_results,
    update_contact_property,
)
from ..services.render import contacts_to_base64_image, latest_mail_records_to_base64_image
from ..config import config

def whitechecker():
    async def _checker(bot: Bot, event: GroupMessageEvent) -> bool:
        if not config.mail_group_whitelist:
            return True
        if event.group_id in config.mail_group_whitelist:
            return True
        return False

    return Rule(_checker)

matcher = on_command("mail", rule=whitechecker(),priority=5, block=True)

PAGE_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$"
)


def is_superuser(user_id: str) -> bool:
    superusers = getattr(get_driver().config, "superusers", set()) or set()
    return str(user_id) in {str(item) for item in superusers}


def normalize_page_id(page_id: str) -> str:
    compact = page_id.strip().replace("-", "")
    if len(compact) != 32:
        return page_id.strip()
    return f"{compact[:8]}-{compact[8:12]}-{compact[12:16]}-{compact[16:20]}-{compact[20:]}"


def split_words(text: str) -> list[str]:
    return [part for part in re.split(r"\s+", text.strip()) if part]


def find_contact(contacts: list[dict], contact_id: str) -> dict | None:
    for item in contacts:
        if item.get("id") == contact_id:
            return item
    return None


def contact_name(contacts: list[dict], contact_id: str) -> str:
    item = find_contact(contacts, contact_id)
    return item.get("姓名") if item else contact_id


def supported_fields_text() -> str:
    return "电话、电子邮箱、地址1、邮编1、地址2、邮编2、QQ"


async def format_mail_rows(rows: list[dict], contacts: list[dict]) -> str:
    if not rows:
        return "没有找到最近寄件记录。"
    lines = []
    for index, mail in enumerate(rows, 1):
        addressee = await get_name_by_uuid(mail.get("收件人_uuid"), contacts) or mail.get("收件人_uuid") or "未知"
        sender = await get_name_by_uuid(mail.get("寄件人_uuid"), contacts) or mail.get("寄件人_uuid") or "未知"
        tracking_no = mail.get("邮件编号") or "无"
        lines.append(
            f"{index}. {mail.get('寄出日期') or '无日期'} "
            f"{mail.get('备注') or '无备注'} "
            f"{sender} -> {addressee} 编号：{tracking_no}"
        )
    return "\n".join(lines)


async def handle_profile_update(
    event: GroupMessageEvent,
    cmd: str,
    at: list,
    contacts: list[dict],
):
    words = split_words(cmd)
    if not words or words[0] not in ("set", "修改"):
        return False

    admin = is_superuser(event.get_user_id())
    target_id = None
    rest = words[1:]

    if at:
        if not admin:
            await matcher.finish("普通用户只能修改自己的信息。")
        target_id = get_key_by_qq(str(at[0]))
        if not target_id:
            await matcher.finish("没有找到被 @ 用户的联系人信息。")
    elif rest and PAGE_ID_RE.match(rest[0]):
        if not admin:
            await matcher.finish("普通用户只能修改自己的信息。")
        target_id = normalize_page_id(rest[0])
        rest = rest[1:]
    else:
        target_id = get_key_by_qq(event.get_user_id())

    if at:
        # @ 段不会出现在纯文本里，剩下的词就是字段和值。
        rest = words[1:]

    if not target_id:
        await matcher.finish("没有找到你的联系人信息，请确认联系人表里的 QQ 是否包含你的 QQ 号。")
    if len(rest) < 2:
        await matcher.finish(f"用法：/mail 修改 字段 新内容\n可修改字段：{supported_fields_text()}")

    field = normalize_contact_field(rest[0])
    if not field:
        await matcher.finish(f"不支持修改“{rest[0]}”。可修改字段：{supported_fields_text()}")
    value = " ".join(rest[1:]).strip()

    try:
        await update_contact_property(target_id, field, value)
    except Exception as e:
        logger.exception("Update contact property failed")
        await matcher.finish(f"更新失败：{e}")

    await get_contacts(force=True)
    name = contact_name(contacts, target_id)
    owner = "你的" if target_id == get_key_by_qq(event.get_user_id()) else f"{name} 的"
    await matcher.finish(f"已更新{owner}{field}：\n{value or '已清空'}")
    return True


async def handle_my_records(event: GroupMessageEvent, cmd: str, at: list, contacts: list[dict]):
    words = split_words(cmd)
    if cmd not in ("我的寄件", "my records", "my record", "sent", "寄件记录") and words[:2] != ["我的", "寄件"]:
        return False

    admin = is_superuser(event.get_user_id())
    target_id = None
    if at:
        if not admin:
            await matcher.finish("普通用户只能查看自己的寄件记录。")
        target_id = get_key_by_qq(str(at[0]))
    else:
        target_id = get_key_by_qq(event.get_user_id())
    if not target_id:
        await matcher.finish("没有找到联系人信息，无法查询寄件记录。")

    result = await query_recent_mails_by_sender(target_id, 10)
    rows = simplify_mail_results(result)
    name = contact_name(contacts, target_id)
    await matcher.finish(f"{name} 最近寄出的记录：\n{await format_mail_rows(rows, contacts)}\n\n删除请发送：/mail 删除 编号 确认删除")
    return True


async def handle_delete_record(event: GroupMessageEvent, cmd: str, at: list, contacts: list[dict]):
    words = split_words(cmd)
    if not words or words[0] not in ("删除", "delete", "del"):
        return False

    admin = is_superuser(event.get_user_id())
    args = words[1:]
    confirmed = bool(args and args[-1] in ("确认", "确认删除", "confirm"))
    if confirmed:
        args = args[:-1]

    if not args:
        await matcher.finish("用法：/mail 删除 编号 确认删除\n先用 /mail 我的寄件 查看编号。")

    if PAGE_ID_RE.match(args[0]):
        if not admin:
            await matcher.finish("只有 superuser 可以按 Notion 页面 ID 删除记录。")
        page_id = normalize_page_id(args[0])
        if not confirmed:
            await matcher.finish(f"将删除记录 {page_id}\n确认请发送：/mail 删除 {page_id} 确认删除")
        await archive_mail_record(page_id)
        await matcher.finish(f"已删除寄件记录：{page_id}")

    if not args[0].isdigit():
        await matcher.finish("删除编号需要是数字。先用 /mail 我的寄件 查看编号。")

    target_id = None
    if at:
        if not admin:
            await matcher.finish("普通用户只能删除自己的寄件记录。")
        target_id = get_key_by_qq(str(at[0]))
    else:
        target_id = get_key_by_qq(event.get_user_id())
    if not target_id:
        await matcher.finish("没有找到联系人信息，无法删除寄件记录。")

    result = await query_recent_mails_by_sender(target_id, 10)
    rows = simplify_mail_results(result)
    index = int(args[0])
    if index < 1 or index > len(rows):
        await matcher.finish(f"编号超出范围。当前可删除记录共 {len(rows)} 条。")

    mail = rows[index - 1]
    if mail.get("寄件人_uuid") != target_id and not admin:
        await matcher.finish("普通用户只能删除自己寄出的记录。")

    summary = await format_mail_rows([mail], contacts)
    if not confirmed:
        confirm_hint = f"/mail 删除 {index} 确认删除"
        if at:
            confirm_hint = f"/mail 删除 @目标用户 {index} 确认删除"
        await matcher.finish(f"将删除这条寄件记录：\n{summary}\n确认请发送：{confirm_hint}")

    await archive_mail_record(mail["page_id"])
    await matcher.finish(f"已删除寄件记录：\n{summary}")
    return True


@matcher.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    contacts = await get_contacts()
    qqmap(contacts)
    cmd = arg.extract_plain_text().strip().lower()
    at = At(event.json())

    if cmd in ("contacts", "联系人", "contact"):
        img = await contacts_to_base64_image()
        await matcher.finish(MessageSegment.image(img))

    elif cmd in ("records", "record", "邮件", "mail"):
        img = await latest_mail_records_to_base64_image(15)
        await matcher.finish(MessageSegment.image(img))

    elif await handle_profile_update(event, cmd, at, contacts):
        return

    elif await handle_my_records(event, cmd, at, contacts):
        return

    elif await handle_delete_record(event, cmd, at, contacts):
        return

    elif at:
        result_blocks = []
        for idx, qq in enumerate(at, 1):
            target_qq = str(qq)
            target_uuid = get_key_by_qq(target_qq)
            if not target_uuid:
                result_blocks.append(f"--- 第 {idx} 位 ---\n" f"QQ：{target_qq}\n" f"没有找到这个联系人的信息哦")
                continue
            target_contact = None
            for c in contacts:
                if c["id"] == target_uuid:
                    target_contact = c
                    break
            if not target_contact:
                result_blocks.append(f"--- 第 {idx} 位 ---\n" f"QQ：{target_qq}\n" f"没有找到这个联系人的详细资料哦")
                continue
            lines = [
                f"--- 第 {idx} 位 ---",
                f"姓名：{target_contact.get('姓名', '') or '无'}",
                f"电话：{target_contact.get('电话', '') or '无'}",
                f"地址1：{target_contact.get('地址1', '') or '无'}",
                f"邮编1：{target_contact.get('邮编1', '') or '无'}",
            ]
            if target_contact.get("地址2"):
                lines.append(f"地址2：{target_contact.get('地址2', '')}")
            if target_contact.get("邮编2"):
                lines.append(f"邮编2：{target_contact.get('邮编2', '')}")
            result_blocks.append("\n".join(lines))
        await matcher.finish("\n\n".join(result_blocks))

    else:
        await matcher.finish(
            "用法：\n"
            "/mail contacts  查看联系人表（全部）\n"
            "/mail records   查看邮件记录（最新15条）\n"
            "/mail @某人      查看该联系人的信息\n"
            "/mail @甲 @乙    按顺序查看多位联系人的信息\n"
            "/mail 修改 字段 内容  修改自己的联系人信息\n"
            "/mail 我的寄件   查看自己最近寄出的记录\n"
            "/mail 删除 编号 确认删除  删除自己的寄件记录"
        )
