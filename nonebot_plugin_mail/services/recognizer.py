# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：视觉 AI 调用、prompt 构造、AI JSON 解析

import json
from typing import Any

import httpx

from ..config import config
from .contacts import public_contact, to_ai_contact
from .rules import normalize_ai_record


class AiRecognizeError(RuntimeError):
    pass


async def recognize_images(images: list[dict[str, Any]], contacts: list[dict[str, Any]]):
    if not config.ai_api_key:
        raise AiRecognizeError("缺少 AI_API_KEY，请先配置 .env")
    if not images:
        raise AiRecognizeError("请上传至少一张信封图片")
    if len(images) > config.mail_image_max_count:
        raise AiRecognizeError(f"一次最多上传 {config.mail_image_max_count} 张图片")

    trimmed_contacts = [
        {
            "id": c["id"],
            "name": c["name"],
            "aliases": c.get("aliases") or [],
            "phone": c["phone"],
            "qq": c["qq"],
            "postcode1": c["postcode1"],
            "address1": c["address1"],
            "postcode2": c["postcode2"],
            "address2": c["address2"],
            "macauRecipient": bool(c.get("macauRecipient")),
        }
        for c in (to_ai_contact(x) for x in contacts)
    ]
    content = [{"type": "text", "text": build_vision_prompt(trimmed_contacts)}]
    content.extend({"type": "image_url", "image_url": {"url": image["dataUrl"], "detail": "high"}} for image in images)
    ai_json = await call_vision_model(content)
    raw_records = ai_json.get("records") if isinstance(ai_json.get("records"), list) else []
    records = []
    for index, image in enumerate(images):
        raw = next((r for r in raw_records if int(r.get("imageIndex", -1)) == index), None) or (raw_records[index] if index < len(raw_records) else {})
        records.append(normalize_ai_record(raw, image.get("name") or f"图片 {index + 1}", contacts, image))
    return {"records": records, "contacts": [public_contact(c) for c in contacts], "raw": ai_json}


def build_vision_prompt(contacts) -> str:
    return f"""你是一个严谨的中文信封 OCR 与邮件登记助手。请逐张识别用户上传的信封图片，只输出 JSON，不要输出 Markdown。

核心目标：
1. 识别收件人、寄件人、寄出日期、邮件类型、备注；不要读取条码文字。
2. 收件人和寄件人必须从下方联系人库中匹配，不能编造联系人、地址、电话、id。
3. 如果无法确定某一方联系人，contactId 必须为 null，并在 errors 中说明原因。
4. 用户后续会人工校对，所以宁可低置信度报错，也不要臆测。

联系人库 JSON：
{json.dumps(contacts, ensure_ascii=False)}

识别与匹配规则：
- 优先用信封上的姓名、电话、邮编、地址与联系人库匹配；电话和完整地址权重最高，姓名/昵称次之。
- 如果图片中出现“澳门”“澳門”“Macau”，或者收件人为/近似为 “Chan Kuok Cheng / Chan Kwok Cheng / 陈国政 / 陳國政 / 诺斯”，收件人必须匹配到联系人库中 macauRecipient=true 的联系人。
- 不要 OCR 条码下面的数字/字母，不要输出邮件编号。条码编号由系统的普通条码识别器读取；你只需要观察条码区域颜色、是否明显有条码、目的地是否澳门，辅助判断邮件类型。
- 日期只读邮戳、收寄戳或清晰标注的寄出日期。无法识别、没盖戳、看不清时 sendDate 设为 ""，不要猜；系统会默认当天 UTC+8。
- 日期输出 YYYY-MM-DD。如果邮戳只有月日且年份无法确定，可以结合当前日期所在年份推断；不确定仍输出 ""。
- 一个信封可能有多个邮戳/收寄戳，它们的日期 expected 应该一致；如有多个印记，请相互比较后取共同的年月日。
- 邮戳中形如 “2026.06.07.14”、“2026-06-07-14”、“2026/06/07 14” 的最后一段通常是小时/时刻，不是日期。此例日期应为 2026-06-07，不要误判成 14 日。
- 如果多个邮戳日期看起来冲突，优先选择最清晰、最完整、符合 YYYY-MM-DD 或 年.月.日.时 格式的那一个；仍不确定时 sendDate 设为 ""。

邮件类型判断：
- 平信：黑白条码，通常 7000 或 7120 开头。
- 挂号信：条码下方绿色，编号通常以 XA/XB/XC/XD 开头。
- 挂号印刷品小包/挂刷：编号 SA 开头，条码下方棕黄色。
- 国际平信：寄到澳门且没有条码。
- 国际挂号信：寄到澳门且有 R 开头条码。
- 如果类型不符合以上但图片可判断，可用“明信片”“邮简”“平常印刷品”等常见类型；无法判断时用 ""。

参考备注规则：
- note 只写给用户看的参考说明，例如“邮戳较模糊”“疑似挂号信，需人工确认”等。
- note 不会提交到 Notion；提交到 Notion 备注字段的是 mailType。

返回格式必须是：
{{
  "records": [
    {{
      "imageIndex": 0,
      "sender": {{"contactId": null, "matchedText": "", "confidence": 0}},
      "recipient": {{"contactId": null, "matchedText": "", "confidence": 0}},
      "sendDate": "",
      "mailType": "",
      "note": "",
      "evidence": {{
        "barcodeColor": "",
        "destinationText": "",
        "postmarkText": "",
        "senderText": "",
        "recipientText": ""
      }},
      "errors": []
    }}
  ]
}}

严格要求：
- records 数量必须等于图片数量，imageIndex 从 0 开始对应上传顺序。
- contactId 必须来自联系人库 id 或 null。
- 不要输出 trackingNo 字段；即使看到了条码文字也不要抄写。
- 不要加入 JSON 以外的文字。"""


async def call_vision_model(content):
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{config.ai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.ai_api_key}", "Content-Type": "application/json"},
            json={
                "model": config.ai_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "你只输出可解析 JSON，不能输出 Markdown 或解释文字。"},
                    {"role": "user", "content": content},
                ],
            },
        )
    data = response.json()
    if response.status_code >= 400:
        raise AiRecognizeError(data.get("error", {}).get("message") or "AI 接口请求失败")
    text = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not text:
        raise AiRecognizeError("AI 没有返回内容")
    return parse_ai_json(text)


def parse_ai_json(text: str):
    raw = str(text or "").strip()
    if raw.lower().startswith("![image](") or "/t2i/" in raw.lower():
        raise AiRecognizeError("当前 AI 模型返回了图片链接，像是生图模型而不是视觉识别模型。请改用支持图片理解/OCR 的模型")
    candidates = [
        raw,
        raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip(),
        raw[raw.find("{"): raw.rfind("}") + 1] if "{" in raw and "}" in raw else "",
        *list(reversed(extract_json_objects(raw))),
    ]
    for candidate in candidates:
        if not candidate or "{" not in candidate:
            continue
        try:
            return json.loads(candidate)
        except Exception:
            pass
    raise AiRecognizeError("AI 返回不是合法 JSON")


def extract_json_objects(text: str):
    objects = []
    start = -1
    depth = 0
    in_string = False
    escaping = False
    for i, char in enumerate(text):
        if in_string:
            if escaping:
                escaping = False
            elif char == "\\":
                escaping = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                objects.append(text[start:i + 1])
                start = -1
            if depth < 0:
                depth = 0
                start = -1
    return objects
