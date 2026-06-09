# python3
# -*- coding: utf-8 -*-
# @Version : 0.7.0
# 规划备注：Contact、RecognizeResult、MailRecordDraft 等数据结构

from typing import Any
from pydantic import BaseModel, Field


class Contact(BaseModel):
    id: str
    name: str = ""
    phone: str = ""
    email: str = ""
    postcode1: str = ""
    address1: str = ""
    postcode2: str = ""
    address2: str = ""
    qq: str = ""
    url: str = ""
    source: str = "notion"
    aliases: list[str] = Field(default_factory=list)
    macau_recipient: bool = False

    def to_legacy(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "姓名": self.name,
            "电话": self.phone,
            "邮箱": self.email,
            "地址1": self.address1,
            "邮编1": self.postcode1,
            "地址2": self.address2,
            "邮编2": self.postcode2,
            "QQ": self.qq,
            "url": self.url,
            "source": self.source,
            "aliases": self.aliases,
            "macauRecipient": self.macau_recipient,
        }


class MailRecordDraft(BaseModel):
    sender_id: str = ""
    recipient_id: str = ""
    send_date: str = ""
    tracking_no: str = ""
    mail_type: str = ""
    image_name: str = ""
    note: str = ""
    errors: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
