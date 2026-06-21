# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：群聊命令通用消息解析工具

import json
from typing import Union


def At(data: str) -> Union[list[str], list[int], list]:
    """
    检测at了谁，返回[qq, qq, qq,...]
    包含全体成员直接返回['all']
    如果没有at任何人，返回[]
    :param data: event.json()  event: GroupMessageEvent
    :return: list
    """
    try:
        qq_list = []
        data = json.loads(data)
        for msg in data["message"]:
            if msg["type"] == "at":
                if "all" not in str(msg):
                    qq_list.append(int(msg["data"]["qq"]))
                else:
                    return ["all"]
        return qq_list
    except KeyError:
        return []


def MsgText(data: str):
    """
    返回消息文本段内容(即去除 cq 码后的内容)
    :param data: event.json()
    :return: str
    """
    try:
        data = json.loads(data)
        msg_text_list = filter(lambda x: x["type"] == "text" and x["data"]["text"].replace(" ", "") != "", data["message"])
        msg_text = " ".join(map(lambda x: x["data"]["text"].strip(), msg_text_list)).strip()
        return msg_text
    except Exception:
        return ""
