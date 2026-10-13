"""与外部 WebSocket 服务保持全双工文字通信。"""

import asyncio
import json
import logging
import os
import time

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed


DEFAULT_SERVER_B_URL = "ws://10.42.0.192:8765"
RECONNECT_DELAY_SECONDS = 2
MAX_PENDING_MESSAGES = 100

logger = logging.getLogger(__name__)


class TextWebSocketClient:
    """单个目标地址对应一个异步发送队列和长连接。"""

    def __init__(self, url: str):
        self.url = url
        self.queue = asyncio.Queue(maxsize=MAX_PENDING_MESSAGES)
        self.worker_task = None
        self.send_lock = asyncio.Lock()

    async def enqueue(self, payload: dict):
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker())

        try:
            self.queue.put_nowait(payload)
        except asyncio.QueueFull:
            logger.warning("发送到 WebSocket 服务的文字队列已满，丢弃一条消息")

    async def _worker(self):
        while True:
            try:
                async with connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=20,
                ) as websocket:
                    logger.info("文字 WebSocket 已连接：%s", self.url)

                    sender_task = asyncio.create_task(self._send_loop(websocket))
                    receiver_task = asyncio.create_task(
                        self._receive_loop(websocket)
                    )
                    done, pending_tasks = await asyncio.wait(
                        {sender_task, receiver_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in pending_tasks:
                        task.cancel()
                    await asyncio.gather(*pending_tasks, return_exceptions=True)

                    for task in done:
                        task.result()

                    raise RuntimeError("文字 WebSocket 连接已结束")

            except asyncio.CancelledError:
                raise
            except (OSError, ConnectionClosed, TimeoutError) as error:
                logger.warning("文字 WebSocket 发送失败：%s", error)
                await asyncio.sleep(RECONNECT_DELAY_SECONDS)
            except Exception as error:
                logger.warning("文字 WebSocket 发送失败：%s", error)
                await asyncio.sleep(RECONNECT_DELAY_SECONDS)

    async def _send_loop(self, websocket):
        while True:
            payload = await self.queue.get()
            try:
                async with self.send_lock:
                    await websocket.send(json.dumps(payload, ensure_ascii=False))
            except (OSError, ConnectionClosed):
                # 发送失败时保留这条消息，重连后继续发送。
                await self.queue.put(payload)
                self.queue.task_done()
                raise
            else:
                self.queue.task_done()

    async def _receive_loop(self, websocket):
        """接收 B 发来的文字，并回传确认消息。"""
        async for raw_message in websocket:
            try:
                message = json.loads(raw_message)
            except (TypeError, json.JSONDecodeError):
                message = {"type": "text", "text": str(raw_message)}

            if isinstance(message, dict) and message.get("type") == "text":
                text = message.get("text", "")
                logger.info("收到 B 服务的文字：%s", text)
                acknowledgement = {
                    "type": "ack",
                    "ok": True,
                    "received_type": "text",
                    "timestamp": int(time.time() * 1000),
                }
                async with self.send_lock:
                    await websocket.send(
                        json.dumps(acknowledgement, ensure_ascii=False)
                    )
            else:
                logger.info("收到 B 服务消息：%s", message)


_clients = {}


def _get_server_b_url(configured_url: str | None = None) -> str:
    if configured_url:
        return configured_url
    return os.getenv("XIAOZHI_TEXT_WS_URL", DEFAULT_SERVER_B_URL)


async def enqueue_text_to_b(
    text: str,
    session_id: str = "",
    device_id: str = "",
    url: str | None = None,
):
    """异步排队一条文字消息，不等待 B 服务端的网络响应。"""
    if text is None or not str(text).strip():
        return

    target_url = _get_server_b_url(url)
    client = _clients.get(target_url)
    if client is None:
        client = TextWebSocketClient(target_url)
        _clients[target_url] = client

    await client.enqueue(
        {
            "type": "text",
            "role": "user",
            "text": str(text),
            "session_id": session_id or "",
            "device_id": device_id or "",
            "timestamp": int(time.time() * 1000),
        }
    )
