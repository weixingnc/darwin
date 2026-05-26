"""Config — Darwin 配置管理

管理配置文件的读取、写入和验证。
默认配置文件在 ~/.darwin/config.yaml
"""

import json
import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


DEFAULT_CONFIG_DIR = Path.home() / ".darwin"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "minimax"           # minimax / openai / custom
    api_key: str = ""
    base_url: Optional[str] = None       # 自定义 provider 用
    model: str = "MiniMax-Text-01"       # 默认模型
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    request_timeout: int = 60


@dataclass
class FeishuConfig:
    """飞书配置"""
    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    bot_name: str = "Darwin"


@dataclass
class DarwinConfig:
    """Darwin 完整配置"""
    darwin_root: Path = field(default_factory=Path.cwd)
    profile: str = "default"
    llm: LLMConfig = field(default_factory=LLMConfig)
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    log_level: str = "INFO"


class ConfigManager:
    """
    配置管理器

    负责读取、写入、验证配置文件。
    配置默认存放在 ~/.darwin/config.yaml
    """

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or DEFAULT_CONFIG_FILE

    # ──────────────────────────────────────────
    # 读取
    # ──────────────────────────────────────────

    def load(self) -> DarwinConfig:
        """从文件加载配置"""
        if not self.config_file.exists():
            return self._default_config()

        with open(self.config_file) as f:
            data = yaml.safe_load(f) or {}

        return self._parse_config(data)

    def _parse_config(self, data: dict) -> DarwinConfig:
        """解析配置字典"""
        llm_data = data.get("llm", {})
        feishu_data = data.get("feishu", {})

        llm = LLMConfig(
            provider=llm_data.get("provider", "minimax"),
            api_key=llm_data.get("api_key", ""),
            base_url=llm_data.get("base_url"),
            model=llm_data.get("model", "MiniMax-Text-01"),
            max_tokens=llm_data.get("max_tokens", 2048),
            temperature=llm_data.get("temperature", 0.7),
            top_p=llm_data.get("top_p", 1.0),
            request_timeout=llm_data.get("request_timeout", 60),
        )

        feishu = FeishuConfig(
            enabled=feishu_data.get("enabled", False),
            app_id=feishu_data.get("app_id", ""),
            app_secret=feishu_data.get("app_secret", ""),
            bot_name=feishu_data.get("bot_name", "Darwin"),
        )

        return DarwinConfig(
            darwin_root=Path(data.get("darwin_root", str(Path.cwd()))),
            profile=data.get("profile", "default"),
            llm=llm,
            feishu=feishu,
            log_level=data.get("log_level", "INFO"),
        )

    def _default_config(self) -> DarwinConfig:
        """返回默认配置"""
        return DarwinConfig(
            darwin_root=Path.cwd(),
            profile="default",
            llm=LLMConfig(),
            feishu=FeishuConfig(),
            log_level="INFO",
        )

    # ──────────────────────────────────────────
    # 写入
    # ──────────────────────────────────────────

    def save(self, config: DarwinConfig) -> bool:
        """保存配置到文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "darwin_root": str(config.darwin_root),
            "profile": config.profile,
            "llm": {
                "provider": config.llm.provider,
                "api_key": config.llm.api_key,
                "base_url": config.llm.base_url,
                "model": config.llm.model,
                "max_tokens": config.llm.max_tokens,
                "temperature": config.llm.temperature,
                "top_p": config.llm.top_p,
                "request_timeout": config.llm.request_timeout,
            },
            "feishu": {
                "enabled": config.feishu.enabled,
                "app_id": config.feishu.app_id,
                "app_secret": config.feishu.app_secret,
                "bot_name": config.feishu.bot_name,
            },
            "log_level": config.log_level,
        }

        with open(self.config_file, "w") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        # 设置文件权限（Unix：仅当前用户可读写）
        os.chmod(self.config_file, 0o600)

        return True

    # ──────────────────────────────────────────
    # 验证
    # ──────────────────────────────────────────

    def validate(self, config: DarwinConfig) -> tuple[bool, list[str]]:
        """验证配置是否有效"""
        errors = []

        # LLM 验证
        if not config.llm.api_key:
            errors.append("LLM API Key 不能为空")
        elif len(config.llm.api_key) < 10:
            errors.append("LLM API Key 长度不足")

        # 飞书验证
        if config.feishu.enabled:
            if not config.feishu.app_id:
                errors.append("飞书 App ID 不能为空")
            if not config.feishu.app_secret:
                errors.append("飞书 App Secret 不能为空")

        # LLM 参数范围
        if not (0.0 <= config.llm.temperature <= 2.0):
            errors.append("temperature 必须在 0.0-2.0 之间")
        if not (0.0 <= config.llm.top_p <= 1.0):
            errors.append("top_p 必须在 0.0-1.0 之间")
        if not (256 <= config.llm.max_tokens <= 8192):
            errors.append("max_tokens 必须在 256-8192 之间")

        return len(errors) == 0, errors

    # ──────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────

    def exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_file.exists()

    def get_config_path(self) -> Path:
        """返回配置文件的路径"""
        return self.config_file

    def print_config(self, config: DarwinConfig):
        """打印配置（隐藏敏感信息）"""
        print(f"配置文件: {self.config_file}")
        print(f"LLM Provider: {config.llm.provider}")
        print(f"Model: {config.llm.model}")
        print(f"API Key: {'*' * 20}{config.llm.api_key[-4:] if config.llm.api_key else '(未设置)'}")
        print(f"飞书: {'已启用' if config.feishu.enabled else '未启用'}")
        if config.feishu.enabled:
            print(f"  Bot Name: {config.feishu.bot_name}")