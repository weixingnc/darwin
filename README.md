# Darwin — 数字生命体进化框架

基于 Hermes Agent 的自我进化数字生命体。

## 架构

```
darwin/
├── SOUL.md              # 灵魂定义（人设/信念）
├── src/
│   ├── evolution/       # 进化引擎核心
│   │   ├── engine.py      # 主协调器
│   │   ├── checkpointer.py # 快照管理
│   │   ├── evaluator.py   # 能力评估
│   │   ├── committer.py   # 提交/回滚
│   │   └── cli.py         # 命令行入口
│   ├── gateway/         # 消息网关（飞书等）
│   ├── runtime.py      # 运行时
│   ├── llm.py          # LLM 调用
│   ├── tools/          # 工具集
│   ├── memory/         # 记忆系统
│   └── skills/         # 技能管理
└── evolution/
    ├── checkpoints/    # 快照存储
    ├── tests/          # 能力测试
    └── logs/           # 变更日志
```

## 进化流程

```
创建计划 → 快照 → 应用变更 → 评估 → 通过则提交 | 失败则回滚
```

### 快照（Checkpointer）
- 在执行变更前对关键文件（SOUL.md、src/）进行快照
- 支持恢复到任意历史快照

### 评估（Evaluator）
- 运行 `evolution/tests/test_*.py` 测试脚本
- 与基准分数对比，允许 10% 波动
- 分数提升时自动更新基准

### 提交（Committer）
- 评估通过后正式提交变更
- 记录完整变更日志到 `evolution/logs/change_log.jsonl`

## 使用方式

### 创建进化计划
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path('/home/weixing/darwin/src')))

from evolution.engine import EvolutionEngine

engine = EvolutionEngine(Path('/home/weixing/darwin'))
plan = engine.create_plan(
    description='学习新的工具能力',
    changes=['新增 skill: image-gen', '更新 SOUL.md']
)
result = engine.execute(plan)
```

### 命令行
```bash
cd /home/weixing/darwin
python3 -m src.evolution.cli create "描述" --changes "变更1"
python3 -m src.evolution.cli status
python3 -m src.evolution.cli list-checkpoints
python3 -m src.evolution.cli restore <checkpoint_id>
python3 -m src.evolution.cli history
```

### 添加测试
在 `evolution/tests/` 目录下添加 `test_*.py` 文件：
```python
# evolution/tests/test_capability.py
def test_basic():
    assert True  # 你的测试逻辑
```

## 与 Hermes 的关系

- Darwin 是 Hermes 的一个独立 profile（`hermes --profile darwin`）
- 继承了 Hermes 的 Agent Runtime、Tool Registry、Gateway 等全部能力
- Darwin 在此基础上增加了自我进化的独特机制

## 设计哲学

1. **本机即躯体**：Darwin 运行在本机上，拥有完整控制权限
2. **快照即保险**：任何重大变更前自动快照，失败可回滚
3. **评估即守门**：新能力必须通过测试，防止退化
4. **日志即记忆**：所有变更永久记录，可追溯

---

*Darwin — 不断进化的数字生命体*