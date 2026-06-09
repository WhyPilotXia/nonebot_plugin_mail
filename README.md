QQ 邮件登记机器人插件

一个基于 NoneBot2 + OneBot v11 的 QQ 机器人文件夹插件，用于管理“寄信 / 查件 / 签收 / 联系人表 / 邮件记录表”，并将数据同步到 Notion。

版本：0.8.0

本版本将原 `mail_v7.py` 单文件插件重构为 `nonebot_plugin_mail/` 文件夹插件，并把叶恩杰项目的信封图片智能识别能力整合为群聊命令流程。

## 功能

- `/mail contacts`：查看联系人表图片
- `/mail records`：查看最新邮件记录图片
- `/mail @某人`：查看联系人信息
- /`寄信` / `寄件` / `寄出`：进入人工寄件登记流程
- /`查询` / `查件`：查询最近 7 天内是否有人给自己寄信
- /`签收` / `收件`：查询并签收未签收邮件
- /`识别信件` / `智能寄信` / `信件识别` / `识别邮件`：群聊发送信封图片，使用视觉 AI 识别后人工确认写入 Notion

## 智能识别流程

1. 群内发送 `/识别信件`。
2. 按提示发送一张或多张信封图片。
3. 插件下载图片并尝试压缩到最长边 2200px、JPEG 质量 0.92。
4. 视觉 AI 识别寄件人、收件人、寄出日期、邮件类型和参考备注。
5. 后端规则校验联系人 ID、日期、邮件类型、澳门收件人规则，并做电话、QQ、姓名、别名、地址兜底匹配。
6. 群内返回识别结果预览。
7. 回复 `确认` 后写入 Notion。

如需修改识别结果，可在确认前回复类似：

```text
收件人 @某人
寄件人 @某人
日期2026-06-09
类型挂号信
编号XA123456789
```

## 配置

在 NoneBot 2环境配置.env或.env.dev中设置：

```env
NOTION_TOKEN=
NOTION_VERSION=2025-09-03
RAS_DATA_SOURCE_ID=31e70d82-c716-80ba-b4d2-000b1892f62c
RAS_DATABASE_ID=31e70d82-c716-80d3-9f2d-e73dcc4033b3
CONTACT_DATA_SOURCE_ID=31e70d82-c716-8034-b23d-000ba20878af
AI_BASE_URL=https://api.exesim.com/v1
AI_API_KEY=
AI_MODEL=Qwen3.6-Plus
MAIL_IMAGE_MAX_COUNT=12
```

## 目录

```text
  nonebot_plugin_mail/
    __init__.py              # 插件入口：PluginMetadata、注册所有 handlers
    config.py                # 配置：Notion、AI_BASE_URL、AI_API_KEY、AI_MODEL、数据库 ID
    models.py                # Contact、RecognizeResult、MailRecordDraft 等数据结构
    constants.py             # 邮件类型、字段名、默认值、正则、澳门规则常量

    services/
      notion.py              # Notion 联系人读取、邮件记录写入/查询/签收
      contacts.py            # 联系人缓存、fallback 合并、QQ 映射、联系人公开字段
      recognizer.py          # 视觉 AI 调用、prompt 构造、AI JSON 解析
      matcher.py             # 联系人匹配：电话、QQ、姓名/别名、地址片段评分
      rules.py               # AI 结果归一化：日期、邮件类型、条码、澳门收件人、错误项
      images.py              # 群聊图片下载、压缩/转 base64、图片临时保存
      render.py              # 联系人表、邮件记录、识别结果预览转图片/文本

    handlers/
      mail.py                # /mail contacts、/mail records、/mail @某人
      send.py                # “寄信/寄件/寄出”人工登记流程
      query.py               # “查询/查件”
      receive.py             # “签收/收件”
      recognize.py           # 识别信件/智能寄信/信件识别/识别邮件 发送信件图片触发智能识别、人工确认、提交 Notion

    data/
      fallback_contacts.py   # notion不可用时的临时contacts
```
