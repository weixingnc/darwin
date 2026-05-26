"""Feishu WebSocket 适配器

架构：
- lark-oapi SDK 运行在独立线程，维护 WebSocket 长连接
- 通过 asyncio.Queue 把消息从 SDK 线程传到主 event loop
- Runtime 通过 set_message_handler() 接收消息
"""
import asyncio
import json
import logging
import threading
from typing import Any

from .base import ChannelAdapter, InboundMessage

logger = logging.getLogger(__name__)


class FeishuAdapter(ChannelAdapter):
    """Feishu WebSocket 长连接适配器"""

    name = "feishu"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

        self._client: Any = None
        self._running = False
        self._ws_thread: threading.Thread | None = None
        self._inbound_queue: asyncio.Queue[InboundMessage] = asyncio.Queue()

    async def connect(self) -> None:
        self._running = True

        dispatcher = (
            EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(self._on_lark_message)
            .build()
        )

        self._client = LarkWSClient(
            app_id=self.app_id,
            app_secret=self.app_secret,
            event_handler=dispatcher,
            auto_reconnect=True,
        )

        self._ws_thread = threading.Thread(
            target=self._run_lark_loop,
            name="feishu-ws",
            daemon=True,
        )
        self._ws_thread.start()

        logger.info("[feishu] WebSocket 连接启动中...")

        # 启动消息派发协程
        asyncio.create_task(self._dispatch_loop())

    def _run_lark_loop(self) -> None:
        """lark-oapi SDK 在独立线程运行（阻塞）"""
        try:
            self._client.start()
        except Exception as e:
            logger.error(f"[feishu] WebSocket 线程异常: {e}")

    async def _dispatch_loop(self) -> None:
        """从队列取消息，转发给 handler"""
        while self._running:
            try:
                msg = await asyncio.wait_for(
                    self._inbound_queue.get(),
                    timeout=1.0
                )
                await self._dispatch(msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[feishu] 派发消息异常: {e}")

    async def disconnect(self) -> None:
        self._running = False
        logger.info("[feishu] 已断开")

    async def send(self, chat_id: str, content: str) -> None:
        """发送文本消息"""
        if not self._client:
            raise RuntimeError("[feishu] 未连接")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_sync, chat_id, content)

    def _send_sync(self, chat_id: str, content: str) -> None:
        """同步发送（在 executor 中运行）"""
        req = (
            CreateMessageRequestBuilder()
            .receive_id(chat_id)
            .msg_type("text")
            .content(json.dumps({"text": content}))
            .build()
        )
        resp = self._client.im.v1.message.create(req)
        if resp.code() != 0:
            raise RuntimeError(f"[feishu] 发送失败: {resp.msg()}")

    def _on_lark_message(self, data: Any) -> None:
        """SDK 事件回调（运行在 lark-oapi 线程）"""
        try:
            event = getattr(data, "event", None)
            if not event:
                return

            msg_event = getattr(event, "message", None)
            if not msg_event:
                return

            content_str = getattr(msg_event, "content", "{}")
            try:
                content_obj = json.loads(content_str)
            except Exception:
                content_obj = {"text": content_str}

            text = content_obj.get("text", "")
            if not text:
                logger.warning(f"[feishu] 消息文本为空: content={content_str[:100]}")
                return

            # 获取发送者 ID
            sender = getattr(event, "sender", None) or {}
            sender_id_obj = getattr(sender, "sender_id", None) or {}
            sender_id = getattr(sender_id_obj, "open_id", "") or ""

            inbound = InboundMessage(
                platform="feishu",
                sender_id=sender_id,
                chat_id=getattr(msg_event, "chat_id", "") or "",
                content=text,
                message_id=getattr(msg_event, "message_id", "") or None,
                raw={"event": data},
            )

            logger.info(f"[feishu] 收到消息: sender={sender_id} chat_id={getattr(msg_event, 'chat_id', '')} text={text[:50]}")
            # 放入队列（线程安全）
            asyncio.run_coroutine_threadsafe(
                self._inbound_queue.put(inbound),
                asyncio.get_running_loop()
            )
        except Exception as e:
            logger.error(f"[feishu] 解析消息异常: {e}")


# ---------------------------------------------------------------------------
# 以下为占位导入，运行时依赖 lark-oapi
# 实际使用时通过 config.yaml 配置 appId/appSecret，gateway 在启动时检查
# ---------------------------------------------------------------------------
try:
    from lark_oapi.api.im.v1 import CreateMessageRequestBuilder
    from lark_oapi.event.dispatcher_handler import EventDispatcherHandler
    from lark_oapi.ws.client import Client as LarkWSClient
except ImportError:
    LarkWSClient = None
    EventDispatcherHandler = None
    CreateMessageRequestBuilder = None
