QQ 邮件登记机器人插件

一个基于 NoneBot2 + OneBot v11 的 QQ 机器人文件夹插件，用于管理“寄信 / 查件 / 签收 / 联系人表 / 邮件记录表”，并将数据同步到 Notion。

版本：0.7.3

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

在 NoneBot 2 环境配置 `.env` 或 `.env.dev` 中设置：
### 示例
```env
NOTION_TOKEN=
RAS_DATA_SOURCE_ID=31e70d82-c716-80ba-b4d2-000b1892f62c
CONTACT_DATA_SOURCE_ID=31e70d82-c716-8034-b23d-000ba20878af
AI_BASE_URL=https://api.exesim.com/v1
AI_API_KEY=
AI_MODEL=Qwen3.6-Plus
MAIL_IMAGE_MAX_COUNT=12
```

### Notion 相关
| 配置项 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `NOTION_TOKEN` | 否，但不建议 | 无 | Notion API 访问令牌，用于读取联系人表、写入邮件记录、签收邮件记录。 |
| `RAS_DATA_SOURCE_ID` | 否，但不建议 | `31e70d82-c716-80ba-b4d2-000b1892f62c` | 邮件记录表的数据源 ID，用于查询邮件记录。 |
| `CONTACT_DATA_SOURCE_ID` | 否，但不建议 | `31e70d82-c716-8034-b23d-000ba20878af` | 联系人表的数据源 ID，用于读取联系人信息。 |

### AI 相关
| 配置项 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `AI_BASE_URL` | 否 | `https://api.openai.com/v1` | 兼容 OpenAI 接口的视觉模型地址。 |
| `AI_API_KEY` | 否 | 无 | 视觉识别接口的访问密钥。 |
| `AI_MODEL` | 否 | `Qwen3.6-Plus` | 识别信封图片时使用的模型名称。 |
| `MAIL_IMAGE_MAX_COUNT` | 否 | `12` | 单次允许上传并识别的最大图片数量。 |


### 说明
- `AI_BASE_URL` 可不填，不填时默认使用 `https://api.openai.com/v1`
- `MAIL_IMAGE_MAX_COUNT` 可不填，不填时默认 `12`
- `NOTION_TOKEN` 不填时，联系人表会尝试使用本地 fallback，但邮件查询、签收和提交 Notion 仍会受限，基本必须

### notion侧配置

- 创建的表应当至少包括 联系人表、邮件记录表
- 联系人表应当至少包含如下列:姓名 / 昵称，电话，邮编 1, 地址 1, 邮编 2, 地址 2, QQ 
- 其中QQ可以用英文逗号分隔多个
- 邮件记录表需要包括：消息来源，签收，收件人，寄出日期，邮件编号，寄件人，备注

参考:

<img width="1426" height="222" alt="image" src="https://github.com/user-attachments/assets/b9d5247f-5dbf-42b4-85fa-78ca8c502b6a" />

<img width="1250" height="404" alt="f3fb19bb-b182-491d-b7ca-10607eea9afd" src="https://github.com/user-attachments/assets/ac436494-39f0-4824-bf2a-09b87536a0ac" />



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


## 示例
/mail @某人


<img width="572" height="383" alt="image" src="https://github.com/user-attachments/assets/35cebe79-e983-4634-8d97-bb671ce99577" />

/寄件

<img width="596" height="811" alt="image" src="https://github.com/user-attachments/assets/857449c6-b346-48ab-9d51-02e9e77d6458" />
<img width="589" height="617" alt="image" src="https://github.com/user-attachments/assets/8da1e710-479f-479a-8ee0-63a227f8a329" />

/查件

<img width="585" height="425" alt="image" src="https://github.com/user-attachments/assets/541d3e9d-df2f-4d7c-ae27-6ab554d849e2" />

/签收

<img width="598" height="939" alt="image" src="https://github.com/user-attachments/assets/369a8072-0db8-4d8a-a2e3-b63634585750" />


/信件识别

<img width="1440" height="7920" alt="IMG_20260609_224224" src="https://github.com/user-attachments/assets/38142b45-72b6-40d6-bada-103ed0f05466" />

