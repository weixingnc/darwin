"""Gateway — Darwin 的消息网关，支持多种平台"""

from .base import ChannelAdapter, InboundMessage
from .feishu import FeishuAdapter

__all__ = ["ChannelAdapter", "InboundMessage", "FeishuAdapter"]