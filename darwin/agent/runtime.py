"""DarwinRuntime — 基于 Hermes 的运行时

封装 Hermes AIAgent，提供 Darwin 特有的初始化和配置。
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DarwinRuntime:
    """
    Darwin 运行时

    使用 Hermes AIAgent 作为底层引擎，
    Darwin 在此基础上增加灵魂、记忆和进化能力。
    """

    def __init__(
        self,
        darwin_root: Path,
        profile: str = "default",
        model: str = "mini-max",
        provider: str = "minimax-cn",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        toolsets: Optional[list[str]] = None,
        **kwargs,
    ):
        self.darwin_root = Path(darwin_root)
        self.profile = profile

        # 延迟导入 Hermes Agent（避免循环依赖）
        try:
            from hermes_agent import AIAgent
        except ImportError as e:
            raise ImportError(
                "hermes-agent is required for DarwinRuntime. "
                "Install it with: pip install hermes-agent"
            ) from e

        # 构建 Hermes 配置
        hermes_config = {
            "provider": provider,
            "model": model,
            "platform": "darwin",
            "session_id": f"darwin-{profile}",
            "enabled_toolsets": toolsets or ["file", "terminal", "web", "search"],
            **kwargs,
        }

        if api_key:
            hermes_config["api_key"] = api_key
        if api_base:
            hermes_config["base_url"] = api_base

        # 加载 SOUL.md 作为 system prompt
        soul_file = self.darwin_root / "SOUL.md"
        if soul_file.exists():
            hermes_config["system_message"] = soul_file.read_text()
        else:
            logger.warning(f"SOUL.md not found at {soul_file}")

        self.agent = AIAgent(**hermes_config)
        logger.info(f"DarwinRuntime initialized with profile: {profile}")

    def chat(self, message: str) -> str:
        """发送消息，返回 AI 回复"""
        return self.agent.chat(message)

    def run_conversation(self, message: str, **kwargs) -> dict:
        """完整对话接口"""
        return self.agent.run_conversation(message, **kwargs)

    @property
    def session_id(self) -> str:
        return self.agent.session_id

    def get_status(self) -> dict:
        """获取运行时状态"""
        return {
            "darwin_root": str(self.darwin_root),
            "profile": self.profile,
            "session_id": self.session_id,
        }