# python3
# -*- coding: utf-8 -*-
# @Time    : 2026/3/25
# @Author  : lhc
# @Email   : 2743218818@qq.com
# @Co-Author: mr.cloud
# @Version : 4
# @Software: PyCharm
import json
import logging
import random
import asyncio
import time
import datetime
import base64
import requests
import os
import textwrap
import matplotlib.pyplot as plt
from typing import Union, Optional, List
import nonebot
from nonebot.rule import Rule
from nonebot import on_command, on_startswith, on_keyword, on_fullmatch, on_message
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, GROUP_MEMBER
from nonebot.typing import T_State
from nonebot.log import logger
from nonebot.params import ArgPlainText, CommandArg, ArgStr
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, MessageSegment, Message, GroupMessageEvent, \
    Event, escape
from notion_client import Client

NOTION_TOKEN = "ntn_***"
RAS_DATA_SOURCE_ID = "31e70d82-c716-80ba-b4d2-000b1892f62c"
RAS_DATABASE_ID = "31e70d82-c716-80d3-9f2d-e73dcc4033b3"
CONTACT_DATA_SOURCE_ID = "31e70d82-c716-8034-b23d-000ba20878af"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "mail_imgs")
os.makedirs(DATA_DIR, exist_ok=True)

notion = Client(auth=NOTION_TOKEN)

qq_map = {
    "31e70d82-c716-8032-9ccb-c4d2aa34158a": ["3423118775", "3839761587"],
    "31e70d82-c716-812f-a2f2-f8adb7dc8cc9": ["2743218818"],
    "31e70d82-c716-8131-8e40-c550d6c358af": ["3658503541", "1874826835"],
    "31e70d82-c716-8148-95fb-f8e38f1d9292": ["1925879836"],
    "31e70d82-c716-815e-9cce-c216a363a9df": ["8630023"],
    "31e70d82-c716-8172-8088-c4cc856f8422": ["907347520"],
    "31e70d82-c716-8180-9fa9-e6328d4db9c0": ["1920143820"],
    "31e70d82-c716-81a8-b2c2-ca848376185e": ["2176700635"],
    "31e70d82-c716-81ef-9ecb-ec45fbaabaf2": ["2092494182"],
    "31f70d82-c716-8118-9c2f-de89c74c875b": ["2662751570"],
    "31f70d82-c716-81ea-9fe9-cff8aee2d0c2": ["1292465559"],
    "32170d82-c716-81f3-9a23-e5ab265f8f08": ["2300790043"]
}
attempt = 0

def _read_property(prop):
    t = prop.get("type")

    if t == "title":
        return "".join(x.get("plain_text", "") for x in prop.get("title", [])).strip()

    elif t == "rich_text":
        return "".join(x.get("plain_text", "") for x in prop.get("rich_text", [])).strip()

    elif t == "phone_number":
        return prop.get("phone_number") or ""

    elif t == "email":
        return prop.get("email") or ""

    elif t == "url":
        return prop.get("url") or ""

    elif t == "number":
        return prop.get("number")

    elif t == "select":
        v = prop.get("select")
        return v.get("name", "") if v else ""

    elif t == "multi_select":
        return [x.get("name", "") for x in prop.get("multi_select", [])]

    elif t == "date":
        v = prop.get("date")
        return v.get("start", "") if v else ""

    elif t == "checkbox":
        return prop.get("checkbox", False)

    elif t == "relation":
        return [x.get("id") for x in prop.get("relation", [])]

    elif t == "status":
        v = prop.get("status")
        return v.get("name", "") if v else ""

    else:
        return None


def _query_all_rows(data_source_id, page_size=100):
    results = []
    start_cursor = None

    while True:
        kwargs = {
            "data_source_id": data_source_id,
            "page_size": page_size,
        }
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        resp = notion.data_sources.query(**kwargs)
        results.extend(resp.get("results", []))

        if not resp.get("has_more"):
            break

        start_cursor = resp.get("next_cursor")

    return results


def _query_latest_rows(data_source_id, limit):
    resp = notion.data_sources.query(
        data_source_id=data_source_id,
        page_size=limit,
        sorts=[
            {
                "timestamp": "created_time",  # 或 last_edited_time
                "direction": "descending"
            }
        ]
    )
    return resp.get("results", [])


# =========================
# 联系人表：读取
# =========================
def get_contacts():
    rows = _query_all_rows(CONTACT_DATA_SOURCE_ID)
    contacts = []

    for row in rows:
        props = row.get("properties", {})
        row_id = row.get("id")

        # 👉 取 QQ
        qq_value = qq_map.get(row_id, [])

        # 👉 统一格式：全部转成 list
        if isinstance(qq_value, str):
            qq_value = [qq_value]

        contact = {
            "id": row_id,
            "姓名": _read_property(props.get("姓名/昵称", {})),
            "电话": _read_property(props.get("电话", {})),
            "邮箱": _read_property(props.get("电子邮箱", {})),
            "地址1": _read_property(props.get("地址1", {})),
            "邮编1": _read_property(props.get("邮编1", {})),
            "地址2": _read_property(props.get("地址2", {})),
            "邮编2": _read_property(props.get("邮编2", {})),
            "QQNumber": qq_value,  # 👈 加这一行
            "url": row.get("url", ""),
        }

        contacts.append(contact)

    return contacts


# =========================
# 联系人表：写入
# =========================
def create_contact(
        name,
        phone="",
        email="",
        address1="",
        postcode1="",
        address2="",
        postcode2=""
):
    properties = {
        "姓名/昵称": {
            "title": [
                {
                    "text": {
                        "content": name
                    }
                }
            ]
        },
        "电话": {
            "phone_number": phone or None
        },
        "电子邮箱": {
            "email": email or None
        },
        "地址1": {
            "rich_text": [{"text": {"content": address1}}] if address1 else []
        },
        "邮编1": {
            "rich_text": [{"text": {"content": postcode1}}] if postcode1 else []
        },
        "地址2": {
            "rich_text": [{"text": {"content": address2}}] if address2 else []
        },
        "邮编2": {
            "rich_text": [{"text": {"content": postcode2}}] if postcode2 else []
        },
    }

    resp = notion.pages.create(
        parent={"data_source_id": CONTACT_DATA_SOURCE_ID},
        properties=properties
    )
    return resp


# =========================
# 邮件记录表：读取
# =========================
def get_mail_records():
    rows = _query_latest_rows(RAS_DATA_SOURCE_ID, 20)
    records = []

    for row in rows:
        props = row.get("properties", {})

        mail_type = _read_property(props.get("备注", {})) or ""
        tracking_no = _read_property(props.get("邮件编号", {})) or ""
        recipients = _read_property(props.get("收件人", {})) or []
        senders = _read_property(props.get("寄件人", {})) or []

        record = {
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
            "url": row.get("url", "")
        }
        records.append(record)

    return records


# =========================
# 邮件记录表：写入
# =========================
def create_mail_record(
        send_date="",
        tracking_no="",
        recipient_ids=None,
        sender_ids=None,
        note=""
):
    recipient_ids = recipient_ids or []
    sender_ids = sender_ids or []

    properties = {
        "备注": {
            "rich_text": [{"text": {"content": note}}] if note else []
        },
        "邮件编号": {
            "rich_text": [{"text": {"content": tracking_no}}] if tracking_no else []
        },
        "收件人": {
            "relation": [{"id": x} for x in recipient_ids]
        },
        "寄件人": {
            "relation": [{"id": x} for x in sender_ids]
        },
        "寄出日期": {
            "date": {"start": send_date} if send_date else None
        },
    }

    resp = notion.pages.create(
        parent={"data_source_id": RAS_DATA_SOURCE_ID},
        properties=properties
    )
    return resp


# =========================
# 邮件记录表：写入（实际调用）
# =========================
def mail_record(
        DATABASE_ID,
        SENDER_ID,
        ADDRESSEE_ID,
        SEND_DATE,
        TRACKING_NO,
        TYPE
):
    properties = {
        # ⚠️ 这个是标题列（名字是 " "）
        " ": {
            "title": [
                {
                    "text": {
                        "content": f"由QQBot提交"
                    }
                }
            ]
        },

        "寄件人": {
            "relation": [
                {"id": SENDER_ID}
            ]
        },

        "收件人": {
            "relation": [
                {"id": ADDRESSEE_ID}
            ]
        },

        "寄出日期": {
            "date": {
                "start": SEND_DATE
            }
        },

        "备注": {
            "rich_text": [
                {
                    "text": {
                        "content": TYPE
                    }
                }
            ]
        }
    }
    if TRACKING_NO:
        properties["邮件编号"] = {
            "rich_text": [
                {
                    "text": {
                        "content": TRACKING_NO
                    }
                }
            ]
        }
    res = notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties=properties

    )
    return res


# =========================
# 邮件记录表：查询（实际调用）
# =========================
def query_recent_mails_by_addressee(addressee_id: str, days: int = 7, limit: int = 10):
    """
    查询最近 days 天内，收件人为 addressee_id 的邮件记录，最多返回 limit 条
    """
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=int(days))).isoformat()

    response = notion.data_sources.query(
        data_source_id=RAS_DATA_SOURCE_ID,
        filter={
            "and": [
                {
                    "property": "收件人",
                    "relation": {
                        "contains": addressee_id
                    }
                },
                {
                    "property": "寄出日期",
                    "date": {
                        "on_or_after": start_date
                    }
                }
            ]
        },
        sorts=[
            {
                "property": "寄出日期",
                "direction": "descending"
            }
        ],
        page_size=int(limit)
    )

    return response


def simplify_mail_results(query_result: dict):
    """
    把 Notion 原始返回结果整理成更好读的列表
    """
    rows = []

    for item in query_result.get("results", []):
        props = item["properties"]

        # 标题列名字是一个空格 " "
        title_arr = props.get(" ", {}).get("title", [])
        title_text = "".join(
            t.get("plain_text", "") for t in title_arr
        ) if title_arr else ""

        send_date = props.get("寄出日期", {}).get("date", {})
        send_date = send_date.get("start") if send_date else None

        remark_arr = props.get("备注", {}).get("rich_text", [])
        remark_text = "".join(
            t.get("plain_text", "") for t in remark_arr
        ) if remark_arr else ""

        tracking_arr = props.get("邮件编号", {}).get("rich_text", [])
        tracking_no = "".join(
            t.get("plain_text", "") for t in tracking_arr
        ) if tracking_arr else ""

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

def get_key_by_qq(qq_str):
    """
    根据QQ字符串反向查询字典的键
    :param qq_str: 要查询的QQ号（字符串格式）
    :return: 匹配到的键，未找到返回 None
    """
    for key, value in qq_map.items():
        # 判断值是列表 还是 单个字符串
        if isinstance(value, list):
            # 列表：遍历匹配
            if qq_str in value:
                return key
        else:
            # 单个字符串：直接匹配
            if qq_str == value:
                return key
    # 遍历完没找到
    return None


def get_name_by_uuid(uuid, data_list):
    if data_list is None:
        data_list = get_contacts()
    for item in data_list:
        if item["id"] == uuid:
            name = item["姓名"]
            if "蛋糕" in name:
                return "可恶的" + name
            return name
    return None

# =========================
# 示例
# =========================
if __name__ == "__main__":

    # contacts = get_contacts()
    # query_addressee = '31f70d82-c716-81ea-9fe9-cff8aee2d0c2'
    # query_result = query_recent_mails_by_addressee(
    #     addressee_id=query_addressee,
    #     days=7,
    #     limit=10
    # )
    #
    # mails = simplify_mail_results(query_result)
    # if len(mails) == 0:
    #     print("太遗憾没有人给你寄信")
    # query_message = f"""最近 {7} 天内，{f"查询到{len(mails)}条" if len(mails) <= 10 else "寄给你的信真是太多了，你真是个人气王，只能显示最近10条哦"}："""
    # for i, mail in enumerate(mails, 1):
    #     lines = [
    #         f"--- 第 {i} 条 ---",
    #         f"寄出日期: {mail['寄出日期']}",
    #         f"类别: {mail['备注']}",
    #     ]
    #     if mail['邮件编号']:
    #         lines.append(f"邮件编号: {mail['邮件编号']}")
    #     lines.append(f"寄件人: {get_name_by_uuid(mail['寄件人_uuid'], contacts)}")
    #     query_message += "\n" + "\n".join(lines) + "\n"
    # print(query_message)


    # print("=== 联系人读取 ===")
    # contacts = get_contacts()
    # print(contacts[:3])
    #
    # print("\n=== 邮件记录读取 ===")
    # mail_records = get_mail_records()
    # print(mail_records[:3])

    # ===========================
    # 这里测试发件
    # ==========================
    # sender = "31e70d82-c716-8172-8088-c4cc856f8422"
    # addressee = "31e70d82-c716-812f-a2f2-f8adb7dc8cc9"
    # today = datetime.date.today().isoformat()
    # tracking_no = "123123A"
    # type = "测试"
    # sendmail = mail_record(DATABASE_ID=RAS_DATABASE_ID, SENDER_ID=sender, ADDRESSEE_ID=addressee, SEND_DATE=today,
    #                        TRACKING_NO=tracking_no, TYPE=type)
    # print(sendmail)



    # 新增联系人示例
    # resp = create_contact(
    #     name="测试联系人",
    #     phone="13800138000",
    #     email="test@example.com",
    #     address1="北京市朝阳区测试路1号",
    #     postcode1="100000",
    #     address2="上海市浦东新区测试路2号",
    #     postcode2="200000"
    # )
    # print("联系人新增成功:", resp["id"])

    # 新增邮件记录示例
    # 注意 recipient_ids / sender_ids 里填的是联系人表 page id
    # resp = create_mail_record(
    #     send_date="2026-03-25",
    #     tracking_no="TEST123456",
    #     recipient_ids=["31e70d82-c716-812f-a2f2-f8adb7dc8cc9"],
    #     sender_ids=["31e70d82-c716-8180-9fa9-e6328d4db9c0"],
    #     note="平信"
    # )
    # print("邮件记录新增成功:", resp["id"])
    pass




def _safe_filename(name: str) -> str:
    keep = []
    for ch in name:
        if ch.isalnum() or ch in ("_", "-", "."):
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def save_text_to_local_image(text: str, filename: str) -> str:
    """
    把长文本保存成图片，返回本地路径
    """
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    # 控制每行长度，避免一行过长撑爆
    wrapped_lines = []
    for raw_line in text.split("\n"):
        if not raw_line.strip():
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(raw_line, width=45) or [""])

    final_text = "\n".join(wrapped_lines)
    num_lines = len(wrapped_lines)

    fig_height = max(4, num_lines * 0.2 + 0.6)

    fig, ax = plt.subplots(figsize=(10, fig_height))
    ax.axis('off')

    ax.text(
        0.01, 0.99,
        final_text,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment='top',
        family='sans-serif'
    )

    file_path = os.path.join(DATA_DIR, _safe_filename(filename))
    plt.savefig(file_path, format='png', bbox_inches='tight', pad_inches=0.2, dpi=180)
    plt.close(fig)
    return file_path


def contacts_to_image() -> str:
    contacts = get_contacts()

    lines = []
    lines.append("联系人表")
    lines.append(f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"总数：{len(contacts)}")
    lines.append("=" * 50)

    for idx, c in enumerate(contacts, 1):
        lines.append(f"{idx}. 姓名：{c.get('姓名', '')}")
        lines.append(f"   电话：{c.get('电话', '')}")
        lines.append(f"   邮箱：{c.get('邮箱', '')}")
        lines.append(f"   地址1：{c.get('地址1', '')}")
        lines.append(f"   邮编1：{c.get('邮编1', '')}")
        lines.append(f"   地址2：{c.get('地址2', '')}")
        lines.append(f"   邮编2：{c.get('邮编2', '')}")
        lines.append(f"   id：{c.get('id', '')}")
        lines.append("-" * 10)

    content = "\n".join(lines)
    return save_text_to_local_image(content, "contacts_all.png")


def latest_mail_records_to_image(limit: int = 15) -> str:
    def _build_contact_map():
        contacts = get_contacts()
        return {c["id"]: c.get("姓名", "") for c in contacts}

    records = get_mail_records()
    contact_map = _build_contact_map()

    def sort_key(x):
        return x.get("send_date", "") or ""

    records = sorted(records, key=sort_key, reverse=True)
    records = records[:limit]

    lines = []
    lines.append(f"邮件记录表（最新 {len(records)} 条）")
    lines.append(f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 10)

    for idx, r in enumerate(records, 1):
        recipient_name = contact_map.get(r.get("recipient_id", ""), r.get("recipient_id", ""))
        sender_name = contact_map.get(r.get("sender_id", ""), r.get("sender_id", ""))

        lines.append(f"{idx}. 寄出日期：{r.get('send_date', '')}")
        lines.append(f"   类型：{r.get('mail_type', '')}")
        lines.append(f"   备注：{r.get('note', '')}")
        lines.append(f"   邮件编号：{r.get('tracking_no', '')}")
        lines.append(f"   收件人：{recipient_name}")
        lines.append(f"   寄件人：{sender_name}")
        lines.append(f"   页面ID：{r.get('page_id', '')}")
        lines.append("-" * 10)

    content = "\n".join(lines)
    return save_text_to_local_image(content, "mail_latest_15.png")


def to_base64(img):
    with open(img, "rb") as im:
        img_bytes = im.read()
    base64_str = "base64://" + base64.b64encode(img_bytes).decode('utf-8')
    return base64_str


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
        for msg in data['message']:
            if msg['type'] == 'at':
                if 'all' not in str(msg):
                    qq_list.append(int(msg['data']['qq']))
                else:
                    return ['all']
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
        # 过滤出类型为 text 的【并且过滤内容为空的】
        msg_text_list = filter(lambda x: x['type'] == 'text' and x['data']['text'].replace(' ', '') != '',
                               data['message'])
        # 拼接成字符串并且去除两端空格
        msg_text = ' '.join(map(lambda x: x['data']['text'].strip(), msg_text_list)).strip()
        return msg_text
    except:
        return ''


matcher = on_command("mail", priority=5, block=True)


@matcher.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    cmd = arg.extract_plain_text().strip().lower()

    if cmd in ("contacts", "联系人", "contact"):
        img_path = contacts_to_image()
        await matcher.finish(MessageSegment.image(f"file:///{img_path}"))

    elif cmd in ("records", "record", "邮件", "mail"):
        img_path = latest_mail_records_to_image(15)
        await matcher.finish(MessageSegment.image(f"file:///{img_path}"))

    else:
        await matcher.finish(
            "用法：\n"
            "/mail contacts  查看联系人表（全部）\n"
            "/mail records   查看邮件记录（最新15条）"
        )


# 多参数输入实例
# abstract = on_command("test", priority=5, block=True)
#
#
# @abstract.handle()
# async def _(state: T_State, arg: Message = CommandArg()):
#     if arg.extract_plain_text().strip():
#         state["a1"] = arg.extract_plain_text().strip()
#
#
# @abstract.got("abstract", prompt="a1=？")
# async def _(bot: Bot, event: Event, a1: str = ArgStr("a1")):
#     await abstract.send(a1, at_sender=True)
#
#
# @abstract.got("a2", prompt="a2=？")
# async def _(bot: Bot, event: Event, a2: str = ArgStr("a2")):
#     await abstract.send(a2, at_sender=True)
#
#
# @abstract.got("a3", prompt="a3=？")
# async def _(bot: Bot, event: Event, a3: str = ArgStr("a3")):
#     await abstract.finish(a3, at_sender=True)



sendletter = on_command("寄信", priority=5, block=True, aliases={"寄件", "寄出", "send a mail"})


@sendletter.handle()
async def _(state: T_State, bot: Bot, event: GroupMessageEvent):
    global contacts
    global attempt
    attempt=0
    contacts = get_contacts()
    qq_str = event.get_user_id()
    nowhour = datetime.datetime.now().hour
    if qq_str in qq_map["31e70d82-c716-81ef-9ecb-ec45fbaabaf2"]:
        s=random.choice(["是可恶的蛋糕又在寄信，这次又会寄信去诅咒谁呢？", "可恶，蛋糕又要去诅咒人了，这次会诅咒谁？", "真坏，蛋糕又在偷偷写信诅咒了，这次又打算害谁呢？", "糟糕，蛋糕又开始寄信了，这回会盯上谁倒霉？", "烦人的蛋糕又动笔写信诅咒了，这次不知道谁要遭殃了", "哎，蛋糕又寄出诅咒信了，这次轮到谁了？", "可恶的蛋糕又在寄出那封信了，这次又会坑谁呢？", "不好，蛋糕又开始诅咒人了，这回是谁中招？", "蛋糕这个家伙又写信诅咒去了，这次又准备害谁啊？", "糟了，蛋糕又寄信诅咒了，这次谁要倒霉？", "这个蛋糕又在搞事情写信诅咒了，这次又会针对谁呢？", "唉，蛋糕又寄出诅咒信了，这回是谁被盯上？"])
        s+="\n不过话说回来，蛋糕还是不愿意透露学校的收件地址诶，给蛋糕回信的时候得等多久才能收到呢？"
    elif qq_str in qq_map["31e70d82-c716-8180-9fa9-e6328d4db9c0"]:
        s=random.choice(["是淞云又在寄信，这次又会寄信给谁呢？","这次会寄信给谁呢？"])
    elif qq_str in qq_map["31e70d82-c716-8172-8088-c4cc856f8422"]:
        s=f"{'早晨' if nowhour < 12 else ('午安' if nowhour < 18 else '晚安')} 諾寶寶，而家你又要寄信畀邊個呀？"
    elif qq_str in qq_map["31e70d82-c716-81a8-b2c2-ca848376185e"]:
        s=random.choice([f"原来是勤奋的鸟绿哥哥要去寄信了诶？是要给谁寄呢👀","每日一问：鸟绿哥哥又会在什么时候抽奖呢？\n今天你打算给谁寄信"])
    elif qq_str in qq_map["31f70d82-c716-81ea-9fe9-cff8aee2d0c2"]:
        s=f"{'早上好' if (nowhour - 8) % 24 < 12 else ('中午好' if (nowhour - 8) % 24 < 18 else '晚上好')} 英✌，难得寄一次信呢，邮费可不便宜。\n打算寄给谁呢？"
    elif qq_str in qq_map["31e70d82-c716-815e-9cce-c216a363a9df"]:
        s=f"蛋蛋今天难得有空寄信呀？打算寄给谁呢？"
    elif qq_str in qq_map["31e70d82-c716-8148-95fb-f8e38f1d9292"]:
        s=f"从学校到寄件点得走好远吧？这么珍贵的一封信打算寄给谁呢？"

    else:
        s="今天要给谁寄信呢？"
    state["sender"] = get_key_by_qq(event.get_user_id())
    s += "\n你需要直接@出收件人哦，我这边看得到哒！\n中途不要输入其他消息"
    await sendletter.send(s)



@sendletter.got("a1")
async def _(state: T_State, bot: Bot, event: Event, addressee: str = ArgStr("a1")):
    global attempt
    at = At(event.json())
    addressee = get_key_by_qq(str(at[0]))
    state["addressee"] = addressee

    if not addressee:
        if attempt > 3:
            await sendletter.finish("我还是不太懂，下次需要登记时候再叫我吧")
        await sendletter.reject(f"我没太明白你想给谁寄呢？再试一次吧！")
        attempt +=1


@sendletter.got("a2", prompt="那么，寄出哪种类型呢？\n平邮、挂号信、明信片还是印刷品小包呢？")
async def _(state: T_State, bot: Bot, event: Event, type: str = ArgStr("a2")):
    if "挂" in type:
        if "包" in type:
            type = "挂号小包"
        elif "简" in type or "簡" in type:
            type = "挂号邮简"
        elif "片" in type:
            type = "挂号明信片"
        elif "约投" in type:
            type = "约投挂号"
        elif "信" in type:
            type = "挂号信"
    elif "片" in type:
        type = "明信片"
    elif "简" in type or "簡" in type:
        type = "邮简"
    elif "信" in type or "邮" in type or "郵" in type:
        type = "平信"
    else:
        pass
    await sendletter.send(f"是要寄 {type} 吗？这边先记下来了")
    await asyncio.sleep(1+random.randint(1,2)+random.randint(0,10)/10)
    state["type"] = type
    if type in ["平信", "邮简", "明信片"]:
        await sendletter.send(f"如果是{type}的话？能拿到{type}编号/条码吗？如果有的话那就直接打出来吧！")
    else:
        await sendletter.send(f"如果是{type},想必一定有邮件编号吧？快快发在聊天框给我看看吧" + MessageSegment.face(
            2) + MessageSegment.face(2) + MessageSegment.face(2))


@sendletter.got("a3")
async def _(bot: Bot, event: Event, sender: str = ArgStr("sender"), addressee: str = ArgStr("addressee"),
            type: str = ArgStr("type"), tracking_no: str = ArgStr("a3")):
    """
    sender,addressee为uuid
    """
    no = ["无","没", "no", "🈚", "冇", "No", "NO"]
    for i in no:
        if i in tracking_no:
            tracking_no = None
            break

    global contacts
    await sendletter.send(
        f"{'唔，这样啊,那就只能老老实实当最纯正的平信寄咯！' if not tracking_no else ''}那么这封邮件就是由{get_name_by_uuid(sender, contacts)}寄给{get_name_by_uuid(addressee, contacts)}的{type}吧"+'\n'+f"现在是{datetime.date.today().strftime('%y-%m-%d')}，应该是今天寄出的吧？\n那我就先帮你登记下来了哦")

    today = datetime.date.today().isoformat()
    sendmail = mail_record(DATABASE_ID=RAS_DATABASE_ID, SENDER_ID=sender, ADDRESSEE_ID=addressee, SEND_DATE=today,
                           TRACKING_NO=tracking_no, TYPE=type)
    await asyncio.sleep(1+random.randint(1,2)+random.randint(0,10)/10)
    s=f"登记成功！\n\n登记的编号是：“{sendmail['id']}”，查询就靠这个啦！\n\n链接是\n{sendmail['url']}\n现在就可以打开看到哦！"
    if addressee == '31e70d82-c716-81ef-9ecb-ec45fbaabaf2':
        s+="\n诶等等！蛋糕的地址好像不是学校诶？\n他真的能及时收到你寄出的信吗..."
    await sendletter.finish(s)


query = on_command("查询", priority=5, block=True, aliases={"查件"})


@query.handle()
async def _(state: T_State, bot: Bot, event: GroupMessageEvent):
    qq_str = event.get_user_id()
    user = get_key_by_qq(event.get_user_id())
    nickname = event.sender.nickname
    await query.send(f"你好呀{nickname},让我帮你查询一下最近有没有人给你寄件呢")

    query_addressee = get_key_by_qq(event.get_user_id())
    query_result = query_recent_mails_by_addressee(
        addressee_id=query_addressee,
        days=7,
        limit=10
    )

    mails = simplify_mail_results(query_result)
    if not mails:
        if qq_str in qq_map["31e70d82-c716-81ef-9ecb-ec45fbaabaf2"]:
            query_message = random.choice(["可恶的蛋糕，遭报应了吧，最近7天内没人给你寄信","这倒霉的蛋糕，是不是你平时诅咒别人太多了？这7天可没人给你写信啊", "真是个讨厌的蛋糕，看来你平常没少咒人，最近一周都没人联系你","这破蛋糕，怕不是你老爱诅咒别人吧，这七天一个给你寄信的都没有","这个可恨的蛋糕，大概是你咒人太多的报应吧，最近七天没人给你寄信"])
        else:
            query_message=f"太遗憾了{nickname}，7天内没有人给你寄信啊"
    else:
        query_message = f"""最近 {7} 天内，{f"查询到{len(mails)}条" if len(mails) <= 10 else "寄给你的信真是太多了，你真是个人气王，我只帮你查最近10条哦"}："""
        for i, mail in enumerate(mails, 1):
            lines = [
                f"--- 第 {i} 条 ---",
                f"寄出日期: {mail['寄出日期']}",
                f"类别: {mail['备注']}",
            ]
            if mail['邮件编号']:
                lines.append(f"邮件编号: {mail['邮件编号']}")
            lines.append(f"寄件人: {get_name_by_uuid(mail['寄件人_uuid'], contacts)}")
            query_message += "\n" + "\n".join(lines) + "\n"
    await query.finish(query_message)
