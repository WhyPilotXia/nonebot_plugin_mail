QQ 邮件登记机器人插件

一个基于 **NoneBot2 + OneBot v11** 的 QQ 机器人插件，用于管理“寄信 / 查件 / 联系人表 / 邮件记录表”等功能，并将数据同步到 **Notion**。

该插件主要适用于“纸质信件往来登记”场景，支持：

- 查询联系人信息
- 新增联系人
- 记录寄件信息
- 查询最近收到的邮件
- 将联系人表 / 邮件记录表导出为图片并发送到群聊
- 通过 QQ `@用户` 自动识别收件人


---

## 功能概览

本插件围绕“邮件登记”构建了四类能力：

### 1. 联系人管理
从 Notion 联系人数据源中读取联系人信息，包括：

- 姓名 / 昵称
- 电话
- 电子邮箱
- 地址 1 / 邮编 1
- 地址 2 / 邮编 2
- QQ 号映射
- Notion 页面链接

也支持向 Notion 中新增联系人。

### 2. 邮件记录管理
从 Notion 邮件记录数据源中读取邮件记录，包括：

- 寄出日期
- 邮件编号
- 收件人
- 寄件人
- 备注 / 邮件类型
- Notion 页面链接

也支持新增邮件记录。

### 3. 群聊指令交互
机器人支持以下主要命令：

- `/mail contacts`：查看联系人表图片
- `/mail records`：查看最新邮件记录图片
- `/寄信`：进入寄件登记流程
- `/查询`：查询最近 7 天内是否有人给自己寄信

### 4. 文本转图片展示
为了避免群聊中长文本刷屏，插件支持把联系人列表、邮件记录列表渲染成图片后发送。

---

## 效果预览

/寄信


<img width="734" height="913" alt="image" src="https://github.com/user-attachments/assets/13c07b97-d8b2-4e05-91b3-71abe3458578" />

<img width="775" height="809" alt="image" src="https://github.com/user-attachments/assets/243f0b2a-cba9-4acf-ba83-8a94f52407cf" />


/查询


<img width="562" height="626" alt="image" src="https://github.com/user-attachments/assets/e67d8d3d-9a1d-4060-8467-576137791ed1" />

<img width="662" height="1067" alt="image" src="https://github.com/user-attachments/assets/7d13fd02-66de-45e5-b4b9-fd4c575a3bbe" />


/mail


<img width="847" height="1092" alt="image" src="https://github.com/user-attachments/assets/c1fafc42-d9ca-46ad-9ba0-632f48dd1842" />
<img width="1466" height="3778" alt="e1876dd600ccdb3fc4ec3ad5352cdf3c" src="https://github.com/user-attachments/assets/b2ea5495-367d-4be2-bb67-03161b8ae351" />
<img width="1466" height="3453" alt="f7f2876c941d312b03afe384cf0faecb" src="https://github.com/user-attachments/assets/8d376413-88a6-4ade-b9b8-2f789a98f2f6" />




