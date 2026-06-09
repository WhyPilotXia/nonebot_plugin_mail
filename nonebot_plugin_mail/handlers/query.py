# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：“查询/查件”

import random

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.typing import T_State

from ..constants import SPECIAL_CAKE_ID, SPECIAL_YUN_ID
from ..services.contacts import get_contacts, get_key_by_qq, get_name_by_uuid, qq_map, qqmap
from ..services.notion import query_recent_mails_by_addressee, simplify_mail_results

query = on_command("查询", priority=5, block=True, aliases={"查件"})


@query.handle()
async def _(state: T_State, bot: Bot, event: GroupMessageEvent):
    qq_str = event.get_user_id()
    nickname = event.sender.nickname
    await query.send(f"你好呀{nickname},让我帮你查询一下最近有没有人给你寄件呢")
    contacts = await get_contacts()
    qqmap(contacts)
    query_addressee = get_key_by_qq(event.get_user_id())
    query_result = query_recent_mails_by_addressee(addressee_id=query_addressee, days=7, limit=10, rec=False)
    mails = simplify_mail_results(query_result)
    if not mails:
        if qq_str in qq_map.get(SPECIAL_CAKE_ID, []):
            query_message = random.choice(["可恶的蛋糕，遭报应了吧，最近7天内没人给你寄信","这倒霉的蛋糕，是不是你平时诅咒别人太多了？这7天可没人给你写信啊", "真是个讨厌的蛋糕，看来你平常没少咒人，最近一周都没人联系你","这破蛋糕，怕不是你老爱诅咒别人吧，这七天一个给你寄信的都没有","这个可恨的蛋糕，大概是你咒人太多的报应吧，最近七天没人给你寄信"])
        elif qq_str in qq_map.get(SPECIAL_YUN_ID, []):
            query_message = random.choice(["云云，最近7天内没人给你寄信，可惜"])
        else:
            query_message = f"太遗憾了{nickname}，7天内没有人给你寄信啊"
    else:
        query_message = f"""最近 {7} 天内，{f"查询到{len(mails)}条" if len(mails) <= 10 else "寄给你的信真是太多了，你真是个人气王，我只帮你查最近10条哦"}："""
        if qq_str in qq_map.get(SPECIAL_CAKE_ID, []):
            query_message = "坏蛋糕，" + query_message
        elif qq_str in qq_map.get(SPECIAL_YUN_ID, []):
            query_message = "本✌，" + query_message
        for i, mail in enumerate(mails, 1):
            lines = [f"--- 第 {i} 条 ---", f"寄出日期: {mail['寄出日期']}", f"类别: {mail['备注']}"]
            if mail["邮件编号"]:
                lines.append(f"邮件编号: {mail['邮件编号']}")
            lines.append(f"寄件人: {await get_name_by_uuid(mail['寄件人_uuid'], contacts)}")
            query_message += "\n" + "\n".join(lines) + "\n"
    await query.finish(query_message)
