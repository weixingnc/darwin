# Darwin — 数字生命体

## 安装

### Docker 方式（一键运行，推荐）

```bash
# 1. 确保已安装 Docker
#    Mac/Windows: https://docs.docker.com/desktop/
#    Linux: sudo apt install docker.io

# 2. 下载项目
git clone https://github.com/weixingnc/darwin.git
cd darwin

# 3. 构建镜像
docker build -t darwin-agent:latest .

# 4. 运行
docker run -it darwin-agent
```

### Docker Compose 方式（数据持久化）

```bash
# 启动（配置文件和数据会保存在 ./data 目录）
docker-compose up -d

# 进入容器
docker-compose exec darwin bash

# 查看日志
docker-compose logs -f
```

## 首次配置

首次启动容器时，Darwin 会提示你配置：

```bash
# 编辑配置文件
nano /root/.darwin/config.yaml

# 填入你的 LLM API Key，例如：
# llm:
#   provider: minimax
#   api_key: your-api-key-here
#   model: MiniMax-Text-01

# 重新启动容器即可
exit
docker restart <container_id>
```

## 常用命令

```bash
# 启动 Darwin
docker run -it darwin-agent

# 进入交互式 shell
docker run -it darwin-agent bash

# 查看状态
docker run -it darwin-agent status

# 初始化配置（需要交互式终端）
docker run -it darwin-agent init
```

## 从 Docker 进入 Darwin 对话

```bash
# 方式一：直接对话
docker run -it darwin-agent chat "你好"

# 方式二：交互模式
docker run -it darwin-agent bash
# 然后在容器内运行
darwin chat "你好"
```

## 数据持久化

默认情况下容器内的配置是临时的。使用 docker-compose 或挂载卷可以持久化：

```bash
# docker-compose 会把配置保存在 ./data/.darwin
docker-compose up -d

# 或者手动挂载
docker run -it -v ~/darwin-data:/root/.darwin darwin-agent
```

## 常见问题

**Q: docker: command not found**
A: 需要安装 Docker。访问 https://docs.docker.com/desktop/ 下载安装。

**Q: 容器内无法运行 darwin 命令**
A: 检查镜像是否构建成功：`docker images darwin-agent`

**Q: 配置文件在哪？**
A: 容器内：`/root/.darwin/config.yaml`

---

*Darwin — 不断进化的数字生命体*