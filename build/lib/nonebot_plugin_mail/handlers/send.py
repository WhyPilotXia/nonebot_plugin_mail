# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：原 mail_v7 的“寄信/寄件/寄出”人工登记流程

import asyncio
import datetime
import random

import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, MessageSegment
from nonebot.params import ArgStr
from nonebot.typing import T_State

from .utils import At
from ..config import config
from ..constants import (
    SPECIAL_BIRDGREEN_ID,
    SPECIAL_CAKE_ID,
    SPECIAL_DANDAN_ID,
    SPECIAL_HK_ID,
    SPECIAL_SCHOOL_ID,
    SPECIAL_YING_ID,
    SPECIAL_YUN_ID,
)
from ..services.contacts import get_contacts, get_key_by_qq, get_name_by_uuid, qq_map, qqmap
from ..services.notion import mail_record
from ..services.rules import normalize_mail_type, normalize_tracking_token

sendletter = on_command("寄信", priority=5, block=True, aliases={"寄件", "寄出", "send a mail"})
attempt = 0


@sendletter.handle()
async def _(state: T_State, bot: Bot, event: GroupMessageEvent):
    global attempt
    attempt = 0
    contacts = await get_contacts()
    qq_str = event.get_user_id()
    nowhour = datetime.datetime.now().hour
    qqmap(contacts)
    state["lang"] = "zh-cn"
    if qq_str in qq_map.get(SPECIAL_CAKE_ID, []):
        s = random.choice(["是可恶的蛋糕又在寄信，这次又会寄信去诅咒谁呢？", "可恶，蛋糕又要去诅咒人了，这次会诅咒谁？", "真坏，蛋糕又在偷偷写信诅咒了，这次又打算害谁呢？", "糟糕，蛋糕又开始寄信了，这回会盯上谁倒霉？", "烦人的蛋糕又动笔写信诅咒了，这次不知道谁要遭殃了", "哎，蛋糕又寄出诅咒信了，这次轮到谁了？", "可恶的蛋糕又在寄出那封信了，这次又会坑谁呢？", "不好，蛋糕又开始诅咒人了，这回是谁中招？", "蛋糕这个家伙又写信诅咒去了，这次又准备害谁啊？", "糟了，蛋糕又寄信诅咒了，这次谁要倒霉？", "这个蛋糕又在搞事情写信诅咒了，这次又会针对谁呢？", "唉，蛋糕又寄出诅咒信了，这回是谁被盯上？"])
        s += "\n不过话说回来，蛋糕还是不愿意透露学校的收件地址诶，给蛋糕回信的时候得等多久才能收到呢？"
    elif qq_str in qq_map.get(SPECIAL_YUN_ID, []):
        s = "早安" if nowhour < 12 else ("午安" if nowhour < 18 else "晚安") + "捏," + random.choice(["是本✌又在寄信，这次又在想谁呢？","是可爱的云云又在寄信，这次又会寄信去诱惑谁呢？","云云又要去诱惑人了，这次会诱惑谁？"])
    elif qq_str in qq_map.get(SPECIAL_HK_ID, []):
        state["lang"] = "zh-hk"
        s = f"{'早晨' if nowhour < 12 else ('午安' if nowhour < 18 else '晚安')} 諾寶寶，而家你又要寄信畀邊個呀？"
    elif qq_str in qq_map.get(SPECIAL_BIRDGREEN_ID, []):
        s = random.choice([f"原来是勤奋的鸟绿哥哥要去寄信了诶？是要给谁寄呢👀","每日一问：鸟绿哥哥又会在什么时候抽奖呢？\n今天你打算给谁寄信"])
    elif qq_str in qq_map.get(SPECIAL_YING_ID, []):
        s = f"英✌，难得寄一次信呢。\n打算寄给谁呢？"
    elif qq_str in qq_map.get(SPECIAL_DANDAN_ID, []):
        s = f"蛋蛋今天难得有空寄信呀？打算寄给谁呢？"
    elif qq_str in qq_map.get(SPECIAL_SCHOOL_ID, []):
        s = f"从学校到寄件点得走好远吧？这么珍贵的一封信打算寄给谁呢？"
    else:
        s = "今天要给谁寄信呢？"

    state["sender"] = get_key_by_qq(event.get_user_id())
    state["contacts"] = contacts
    if state["lang"] == "zh-cn":
        s += "\n你需要直接@出收件人哦，我这边看得到哒！\n中途不要输入其他消息"
    elif state["lang"] == "zh-hk":
        s += "\n你要直接@返收件人呀，我呢邊睇得到㗎！\n中途唔好輸入其他嘅訊息"
    await sendletter.send(s)


@sendletter.got("a1")
async def _(state: T_State, bot: Bot, event: Event, addressee: str = ArgStr("a1")):
    contacts = state["contacts"]
    at = At(event.json())
    if not at:
        if state["lang"] == "zh-cn":
            await sendletter.finish("我不太明白你的输入，下次需要登记时候再叫我吧！")
        elif state["lang"] == "zh-hk":
            await sendletter.finish("我都係仲未係好明，下次要登記嗰陣再叫我啦！")

    if len(at) > 1:
        addressee_list = []
        name_list = []
        for qq in at:
            uuid = get_key_by_qq(str(qq))
            if uuid:
                addressee_list.append(uuid)
                name_list.append(await get_name_by_uuid(uuid, contacts))
        state["multi"] = True
        state["addressee_list"] = addressee_list
        state["name_list"] = name_list
        state["name_str"] = "，".join(name_list)
        if state["lang"] == "zh-cn":
            await sendletter.send(f"那么现在要给{state['name_str']}寄什么种类呢？\n如果大家都一样，直接输入一个类型就行。\n如果要区分，请按顺序用空格分开，比如：平信 挂号信 明信片")
        elif state["lang"] == "zh-hk":
            await sendletter.send(f"咁而家要寄畀{state['name_str']}嘅係咩種類呢？\n如果全部一樣，直接輸入一個類型就得。\n如果要分開，請按順序用空格隔開，例如：平信 掛號信 明信片")
    else:
        state["multi"] = False
        addressee = get_key_by_qq(str(at[0]))
        state["addressee"] = addressee
        if state["lang"] == "zh-cn":
            await sendletter.send("那么，寄出哪种类型呢？\n平信、挂号信、明信片还是印刷品小包呢？")
        elif state["lang"] == "zh-hk":
            await sendletter.send("咁，寄邊種類型好呢？\n平郵、掛號信、明信片定係印刷品小包呢？")


@sendletter.got("a2")
async def _(state: T_State, bot: Bot, event: Event, type: str = ArgStr("a2")):
    global attempt
    if state.get("multi") == False:
        type = normalize_mail_type(type)
        if state["lang"] == "zh-cn":
            await sendletter.send(f"是要寄 {type} 吗？这边先记下来了")
        elif state["lang"] == "zh-hk":
            await sendletter.send(f"係要寄 {type} 嗎？呢邊先記低咗")
        await asyncio.sleep(1 + random.randint(1, 2) + random.randint(0, 10) / 10)
        state["type"] = type
        if type in ["平信", "邮简", "明信片", "平常印刷品"]:
            if state["lang"] == "zh-cn":
                await sendletter.send(f"如果是{type}的话？能拿到{type}编号/条码吗？如果有的话那就直接打出来吧！")
            elif state["lang"] == "zh-hk":
                await sendletter.send(f"如果係{type}嘅話？可唔可以攞到{type}嘅編號/條碼？如果有嘅話就直接打出嚟啦！")
        else:
            if state["lang"] == "zh-cn":
                await sendletter.send(MessageSegment.text(f"如果是{type},想必一定有邮件编号吧？快快发在聊天框给我看看吧") + MessageSegment.face(2) + MessageSegment.face(2) + MessageSegment.face(2) + MessageSegment.text("邮件编号内请不要输入空格"))
            elif state["lang"] == "zh-hk":
                await sendletter.send(MessageSegment.text(f"如果係{type}嘅話？可唔可以攞到{type}嘅編號/條碼？如果有嘅話就直接打出嚟啦！") + MessageSegment.face(2) + MessageSegment.face(2) + MessageSegment.face(2) + MessageSegment.text("郵件編號內唔要輸入空格"))
        return

    name_list = state["name_list"]
    addressee_list = state["addressee_list"]
    parts = [x.strip() for x in type.strip().split() if x.strip()]
    if not parts:
        if state["lang"] == "zh-cn":
            await sendletter.reject("输入不能为空哦，请重新输入邮件类型。")
        elif state["lang"] == "zh-hk":
            await sendletter.reject("輸入唔可以為空哦，請重新輸入郵件嘅類型。")
    if len(parts) == 1:
        common_type = normalize_mail_type(parts[0])
        state["type_list"] = [common_type for _ in addressee_list]
        if state["lang"] == "zh-cn":
            await sendletter.send("我明白啦，这次大家都是同一种：\n" + "\n".join(f"{name}：{common_type}" for name in name_list) + "\n那么有对应的邮件编号吗？如果有的话请按顺序以空格输入吧！如果部分缺少编号请以 none 占位。如果都沒有只需要输入一个none。")
        elif state["lang"] == "zh-hk":
            await sendletter.send("我明白啦，今次大家都係同一種：\n" + "\n".join(f"{name}：{common_type}" for name in name_list) + "\n咁有冇對應嘅郵件編號？如果有嘅話，請按順序用空格輸入啦！如果有部分冇編號，請用 none 佔位。如果都冇輸入一個 none 就行喇。")
        return
    if len(parts) != len(addressee_list):
        if attempt <= 1:
            attempt += 1
            if state["lang"] == "zh-cn":
                await sendletter.reject(f"输入不正确哦。\n" f"你这次要寄给 {len(addressee_list)} 个人：{'，'.join(name_list)}\n" f"如果不区分，直接输入一个类型就可以；\n" f"如果要区分，请按顺序输入 {len(addressee_list)} 个类型，并用空格隔开。")
            elif state["lang"] == "zh-hk":
                await sendletter.reject(f"輸入唔正確喎。\n" f"你今次要寄畀 {len(addressee_list)} 個人：{'，'.join(name_list)}\n" f"如果唔使分，直接輸入一個類型就得；\n" f"如果要分，請按順序輸入 {len(addressee_list)} 個類型，仲要用空格隔開。")
        else:
            if state["lang"] == "zh-cn":
                await sendletter.finish("我还是不太明白你的意思，稍后再重试吧！")
            elif state["lang"] == "zh-hk":
                await sendletter.finish("我仲係唔太明你嘅意思，等陣再試過啦！")
    normalized_types = [normalize_mail_type(x) for x in parts]
    state["type_list"] = normalized_types
    if state["lang"] == "zh-cn":
        await sendletter.send("好的，我按顺序记下来了：\n" + "\n".join(f"{name}：{mail_type}" for name, mail_type in zip(name_list, normalized_types)) + "\n那么有对应的邮件编号吗？如果有的话请按顺序以空格输入吧！如果部分缺少编号请以 none 占位。")
    elif state["lang"] == "zh-hk":
        await sendletter.send("好嘅，我按順序記低咗：\n" + "\n".join(f"{name}：{mail_type}" for name, mail_type in zip(name_list, normalized_types)) + "\n咁有對應嘅電郵編號嗎？如果有嘅話請按順序用空格輸入啦！如果部分缺少編號請用 none 佔位。")


@sendletter.got("a3")
async def _(bot: Bot, event: Event, state: T_State, tracking_no: str = ArgStr("a3")):
    contacts = state["contacts"]
    sender = state["sender"]
    today = datetime.date.today().isoformat()
    if state.get("multi") == False:
        addressee = state["addressee"]
        type_ = state["type"]
        tracking_no = normalize_tracking_token(tracking_no)
        if state["lang"] == "zh-cn":
            if datetime.datetime.now().hour <= 17:
                await sendletter.send(f"{'唔，这样啊,那就只能老老实实当最纯正的平信寄咯！' if not tracking_no else ''}" f"那么这封邮件就是由{await get_name_by_uuid(sender, contacts)}寄给{await get_name_by_uuid(addressee, contacts)}的{type_}吧\n" f"现在是{datetime.date.today().strftime('%y-%m-%d')}，应该是今天寄出的吧？\n" f"那我就先帮你登记下来了哦")
            else:
                today = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                await sendletter.send(f"{'唔，这样啊,那就只能老老实实当最纯正的平信寄咯！' if not tracking_no else ''}" f"那么这封邮件就是由{await get_name_by_uuid(sender, contacts)}寄给{await get_name_by_uuid(addressee, contacts)}的{type_}吧\n" f"现在是{datetime.date.today().strftime('%y-%m-%d')}，可是邮局现在下班了，那就帮你登记第二天寄出咯")
        elif state["lang"] == "zh-hk":
            if datetime.datetime.now().hour <= 17:
                await sendletter.send(f"{'唔，咁樣啊，咁就唯有老老實實當最純正嘅平信寄啦！' if not tracking_no else ''}" f"咁呢封郵件就係由{await get_name_by_uuid(sender, contacts)}寄俾{await get_name_by_uuid(addressee, contacts)}嘅{type_}啦\n" f"而家係{datetime.date.today().strftime('%y-%m-%d')}，應該係今日寄出嘅吧？\n" f"咁我就先幫你登記咗先啦")
            else:
                today = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                await sendletter.send(f"{'唔，咁樣啊，咁就唯有老老實實當最純正嘅平信寄啦！' if not tracking_no else ''}" f"咁呢封郵件就係由{await get_name_by_uuid(sender, contacts)}寄俾{await get_name_by_uuid(addressee, contacts)}嘅{type_}啦\n" f"而家係{datetime.date.today().strftime('%y-%m-%d')}，郵局而家已經收工咗，我會幫你登記，喺第二日寄出。")
        try:
            sendmail = await mail_record(DATABASE_ID=config.ras_database_id, SENDER_ID=sender, ADDRESSEE_ID=addressee, SEND_DATE=today, TRACKING_NO=tracking_no, TYPE=type_)
        except httpx.ConnectError as e:
            await sendletter.finish(f"Notion 请求异常，请重试: {e}")
            return
        await asyncio.sleep(1 + random.randint(1, 2) + random.randint(0, 10) / 10)
        if state["lang"] == "zh-cn":
            s = f"登记成功！\n\n登记的编号是：“{sendmail['id']}”，查询就靠这个啦！\n\n链接是\n{sendmail['url']}\n现在就可以打开看到哦！"
        elif state["lang"] == "zh-hk":
            s = f"登記成功！\n\n登記嘅編號係：「{sendmail['id']}」，之後查詢就靠呢個啦！\n\n連結係\n{sendmail['url']}\n而家就可以打開睇到喇！"
        if addressee == SPECIAL_CAKE_ID:
            if state["lang"] == "zh-cn":
                s += "\n诶等等！蛋糕的地址好像不是学校诶？\n他真的能及时收到你寄出的信吗..."
            elif state["lang"] == "zh-hk":
                s += "\n欸等等！蛋糕嘅地址好似唔係學校喎？\n佢真係可以準時收到你寄出嘅信嗎..."
        await sendletter.finish(s)

    else:
        addressee_list = state["addressee_list"]
        name_list = state["name_list"]
        type_list = state["type_list"]
        parts = [x.strip() for x in tracking_no.strip().split() if x.strip()]
        if len(parts) == 1 and normalize_tracking_token(parts[0]) is None:
            tracking_list = [None for _ in addressee_list]
        else:
            if len(parts) != len(addressee_list):
                if state["lang"] == "zh-cn":
                    await sendletter.reject(f"输入不正确哦。\n" f"你这次要寄给 {len(addressee_list)} 个人：{'，'.join(name_list)}\n" f"如果大家都没有编号，直接输入一个 none 就可以；\n" f"如果要区分，请按顺序输入 {len(addressee_list)} 个编号，并用空格隔开。\n")
                elif state["lang"] == "zh-hk":
                    await sendletter.reject(f"輸入唔正確喎。\n" f"你今次要寄俾 {len(addressee_list)} 個人：{'，'.join(name_list)}\n" f"如果大家都冇編號，直接輸入一個 none 就可以；\n" f"如果要分開，請按順序輸入 {len(addressee_list)} 個編號，並用空格隔開。\n")
            tracking_list = [normalize_tracking_token(x) for x in parts]
        confirm_lines = []
        for uuid, name, mail_type, trk in zip(addressee_list, name_list, type_list, tracking_list):
            trk = trk if trk else "无"
            confirm_lines.append(f"{name}：{mail_type}，编号：{trk}")
        if state["lang"] == "zh-cn":
            await sendletter.send(f"好哦，这次寄件信息如下：\n" + "\n".join(confirm_lines) + f"\n现在是{datetime.date.today().strftime('%y-%m-%d')}，我这就帮你登记。")
        elif state["lang"] == "zh-hk":
            await sendletter.send(f"好呀，今次寄件資料如下：\n" + "\n".join(confirm_lines) + f"\n而家係{datetime.date.today().strftime('%y-%m-%d')}，我即刻幫你登記。")
        results = []
        try:
            for uuid, mail_type, trk in zip(addressee_list, type_list, tracking_list):
                sendmail = await mail_record(DATABASE_ID=config.ras_database_id, SENDER_ID=sender, ADDRESSEE_ID=uuid, SEND_DATE=today, TRACKING_NO=trk, TYPE=mail_type)
                results.append(sendmail)
        except httpx.ConnectError as e:
            await sendletter.finish(f"Notion 请求异常，请重试: {e}")
            return
        await asyncio.sleep(1 + random.randint(1, 2) + random.randint(0, 10) / 10)
        success_lines = []
        for uuid, res in zip(addressee_list, results):
            name = await get_name_by_uuid(uuid, contacts)
            success_lines.append(f"{name}：{res['url']}")
        if state["lang"] == "zh-cn":
            await sendletter.finish("多人寄件登记成功！\n" + "\n".join(success_lines))
        elif state["lang"] == "zh-hk":
            await sendletter.finish("多人寄件登記成功！\n" + "\n".join(success_lines))
