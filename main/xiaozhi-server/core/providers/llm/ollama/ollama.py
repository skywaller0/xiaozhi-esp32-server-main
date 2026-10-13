"""Ollama 的 OpenAI 兼容适配器。"""

from copy import deepcopy
from urllib.parse import urlparse, urlunparse

from openai import OpenAI

from config.logger import setup_logging
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class _ThinkingFilter:
    """过滤模型输出中的思考标签，并正确处理标签跨流式分片的情况。"""

    OPEN_TAG = "<think>"
    CLOSE_TAG = "</think>"

    def __init__(self):
        self._pending = ""
        self._inside_thinking = False

    def feed(self, content):
        if not content:
            return ""

        self._pending += content
        output = []
        while self._pending:
            tag = self.CLOSE_TAG if self._inside_thinking else self.OPEN_TAG
            index = self._pending.find(tag)
            if index >= 0:
                if not self._inside_thinking:
                    output.append(self._pending[:index])
                self._pending = self._pending[index + len(tag) :]
                self._inside_thinking = not self._inside_thinking
                continue

            # 保留可能属于下一分片标签开头的后缀，其余内容可立即处理。
            keep = self._matching_suffix_length(self._pending, tag)
            ready = self._pending[:-keep] if keep else self._pending
            if not self._inside_thinking:
                output.append(ready)
            self._pending = self._pending[-keep:] if keep else ""
            break

        return "".join(output)

    def flush(self):
        visible = "" if self._inside_thinking else self._pending
        self._pending = ""
        return visible

    @staticmethod
    def _matching_suffix_length(value, tag):
        max_length = min(len(value), len(tag) - 1)
        for length in range(max_length, 0, -1):
            if value.endswith(tag[:length]):
                return length
        return 0


class LLMProvider(LLMProviderBase):
    """通过 Ollama 的 ``/v1/chat/completions`` 接口提供流式对话。"""

    def __init__(self, config):
        self.model_name = str(config.get("model_name") or "").strip()
        if not self.model_name:
            raise ValueError("Ollama model_name cannot be empty")

        self.base_url = self._normalize_base_url(
            config.get("base_url", "http://localhost:11434")
        )
        self.timeout = self._positive_number(config.get("timeout"), 120)
        self.temperature = self._optional_number(config.get("temperature"))
        self.max_tokens = self._optional_integer(config.get("max_tokens"))
        self.disable_thinking = self._as_bool(config.get("disable_thinking"), True)
        self.is_qwen3 = self.model_name.lower().startswith("qwen3")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",  # SDK 要求非空；Ollama 本身不会校验该值。
            timeout=self.timeout,
            max_retries=2,
        )
        logger.bind(tag=TAG).info(
            f"Ollama provider ready: model={self.model_name}, endpoint={self.base_url}"
        )

    def response(self, session_id, dialogue, **kwargs):
        request = self._build_request(dialogue, kwargs)
        stream = self.client.chat.completions.create(**request)
        thinking_filter = _ThinkingFilter()

        try:
            for chunk in stream:
                if not getattr(chunk, "choices", None):
                    continue
                content = getattr(chunk.choices[0].delta, "content", "") or ""
                visible = thinking_filter.feed(content)
                if visible:
                    yield visible

            tail = thinking_filter.flush()
            if tail:
                yield tail
        finally:
            stream.close()

    def response_with_functions(self, session_id, dialogue, functions=None, **kwargs):
        request = self._build_request(dialogue, kwargs)
        if functions:
            request["tools"] = functions

        stream = self.client.chat.completions.create(**request)
        thinking_filter = _ThinkingFilter()
        try:
            for chunk in stream:
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta
                tool_calls = getattr(delta, "tool_calls", None)
                if tool_calls:
                    yield None, tool_calls

                visible = thinking_filter.feed(getattr(delta, "content", "") or "")
                if visible:
                    yield visible, None

            tail = thinking_filter.flush()
            if tail:
                yield tail, None
        finally:
            stream.close()

    def _build_request(self, dialogue, overrides):
        messages = deepcopy(dialogue)
        if self.is_qwen3 and self.disable_thinking:
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = str(message.get("content") or "")
                    if not content.lstrip().startswith("/no_think"):
                        message["content"] = f"/no_think {content}"
                    break

        request = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
        }
        temperature = overrides.get("temperature", self.temperature)
        max_tokens = overrides.get("max_tokens", self.max_tokens)
        if temperature is not None:
            request["temperature"] = float(temperature)
        if max_tokens is not None:
            request["max_tokens"] = int(max_tokens)
        return request

    @staticmethod
    def _normalize_base_url(raw_url):
        value = str(raw_url or "").strip()
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Ollama base_url must be a valid HTTP or HTTPS URL")

        path = parsed.path.rstrip("/")
        if not path.endswith("/v1"):
            path = f"{path}/v1"
        return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))

    @staticmethod
    def _positive_number(value, default):
        if value in (None, ""):
            return default
        parsed = float(value)
        if parsed <= 0:
            raise ValueError("timeout must be greater than zero")
        return parsed

    @staticmethod
    def _optional_number(value):
        return None if value in (None, "") else float(value)

    @staticmethod
    def _optional_integer(value):
        return None if value in (None, "") else int(value)

    @staticmethod
    def _as_bool(value, default):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
