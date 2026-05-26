"""Test suite for Config and Init Wizard"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.config import (
    ConfigManager,
    DarwinConfig,
    LLMConfig,
    FeishuConfig,
)
from darwin.init_wizard import is_interactive


def test_config_manager_defaults():
    """默认配置正确"""
    config = DarwinConfig()
    assert config.llm.provider == "minimax"
    assert config.llm.api_key == ""
    assert config.llm.model == "MiniMax-Text-01"
    assert config.feishu.enabled is False


def test_config_manager_save_load():
    """配置可以保存和加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        manager = ConfigManager(config_file)

        config = DarwinConfig(
            darwin_root=Path(tmpdir),
            llm=LLMConfig(provider="openai", api_key="sk-test123", model="gpt-4"),
            feishu=FeishuConfig(enabled=True, app_id="test-app", app_secret="secret"),
        )

        manager.save(config)
        assert config_file.exists()

        loaded = manager.load()
        assert loaded.llm.provider == "openai"
        assert loaded.llm.api_key == "sk-test123"
        assert loaded.feishu.enabled is True


def test_config_validation():
    """配置验证正确工作"""
    manager = ConfigManager()

    # 正常配置
    config = DarwinConfig(
        llm=LLMConfig(provider="minimax", api_key="valid-key-123"),
    )
    valid, errors = manager.validate(config)
    assert valid is True

    # 空 API Key
    config2 = DarwinConfig(llm=LLMConfig(provider="minimax", api_key=""))
    valid2, errors2 = manager.validate(config2)
    assert valid2 is False
    assert "API Key" in errors2[0]

    # 飞书需要完整信息
    config3 = DarwinConfig(
        llm=LLMConfig(provider="minimax", api_key="valid-key-123"),
        feishu=FeishuConfig(enabled=True, app_id="", app_secret=""),
    )
    valid3, errors3 = manager.validate(config3)
    assert valid3 is False

    # temperature 范围
    config4 = DarwinConfig(
        llm=LLMConfig(provider="minimax", api_key="valid-key-123", temperature=5.0),
    )
    valid4, errors4 = manager.validate(config4)
    assert valid4 is False


def test_config_validation_temperature_range():
    """Temperature 在合法范围内可以通过"""
    manager = ConfigManager()
    config = DarwinConfig(
        llm=LLMConfig(provider="minimax", api_key="valid-key-123", temperature=1.5),
    )
    valid, errors = manager.validate(config)
    assert valid is True


def test_llm_config_defaults():
    """LLM 配置默认值"""
    llm = LLMConfig()
    assert llm.provider == "minimax"
    assert llm.max_tokens == 2048
    assert llm.temperature == 0.7
    assert llm.top_p == 1.0
    assert llm.request_timeout == 60


def test_feishu_config_defaults():
    """飞书配置默认值"""
    feishu = FeishuConfig()
    assert feishu.enabled is False
    assert feishu.bot_name == "Darwin"


if __name__ == "__main__":
    tests = [
        ("ConfigManager defaults", test_config_manager_defaults),
        ("ConfigManager save/load", test_config_manager_save_load),
        ("Config validation", test_config_validation),
        ("Config validation temperature range", test_config_validation_temperature_range),
        ("LLM config defaults", test_llm_config_defaults),
        ("Feishu config defaults", test_feishu_config_defaults),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)