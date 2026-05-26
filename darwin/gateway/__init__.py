"""Gateway — Darwin 的消息网关，支持多种平台"""

from .base import GatewayAdapter
from .feishu import FeishuAdapter

__all__ = ["GatewayAdapter", "FeishuAdapter"]