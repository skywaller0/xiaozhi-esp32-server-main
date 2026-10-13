"""简单语音指令规则库。

键是经过标准化后的用户输入，值是直接返回给下游 TTS/控制逻辑的文本。
需要增加规则时，只需继续向 ``COMMAND_RULES`` 添加条目。
"""

import json
import re
from typing import Optional


COMMAND_RULES = {
    "往前走": "往前走",
    "向前走": "往前走",
    "往后走": "往后走",
    "向后走": "往后走",
}

_TRAILING_PUNCTUATION = "。.!！?？,，;；…\"'“”‘’"


def normalize_command(text: str) -> str:
    """去除空白和句末标点，但不改变句子含义。"""
    compact_text = re.sub(r"\s+", "", text.strip())
    return compact_text.rstrip(_TRAILING_PUNCTUATION)


def extract_text(value: object) -> Optional[str]:
    """从纯文本、ASR 字典或 JSON 字符串中提取用户文本。"""
    if isinstance(value, dict):
        value = value.get("content")

    if not isinstance(value, str):
        return None

    stripped_value = value.strip()
    if stripped_value.startswith("{"):
        try:
            parsed_value = json.loads(stripped_value)
        except (json.JSONDecodeError, TypeError):
            parsed_value = None
        if isinstance(parsed_value, dict):
            nested_content = parsed_value.get("content")
            if isinstance(nested_content, str):
                return nested_content

    return value


def match_command(value: object) -> Optional[str]:
    """完整匹配规则并返回响应；未命中时返回 ``None``。"""
    text = extract_text(value)
    if text is None:
        return None
    return COMMAND_RULES.get(normalize_command(text))
