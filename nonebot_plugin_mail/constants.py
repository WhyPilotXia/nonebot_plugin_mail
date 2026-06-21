# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：邮件类型、字段名、默认值、正则、澳门规则常量

from pathlib import Path

from nonebot import require
from nonebot.log import logger

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import get_plugin_data_dir

PLUGIN_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PLUGIN_DIR / "assets"
FONT_PATH = ASSETS_DIR / "simkai.ttf"
DATA_DIR = get_plugin_data_dir() / "mail_imgs"
logger.info(f"Mail cache dir: {DATA_DIR}")
DATA_DIR.mkdir(parents=True, exist_ok=True)

SPECIAL_CAKE_ID = "31e70d82-c716-81ef-9ecb-ec45fbaabaf2"
SPECIAL_YUN_ID = "31e70d82-c716-8180-9fa9-e6328d4db9c0"
SPECIAL_HK_ID = "31e70d82-c716-8172-8088-c4cc856f8422"
SPECIAL_BIRDGREEN_ID = "31e70d82-c716-81a8-b2c2-ca848376185e"
SPECIAL_YING_ID = "31f70d82-c716-81ea-9fe9-cff8aee2d0c2"
SPECIAL_DANDAN_ID = "31e70d82-c716-815e-9cce-c216a363a9df"
SPECIAL_SCHOOL_ID = "31e70d82-c716-8148-95fb-f8e38f1d9292"
