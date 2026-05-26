"""Init Wizard — Darwin 初始化向导

交互式引导用户完成配置。
"""

import os
import platform
import sys
from pathlib import Path
from typing import Optional

from .config import (
    ConfigManager,
    DarwinConfig,
    LLMConfig,
    FeishuConfig,
    DEFAULT_CONFIG_DIR,
)


def is_interactive() -> bool:
    """检查是否在交互式终端"""
    return sys.stdin.isatty() and sys.stdout.isatty()


def print_banner():
    """打印欢迎横幅"""
    banner = r"""
   _          _             _           
  (_)        | |           (_)          
   _   ____  | |  ___  _ __  _  ____    
  | | |  _ \ | | / _ \| '_ \| |/ _  \   
  | | | |_) || ||  __/| | | | | (_) |  
  |_| |  __/ |_| \___||_| |_|_|\___/   
         | |  Digital Life Form          
         |_|                            
    """
    print(banner)
    print("欢迎使用 Darwin — 数字生命体\n")
    print(f"系统: {platform.system()} {platform.release()}")
    print(f"配置目录: {DEFAULT_CONFIG_DIR}\n")
    print("=" * 50)
    print()


def print_step(current: int, total: int, title: str):
    """打印步骤标题"""
    print(f"\n[步骤 {current}/{total}] {title}")
    print("-" * 40)


def prompt_choice(
    prompt_text: str,
    options: list[tuple[str, str]],
    default: Optional[int] = 0,
) -> str:
    """
    交互式选择

    Args:
        prompt_text: 提示文本
        options: [(key, description), ...] 列表
        default: 默认选项索引

    Returns:
        选中的 key
    """
    print(f"\n{prompt_text}")

    for i, (key, desc) in enumerate(options):
        marker = "❯" if i == default else " "
        print(f"  {marker} [{i+1}] {desc}")

    while True:
        try:
            choice = input(f"\n请选择 (默认 {default+1}): ").strip()
            if not choice:
                choice = str(default + 1)
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
            print("无效选择，请重新输入")
        except ValueError:
            print("请输入数字")


def prompt_input(prompt_text: str, default: str = "", password: bool = False) -> str:
    """交互式输入"""
    if default:
        prompt_text = f"{prompt_text} (默认: {default})"

    while True:
        try:
            if password:
                import getpass
                value = getpass.getpass(f"\n{prompt_text}: ")
            else:
                value = input(f"\n{prompt_text}: ").strip()

            if not value and default:
                return default
            if not value:
                print("此项不能为空，请重新输入")
                continue
            return value
        except (EOFError, KeyboardInterrupt):
            print("\n\n已取消")
            sys.exit(0)


def prompt_yes_no(prompt_text: str, default: bool = True) -> bool:
    """是/否确认"""
    marker = "[Y/n]" if default else "[y/N]"
    while True:
        try:
            value = input(f"\n{prompt_text} {marker}: ").strip().lower()
            if not value:
                return default
            if value in ("y", "yes", "是"):
                return True
            if value in ("n", "no", "否"):
                return False
            print("请输入 y 或 n")
        except (EOFError, KeyboardInterrupt):
            print("\n\n已取消")
            sys.exit(0)


def setup_llm(config: DarwinConfig) -> DarwinConfig:
    """配置 LLM"""
    # 选择 provider
    provider = prompt_choice(
        "请选择 LLM 提供商：",
        [
            ("minimax", "MiniMax（推荐国内用户，快速稳定）"),
            ("openai", "OpenAI（需要海外网络）"),
            ("custom", "自定义（手动输入 API 地址）"),
        ],
        default=0,
    )

    config.llm.provider = provider

    # MiniMax 配置
    if provider == "minimax":
        config.llm.api_key = prompt_input("请输入 MiniMax API Key", password=True)
        model_choice = prompt_choice(
            "请选择模型：",
            [
                ("MiniMax-Text-01", "MiniMax-Text-01（推荐）"),
                ("MiniMax-Text-01-Smart", "MiniMax-Text-01-Smart（更智能）"),
                ("abab6.5s-chat", "abab6.5s-chat（轻量快速）"),
            ],
            default=0,
        )
        config.llm.model = model_choice

    # OpenAI 配置
    elif provider == "openai":
        config.llm.api_key = prompt_input("请输入 OpenAI API Key", password=True)
        config.llm.model = prompt_input("请输入模型名称", default="gpt-4o-mini")

    # 自定义配置
    else:
        config.llm.api_key = prompt_input("请输入 API Key", password=True)
        config.llm.base_url = prompt_input("请输入 API 地址（base URL）", default="https://api.openai.com/v1")
        config.llm.model = prompt_input("请输入模型名称")

    # 高级参数
    if prompt_yes_no("是否需要调整高级参数？", default=False):
        print("\n高级参数（直接回车使用默认值）：")

        max_tokens_str = prompt_input(
            f"最大 Token 数 (256-8192)",
            default=str(config.llm.max_tokens),
        )
        config.llm.max_tokens = max(256, min(8192, int(max_tokens_str)))

        temp_str = prompt_input(
            f"Temperature (0.0-2.0)",
            default=str(config.llm.temperature),
        )
        config.llm.temperature = max(0.0, min(2.0, float(temp_str)))

    return config


def setup_feishu(config: DarwinConfig) -> DarwinConfig:
    """配置飞书"""
    print("\n飞书机器人配置")
    print("如果你不需要接入飞书，可以跳过这一步。")

    if prompt_yes_no("是否配置飞书机器人？", default=False):
        config.feishu.enabled = True
        config.feishu.app_id = prompt_input("请输入飞书 App ID", default=config.feishu.app_id)
        config.feishu.app_secret = prompt_input("请输入飞书 App Secret", password=True)
        config.feishu.bot_name = prompt_input("请输入 Bot 名称", default="Darwin")
    else:
        config.feishu.enabled = False

    return config


def setup_soul(config: DarwinConfig) -> DarwinConfig:
    """配置 SOUL"""
    print("\n灵魂定义（SOUL.md）")
    print("SOUL.md 定义了 Darwin 的身份、信念和行为方式。")

    darwin_root = Path(prompt_input(
        f"Darwin 项目目录",
        default=str(config.darwin_root),
    ))
    config.darwin_root = darwin_root

    soul_file = darwin_root / "SOUL.md"
    if not soul_file.exists():
        print(f"\n⚠️  警告：{soul_file} 不存在")
        print("向导完成后，请手动创建 SOUL.md 或从示例复制。")

    return config


def run_wizard() -> Optional[DarwinConfig]:
    """运行初始化向导"""
    if not is_interactive():
        print("错误：向导需要交互式终端，请使用 --non-interactive 或手动编辑配置")
        print(f"手动配置文件位置: {DEFAULT_CONFIG_DIR / 'config.yaml'}")
        return None

    print_banner()

    # 检查是否已有配置
    manager = ConfigManager()
    if manager.exists():
        print("检测到已有配置：")
        existing = manager.load()
        manager.print_config(existing)
        print()

        if not prompt_yes_no("是否覆盖现有配置？", default=False):
            print("取消初始化")
            return None

    config = DarwinConfig()
    total_steps = 4

    # 步骤 1：LLM 配置
    print_step(1, total_steps, "LLM 配置")
    config = setup_llm(config)

    # 步骤 2：飞书配置
    print_step(2, total_steps, "飞书配置（可选）")
    config = setup_feishu(config)

    # 步骤 3：项目目录
    print_step(3, total_steps, "项目目录")
    config = setup_soul(config)

    # 步骤 4：验证并保存
    print_step(4, total_steps, "验证并保存")

    valid, errors = manager.validate(config)

    if not valid:
        print("\n⚠️  配置验证失败：")
        for err in errors:
            print(f"  - {err}")
        print("\n请重新运行初始化向导修正问题")
        return None

    # 保存
    manager.save(config)

    # 确认
    print("\n" + "=" * 50)
    print("✅ 配置完成！\n")
    manager.print_config(config)
    print()
    print("下一步：")
    print("  - 运行 'darwin start' 启动 Darwin")
    print("  - 运行 'darwin status' 查看状态")
    print("  - 运行 'darwin init --reconfigure' 重新配置")

    return config