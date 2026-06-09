# python3
# -*- coding: utf-8 -*-
# @Version : 0.8.0
# 规划备注：插件入口：PluginMetadata、注册所有 handlers

from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from .config import MailConfig

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-mail",
    description="QQ 邮件登记机器人插件，支持 Notion 邮件登记、查询、签收和群聊信封图片智能识别。",
    usage=(
        "/mail contacts 查看联系人表\n"
        "/mail records 查看邮件记录\n"
        "寄信 进入人工寄件登记流程\n"
        "查询 查询最近 7 天邮件\n"
        "签收 查询并签收未签收邮件\n"
        "识别信件 使用群聊图片智能识别并登记"
    ),
    type="application",
    homepage="https://github.com/WhyPilotXia/nonebot_plugin_mail",
    config=MailConfig,
    supported_adapters=inherit_supported_adapters("nonebot.adapters.onebot.v11"),
)

from .handlers import mail as mail
from .handlers import query as query
from .handlers import receive as receive
from .handlers import recognize as recognize
from .handlers import send as send
