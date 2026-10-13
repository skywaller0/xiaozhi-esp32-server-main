"""规则优先、OpenAI 大模型兜底的 LLM Provider。"""

from config.logger import setup_logging
from core.providers.llm.openai.openai import LLMProvider as OpenAILLMProvider
from core.providers.llm.rule_openai.rules import match_command


TAG = __name__
logger = setup_logging()


class LLMProvider(OpenAILLMProvider):
    """简单指令直接返回，其他输入沿用原有 OpenAI Provider。"""

    @staticmethod
    def _match_latest_user_message(dialogue):
        if not isinstance(dialogue, (list, tuple)):
            return None

        for message in reversed(dialogue):
            if not isinstance(message, dict) or message.get("role") != "user":
                continue
            return match_command(message.get("content"))

        return None

    def response(self, session_id, dialogue, **kwargs):
        command = self._match_latest_user_message(dialogue)
        if command is not None:
            logger.bind(tag=TAG).info(f"规则路由命中，直接返回指令: {command}")
            yield command
            return

        yield from super().response(session_id, dialogue, **kwargs)

    def response_with_functions(
        self, session_id, dialogue, functions=None, **kwargs
    ):
        command = self._match_latest_user_message(dialogue)
        if command is not None:
            logger.bind(tag=TAG).info(f"规则路由命中，直接返回指令: {command}")
            yield command, None
            return

        yield from super().response_with_functions(
            session_id,
            dialogue,
            functions=functions,
            **kwargs,
        )
