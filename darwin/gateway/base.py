"""渠道适配器抽象"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Awaitable


@dataclass
class InboundMessage:
    """收到的消息"""
    platform: str           # "feishu"
    sender_id: str          # 发送者 ID
    chat_id: str            # 会话 ID
    content: str             # 文本内容
    message_id: str | None = None   # 平台消息 ID
    raw: dict[str, Any] | None = None  # 原始数据


class ChannelAdapter(ABC):
    """渠道适配器基类"""

    name: str = "base"

    # 消息处理器，由 Runtime 设置
    _handler: Callable[[InboundMessage], Awaitable[None]] | None = None

    def set_message_handler(self, handler: Callable[[InboundMessage], Awaitable[None]]) -> None:
        """设置消息处理函数。消息到达时调用 handler(inbound)"""
        self._handler = handler

    @abstractmethod
    async def connect(self) -> None:
        """建立连接（WS 或 HTTP Webhook）"""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        ...

    @abstractmethod
    async def send(self, chat_id: str, content: str) -> None:
        """发送消息到目标会话"""
        ...

    async def _dispatch(self, msg: InboundMessage) -> None:
        """派发消息给 handler"""
        if self._handler:
            await self._handler(msg)
