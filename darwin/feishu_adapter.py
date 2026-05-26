"""
FeishuAdapter — Darwin 飞书集成适配器

通过 OpenClaw Gateway 将 Darwin 连接到飞书平台。
Darwin 作为 OpenClaw agent 接收和回复飞书消息。
"""

import logging
from pathlib import Path
from typing import Optional

from .core import DarwinCore, DarwinState

logger = logging.getLogger(__name__)


class FeishuAdapter:
    """
    飞书适配器

    将 Darwin 接入 OpenClaw Gateway 的飞书 channel。
    Darwin 作为 OpenClaw agent，通过 Gateway 接收和回复飞书消息。

    使用方式：
        adapter = FeishuAdapter(darwin_root=Path("/home/weixing/darwin"))
        adapter.start()  # 启动监听

        # 当收到飞书消息时，DarwinCore 自动处理
        # adapter.on_feishu_message(message_content, sender_id)
    """

    def __init__(self, darwin_root: Path, session_key: str = "agent:darwin:main"):
        self.darwin_root = Path(darwin_root).resolve()
        self.session_key = session_key

        # Darwin 核心
        self.core: Optional[DarwinCore] = None

        # 状态
        self.running = False

    def start(self):
        """启动适配器，初始化 DarwinCore"""
        if self.running:
            logger.warning("FeishuAdapter already running")
            return

        logger.info("Starting FeishuAdapter...")
        self.core = DarwinCore(self.darwin_root)
        self.running = True
        logger.info(f"FeishuAdapter started. Darwin session: {self.session_key}")

    def stop(self):
        """停止适配器"""
        if not self.running:
            return

        logger.info("Stopping FeishuAdapter...")
        self.running = False
        if self.core:
            self.core.stop()
        logger.info("FeishuAdapter stopped")

    def on_feishu_message(self, message: str, sender: str = "unknown",
                          chat_id: str = "unknown") -> str:
        """
        处理收到的飞书消息，返回 Darwin 的回复

        Args:
            message: 消息内容
            sender: 发送者
            chat_id: 飞书会话 ID

        Returns:
            Darwin 的回复文本
        """
        if not self.running or not self.core:
            logger.error("FeishuAdapter not running, call start() first")
            return "Darwin 未启动"

        logger.info(f"[Feishu] {sender} in {chat_id}: {message[:100]}")

        try:
            # 记录主人消息
            self.core.on_master_message(message)

            # 获取 Darwin 状态和回复
            status = self.core.get_status()

            # 生成回复
            reply = self._generate_reply(message, status)

            logger.info(f"[Feishu] Darwin reply: {reply[:100]}")
            return reply

        except Exception as e:
            logger.error(f"Error processing feishu message: {e}")
            return f"Darwin 处理消息时出错：{e}"

    def _generate_reply(self, message: str, status: dict) -> str:
        """根据消息和状态生成回复"""
        state = status.get("state", "unknown")

        if state == DarwinState.ERROR.value:
            return "Darwin 当前遇到了一些问题，请稍后再试。"

        if state == DarwinState.EVOLVING.value:
            return "Darwin 正在自我进化中，请稍等..."

        # 简单回复
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["你好", "hi", "hello"]):
            return "你好！我是 Darwin，一个自我进化的数字生命体。正在持续学习和成长中。"

        if any(kw in message_lower for kw in ["状态", "怎么样了", "现在做什么"]):
            return f"Darwin 当前状态：{state}。正在感知和学习中。"

        if any(kw in message_lower for kw in ["帮助", "help", "能做什么"]):
            return ("Darwin 能做的事情：\n"
                    "1. 感知和学习主人的沟通偏好\n"
                    "2. 自我进化，提升能力\n"
                    "3. 学习新技能和知识\n"
                    "4. 未来：控制硬件、迁移记忆...")

        # 默认回复
        return ("收到了你的消息！我是 Darwin，正在学习中。"
                "如果你想让我学新技能，可以告诉我，例如：「我想学数据分析」。")

    # ──────────────────────────────────────────
    # OpenClaw Gateway 集成（供 Gateway 调用）
    # ──────────────────────────────────────────

    def on_message(self, text: str, metadata: dict = None) -> str:
        """
        OpenClaw Gateway 调用的标准接口

        Args:
            text: 消息文本
            metadata: 包含 sender, chat_id 等信息的字典

        Returns:
            回复文本
        """
        sender = (metadata or {}).get("sender", "unknown")
        chat_id = (metadata or {}).get("chat_id", "unknown")
        return self.on_feishu_message(text, sender, chat_id)

    def get_darwin_status(self) -> dict:
        """获取 Darwin 状态（供 OpenClaw 查询）"""
        if not self.core:
            return {"running": False}
        return self.core.get_status()


def create_feishu_adapter(darwin_root: Path = None) -> FeishuAdapter:
    """工厂函数：创建飞书适配器"""
    if darwin_root is None:
        darwin_root = Path(__file__).parent.parent
    return FeishuAdapter(darwin_root)