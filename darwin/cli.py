"""
Darwin CLI — Darwin 的命令行入口

将 Darwin 接入 OpenClaw Gateway 作为 agent 运行。

用法：
    python -m darwin.cli
    
在 OpenClaw Gateway 配置中注册为 agent，
    Gateway 会通过 stdio 或 HTTP 向 Darwin 发送消息。
"""

import logging
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

from .core import DarwinCore

logger = logging.getLogger(__name__)


def main():
    """Darwin CLI 主入口"""
    # 启动 DarwinCore
    darwin_root = Path(__file__).parent.parent

    logger.info("Starting Darwin...")

    # 初始化 Darwin 核心
    core = DarwinCore(darwin_root)

    logger.info("Darwin initialized successfully")
    logger.info(f"Darwin state: {core.state}")

    # 启动 Darwin 后台循环（异步感知模式）
    core.start()
    logger.info("Darwin background loop started")

    return 0


if __name__ == "__main__":
    sys.exit(main())