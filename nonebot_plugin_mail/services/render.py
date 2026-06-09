# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：联系人表、邮件记录、识别结果预览转图片/文本

import datetime
import os
import textwrap

import matplotlib.pyplot as plt

from ..constants import DATA_DIR
from .contacts import get_contacts, get_name_by_uuid
from .notion import get_mail_records


def _safe_filename(name: str) -> str:
    keep = []
    for ch in name:
        if ch.isalnum() or ch in ("_", "-", "."):
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def save_text_to_local_image(text: str, filename: str) -> str:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Segoe UI Emoji",
        "Arial Unicode MS",
    ]
    plt.rcParams["axes.unicode_minus"] = False
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
    ax.axis("off")
    ax.text(0.01, 0.99, final_text, transform=ax.transAxes, fontsize=11, verticalalignment="top", family="sans-serif")
    file_path = os.path.join(DATA_DIR, _safe_filename(filename))
    plt.savefig(file_path, format="png", bbox_inches="tight", pad_inches=0.2, dpi=180)
    plt.close(fig)
    return file_path


async def contacts_to_image() -> str:
    contacts = await get_contacts()
    lines = ["联系人表", f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"总数：{len(contacts)}", "=" * 50]
    for idx, c in enumerate(contacts, 1):
        lines.append(f"{idx}. 姓名：{c.get('姓名', '')}")
        lines.append(f"   电话：{c.get('电话', '')}")
        lines.append(f"   邮箱：{c.get('邮箱', '')}")
        lines.append(f"   QQ：{c.get('QQ', '')}")
        lines.append(f"   地址1：{c.get('地址1', '')}")
        lines.append(f"   邮编1：{c.get('邮编1', '')}")
        lines.append(f"   地址2：{c.get('地址2', '')}")
        lines.append(f"   邮编2：{c.get('邮编2', '')}")
        lines.append(f"   id：{c.get('id', '')}")
        lines.append("-" * 10)
    content = "\n".join(lines)
    return save_text_to_local_image(content, "contacts_all.png")


async def latest_mail_records_to_image(limit: int = 15) -> str:
    async def _build_contact_map():
        contacts = await get_contacts()
        return {c["id"]: c.get("姓名", "") for c in contacts}

    records = get_mail_records()
    contact_map = await _build_contact_map()
    records = sorted(records, key=lambda x: x.get("send_date", "") or "", reverse=True)[:limit]
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


async def render_recognition_text(records: list[dict], contacts: list[dict]) -> str:
    lines = ["识别完成，请核对："]
    for index, record in enumerate(records, 1):
        sender = await get_name_by_uuid(record.get("senderId"), contacts) or "未匹配"
        recipient = await get_name_by_uuid(record.get("recipientId"), contacts) or "未匹配"
        lines.extend([
            f"--- 第 {index} 张 ---",
            f"寄件人：{sender}",
            f"收件人：{recipient}",
            f"寄出日期：{record.get('sendDate') or ''}",
            f"类别：{record.get('mailType') or ''}",
            f"邮件编号：{record.get('trackingNo') or '无'}",
            f"备注：{record.get('note') or ''}",
        ])
        for error in record.get("errors") or []:
            lines.append(f"需确认：{error}")
    lines.append("回复“确认”提交；如需修改，请回复：寄件人@某人 / 收件人@某人 / 日期2026-06-09 / 类型挂号信 / 编号XA123")
    return "\n".join(lines)
