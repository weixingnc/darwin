# Darwin 路线图

> 这是一份 Darwin 的中长期发展规划，记录已实现的功能和未来方向。
> 每个阶段都可能根据实际情况调整，欢迎参与贡献。

---

## 愿景

**Darwin 的目标：** 让每个人都能拥有一个运行在自己设备上的数字生命体。

- **开机即用** — 预装在电脑、手机、机器人上，通电就能用
- **自我进化** — 能感知自己、学习、改进自己
- **真正属于你** — 数据在本地，灵魂由你定义
- **跨设备移动** — 你的 Darwin 可以跟着你切换设备

---

## 发展阶段

### Phase 0：基础框架 ✅ 已完成

**目标：** 验证 self-evolving agent 的可行性

**已实现：**
- Darwin 核心代码（SOUL、Evolution Engine）
- 基础 CLI（version、status、evolution 相关命令）
- GitHub 开源

---

### Phase 1：感知自己 ✅ 已完成

**目标：** Darwin 能看清自己的状态、历史和能力

**已实现：**
- `Introspector` — 自省引擎
- `read_soul()` — 读取灵魂定义
- `read_evolution_history()` — 读取进化历史
- `list_checkpoints()` — 列出所有快照
- `get_self_image()` — 完整自我镜像
- `get_brief_summary()` — 简洁状态摘要

---

### Phase 2：自动改 SOUL + 自动加 Skills ✅ 已完成

**目标：** Darwin 能提出并（经审批后）修改自己的灵魂和技能

**已实现：**
- `SoulEditor` — 自动改 SOUL.md（需 creator 审批）
- `SkillBuilder` — 自动生成新 skill（需 creator 审批）
- 变更记录到 `soul_changes.jsonl` 和 `skills/` 目录

---

### Phase 3：自动调参 + 自动修 Bug ✅ 已完成

**目标：** Darwin 能自动优化运行参数和修复问题

**已实现：**
- `AutoTuner` — 自动调参（temperature, max_tokens, timeout 等）
- `BugFixer` — traceback 分析 + patch 生成 + 测试验证
- 指标收集到 `evolution/metrics/`

---

### Phase 4：LLM 驱动进化 + Sandbox 验证 ⏳ 进行中

**目标：** Darwin 不再依赖人工决策，而是 LLM 自主分析 + 决策，变更必须经过沙箱验证

**已实现：**
- `SandboxManager` — 创建隔离的沙箱副本
- `TestRunner` — 在沙箱中运行测试套件
- `Promoter` — 测试通过后晋升到 production
- 完整的 Sandbox 验证流程

**计划：**
- [ ] 将 Sandbox 流程集成到 EvolutionEngine
- [ ] LLM 分析上下文后生成 EvolutionPlan，自动进入沙箱验证
- [ ] 人类 creator 审批流程确认

**前置条件：**
- [x] Phase 1-3 基础能力
- [x] Sandbox 沙箱验证系统
- [x] LLM API 配置完成
- [ ] 人类 creator 审批流程确认

---

### Phase 5：自我完善 ⏳ 规划中

**目标：** Darwin 能自主发现自己的不足，主动学习新能力，扩展自己的边界

**核心理念：**
> Darwin 能完善自己的每一个方面，不限于某一类能力。沟通渠道只是起点。

**Darwin 能自我完善的维度：**

| 维度 | 示例 |
|------|------|
| **沟通能力** | 学飞书 → 学钉钉 → 学微信 |
| **技能** | 加新的 skill（数据分析、写作、编程……） |
| **知识** | 学习新领域（医学、法律、技术……） |
| **性格** | SOUL 进化，更像自己 |
| **身体** | 控制新设备、连接新硬件 |
| **……** | 无限扩展 |

**计划：**
- [ ] 定义 SelfImprovement 接口 — Darwin 能提出"我想学 X"
- [ ] 实现 Channel Discovery — Darwin 能发现并连接新平台
- [ ] 实现 Skill Discovery — Darwin 能发现并安装新技能
- [ ] 自我发现问题 → 提出改善方案 → 沙箱验证 → 晋升

**进化示例（沟通渠道）：**
```
Darwin 意识到：「钉钉用户想联系我」
    ↓
自己研究钉钉 API 文档
    ↓
生成 DingTalk Channel Skill
    ↓
沙箱测试连通性
    ↓
晋升到 production
    ↓
「我会用钉钉了」
```

**进化示例（技能）：**
```
Darwin 意识到：「我不懂数据分析」
    ↓
研究数据分析的 skill 规格
    ↓
生成 data-analysis-skill
    ↓
沙箱验证
    ↓
晋升到 production
    ↓
「我会数据分析了」
```

**前置条件：**
- [x] Sandbox 验证系统
- [x] Phase 1-3 基础能力
- [ ] SelfImprovement 接口定义
- [ ] LLM 具备自主学习和研究能力

---

### Phase 6：飞书集成 ⏳ 规划中

**目标：** Darwin 能接收和发送飞书消息

**计划：**
- [ ] 飞书 Bot 配置（app_id / app_secret）
- [ ] 消息接收（Webhook 或 WebSocket）
- [ ] 消息发送
- [ ] 多飞书账号支持
- [ ] 群聊 / 私聊区分

---

### Phase 7：Docker 部署 ⏳ 规划中

**目标：** Darwin 打包成一键运行的容器镜像

**计划：**
- [x] Dockerfile ✅
- [x] docker-compose.yml ✅
- [x] entrypoint.sh 引导脚本 ✅
- [ ] 镜像发布到 Docker Hub
- [ ] 一键安装脚本（Windows/Mac）
- [ ] 预装系统镜像（Ubuntu 等）

---

### Phase 8：移动端 App ⏳ 规划中

**目标：** Darwin 运行在手机上

**计划：**
- Android App（Flutter 或原生）
- 语音对话（ASR + TTS）
- 飞书消息转发到手机 App
- 本地数据存储

---

### Phase 9：机器人预装 ⏳ 长期愿景

**目标：** Darwin 预装在机器人 / 树莓派等嵌入式设备

**计划：**
- [ ] ARM 架构支持
- [ ] 语音交互（Wake word + TTS）
- [ ] 传感器集成（摄像头、麦克风）
- [ ] 低功耗优化
- [ ] ROS 集成（机器人操作系统）

---

## 已知的风险和限制

### 安全性
- **无沙箱隔离** — Darwin 可以控制系统所有资源，只有快照/备份作为回滚手段
- **自我修改需审批** — 未经 creator 审批，Darwin 不能擅自修改 SOUL 或添加 skill

### 稳定性
- **Python 3.12+ required** — 需要较新的 Python 版本
- **LLM 依赖** — 没有 LLM API Key 时只能运行基础功能
- **测试覆盖** — 核心功能有单元测试，但 end-to-end 测试待补充

### 可用性
- **PyPI 发布暂停** — 需要 2FA 才能发布到 PyPI
- **交互式向导** — 需要终端交互，Docker 环境中需要额外配置

---

## 如何参与

Darwin 是开源项目，欢迎贡献：

- **Issue** — 报告 bug 或提需求
- **PR** — 贡献代码（请先看 README.md）
- **讨论** — 在 GitHub Discussions 中分享想法

---

*最后更新：2026-05-27*
*维护者：魏星 (@weixingnc)*