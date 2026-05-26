"""CLI — Darwin 命令行入口"""

import click
import sys
from pathlib import Path

# Add darwin to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Darwin — 数字生命体"""
    pass


@cli.command()
@click.argument("message")
@click.option("--profile", default="default", help="Darwin profile 名称")
@click.option("--model", default=None, help="使用的模型")
def chat(message: str, profile: str, model: str | None):
    """发送消息给 Darwin"""
    from darwin.agent.runtime import DarwinRuntime

    darwin_root = Path(__file__).parent.parent
    runtime = DarwinRuntime(darwin_root, profile=profile, model=model)
    response = runtime.chat(message)
    click.echo(response)


@cli.command()
@click.option("--profile", default="default", help="Darwin profile 名称")
def status(profile: str):
    """查看 Darwin 状态"""
    from darwin.agent.runtime import DarwinRuntime

    darwin_root = Path(__file__).parent.parent
    runtime = DarwinRuntime(darwin_root, profile=profile)
    status = runtime.get_status()
    click.echo(f"Darwin 状态: {status}")


@cli.command()
def version():
    """显示版本"""
    from darwin import __version__
    click.echo(f"Darwin v{__version__}")


@cli.command("init")
@click.option("--non-interactive", is_flag=True, help="非交互模式（使用默认值）")
@click.option("--reconfigure", is_flag=True, help="重新配置")
def init(non_interactive: bool, reconfigure: bool):
    """初始化 Darwin（首次运行需要）"""
    from .init_wizard import run_wizard
    from .config import ConfigManager, DEFAULT_CONFIG_DIR, DarwinConfig

    if non_interactive:
        print("非交互模式：创建默认配置")
        config = DarwinConfig(darwin_root=Path(__file__).parent.parent)
        manager = ConfigManager()
        manager.save(config)
        print(f"默认配置已保存到 {DEFAULT_CONFIG_DIR / 'config.yaml'}")
        print("请编辑配置文件后运行 'darwin start'")
        return

    config = run_wizard()
    if config is None:
        sys.exit(1)


@cli.command("start")
@click.option("--profile", default="default", help="Darwin profile 名称")
def start(profile: str):
    """启动 Darwin"""
    from .config import ConfigManager
    from .agent.runtime import DarwinRuntime

    manager = ConfigManager()
    if not manager.exists():
        print("未检测到配置，请先运行 'darwin init'")
        sys.exit(1)

    config = manager.load()
    manager.print_config(config)

    print("\n启动 Darwin...")
    runtime = DarwinRuntime(config.darwin_root, profile=profile)
    print(f"Darwin 已启动 (session: {runtime.session_id})")

    # 临时：打印状态
    status = runtime.get_status()
    print(f"状态: {status}")


@cli.group()
def evolution():
    """进化引擎相关命令"""
    pass


@evolution.command("status")
def evolution_status():
    """查看当前进化状态"""
    from darwin.evolution import EvolutionEngine

    darwin_root = Path(__file__).parent.parent
    engine = EvolutionEngine(darwin_root)
    status = engine.get_status()
    click.echo(f"当前状态: {status}")


@evolution.command("list-checkpoints")
def evolution_list():
    """列出所有快照"""
    from darwin.evolution import EvolutionEngine

    darwin_root = Path(__file__).parent.parent
    engine = EvolutionEngine(darwin_root)
    checkpoints = engine.list_checkpoints()
    for ckpt in checkpoints:
        click.echo(f"  {ckpt['id']}: {ckpt['description']} @ {ckpt['created_at'][:19]}")


@evolution.command("history")
def evolution_history():
    """查看变更历史"""
    from darwin.evolution import Committer

    darwin_root = Path(__file__).parent.parent
    committer = Committer(darwin_root)
    history = committer.get_change_history()
    if not history:
        click.echo("暂无变更历史")
        return
    for entry in history:
        click.echo(f"  [{entry['type']}] {entry['plan_id']}: {entry['description']}")


def main():
    cli()


if __name__ == "__main__":
    main()
else:
    # 当作为入口点安装时
    cli()