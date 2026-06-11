# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：配置：Notion、AI_BASE_URL、AI_API_KEY、AI_MODEL、数据库 ID

from pydantic import BaseModel
from nonebot import get_driver


class MailConfig(BaseModel):
    notion_token: str = ""
    notion_version: str = "2025-09-03"
    ras_data_source_id: str = "31e70d82-c716-80ba-b4d2-000b1892f62c"
    ras_database_id: str = "31e70d82-c716-80d3-9f2d-e73dcc4033b3"
    contact_data_source_id: str = "31e70d82-c716-8034-b23d-000ba20878af"
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o"
    mail_image_max_count: int = 12
    mail_group_blacklist:list[int] = [631145926, 1072293499]


def _dump_driver_config(raw_config):
    if isinstance(raw_config, dict):
        return raw_config

    if hasattr(raw_config, "dict"):
        try:
            return raw_config.dict()
        except Exception:
            pass

    if hasattr(raw_config, "model_dump"):
        try:
            return raw_config.model_dump()
        except Exception:
            pass

    data = {}
    for field in MailConfig.__fields__:
        if hasattr(raw_config, field):
            data[field] = getattr(raw_config, field)
    return data


def get_config() -> MailConfig:
    raw_config = get_driver().config
    config_data = _dump_driver_config(raw_config)
    if hasattr(MailConfig, "model_validate"):  # 兼容pydantic v1/2
        return MailConfig.model_validate(config_data)
    return MailConfig.parse_obj(config_data)


config = get_config()
