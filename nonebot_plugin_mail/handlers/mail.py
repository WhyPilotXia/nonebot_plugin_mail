# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：/mail contacts、/mail records、/mail @某人

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.rule import Rule
from nonebot import logger
from .utils import At
from ..services.contacts import get_contacts, get_key_by_qq, qqmap
from ..services.render import contacts_to_image, latest_mail_records_to_image
from ..config import config

def blackchecker():
    async def _checker(bot: Bot, event: GroupMessageEvent) -> bool:

        if event.group_id in config.group_blacklist:
            logger.info(f"{event.group_id}在mail黑名单。")
            return False
        return True

    return Rule(_checker)

matcher = on_command("mail", rule=blackchecker(),priority=5, block=True)


@matcher.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    contacts = await get_contacts()
    qqmap(contacts)
    cmd = arg.extract_plain_text().strip().lower()
    at = At(event.json())

    if cmd in ("contacts", "联系人", "contact"):
        img_path = await contacts_to_image()
        await matcher.finish(MessageSegment.image(f"file:///{img_path}"))

    elif cmd in ("records", "record", "邮件", "mail"):
        img_path = await latest_mail_records_to_image(15)
        await matcher.finish(MessageSegment.image(f"file:///{img_path}"))

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
            "/mail @甲 @乙    按顺序查看多位联系人的信息"
        )
