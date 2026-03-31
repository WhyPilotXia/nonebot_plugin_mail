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

本插件围绕“邮件登记”构四类能力：

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


<img width="913" height="1138" alt="image" src="https://github.com/user-attachments/assets/4391dda4-ed6b-43b6-957b-7e8b0f5d5efa" />


<img width="965" height="1002" alt="image" src="https://github.com/user-attachments/assets/04fe8b1d-99fd-45f1-bb45-527967ec2f76" />



/查询


<img width="695" height="784" alt="image" src="https://github.com/user-attachments/assets/3662ce1f-fd5e-43f9-9ab7-aafe865715aa" />


<img width="824" height="1203" alt="image" src="https://github.com/user-attachments/assets/7585870d-854f-4588-ac65-ab773a41f8eb" />



/mail


<img width="847" height="1092" alt="image" src="https://github.com/user-attachments/assets/c1fafc42-d9ca-46ad-9ba0-632f48dd1842" />
<img width="495" height="1266" alt="image" src="https://github.com/user-attachments/assets/4e9059d9-d6c1-4a5a-9880-4e6df51ebd46" />

<img width="514" height="1265" alt="image" src="https://github.com/user-attachments/assets/2ca68ebb-777d-43e9-a49a-e3779c217e3b" />





