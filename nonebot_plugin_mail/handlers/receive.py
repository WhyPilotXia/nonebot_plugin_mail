# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：“签收/收件”

import random
import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.log import logger
from nonebot.params import ArgStr
from nonebot.typing import T_State

from .utils import MsgText
from ..constants import SPECIAL_CAKE_ID, SPECIAL_YUN_ID
from ..services.contacts import get_contacts, get_key_by_qq, get_name_by_uuid, qq_map, qqmap
from ..services.notion import mark_signed_from_input, query_recent_mails_by_addressee, simplify_mail_results

receive = on_command("签收", priority=5, block=True, aliases={"收件"})
label_to_page_id = {}


@receive.handle()
async def _(state: T_State, bot: Bot, event: GroupMessageEvent):
    contacts = await get_contacts()
    qq_str = event.get_user_id()
    nickname = event.sender.nickname
    await receive.send(f"你好呀{nickname},让我帮你查询一下你有没有在途的邮件呢")
    qqmap(contacts)
    query_addressee = get_key_by_qq(event.get_user_id())
    query_result = query_recent_mails_by_addressee(addressee_id=query_addressee, days=7, limit=10, rec=True)
    mails = simplify_mail_results(query_result)
    if not mails:
        if qq_str in qq_map.get(SPECIAL_CAKE_ID, []):
            query_message = random.choice(["可恶的蛋糕，你没有等待签收的邮件，是不是因为诅咒的人太多了没人写给你？"])
        elif qq_str in qq_map.get(SPECIAL_YUN_ID, []):
            query_message = random.choice(["云云，你没有等待签收的邮件，要不去gayhub找找同好？"])
        else:
            query_message = f"{nickname}，你目前没有未签收的邮件！快让别人多寄寄给你吧"
        await receive.finish(query_message)
    else:
        query_message = f"""{f"查询到{len(mails)}条，请回复编号以签收" if len(mails) <= 10 else "寄给你的信真是太多了，我只能显示最近10条哦，先签收这一轮的吧！"}："""
        for i, mail in enumerate(mails):
            label = chr(65 + i)
            label_to_page_id[label] = mail["page_id"]
            lines = [f"--- 第 {label} 条 ---", f"寄出日期: {mail['寄出日期']}", f"类别: {mail['备注']}"]
            if mail["邮件编号"]:
                lines.append(f"邮件编号: {mail['邮件编号']}")
            lines.append(f"寄件人: {await get_name_by_uuid(mail['寄件人_uuid'], contacts)}")
            query_message += "\n" + "\n".join(lines) + "\n"
        await receive.send(query_message)


@receive.got("a1")
async def _(state: T_State, bot: Bot, event: MessageEvent, lst: str = ArgStr("a1")):
    msgtext = MsgText(event.json())
    s = msgtext.upper()
    result = []
    for ch in re.findall(r"[A-J]", s):
        if ch not in result:
            result.append(ch)
    if not result:
        await receive.finish("输入无效！请稍后重试！")
    else:
        parse_letters = result
        updated = mark_signed_from_input(parse_letters, label_to_page_id)
        logger.info("已更新如下页面：" + str(updated))
        await receive.finish(f"已签收第 {','.join(parse_letters)} 条")
