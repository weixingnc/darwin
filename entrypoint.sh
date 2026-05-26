#!/bin/bash
# Darwin Entry Point Script
# 负责启动逻辑：首次引导配置 → 正常启动

set -e

CONFIG_FILE="/root/.darwin/config.yaml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_banner() {
    echo -e "${GREEN}"
    echo "   _          _             _           "
    echo "  (_)        | |           (_)          "
    echo "   _   ____  | |  ___  _ __  _  ____    "
    echo "  | | |  _ \\ | | / _ \\| '_ \\| |/ _  \\  "
    echo "  | | | |_) || ||  __/| | | | | (_) | "
    echo "  |_| |  __/ |_| \\___||_| |_|_|\\___/  "
    echo "         | |  Digital Life Form         "
    echo "         |_|                           "
    echo -e "${NC}"
}

# 检查是否已配置
check_configured() {
    if [ -f "$CONFIG_FILE" ]; then
        # 检查是否有 API Key
        if grep -q "api_key:" "$CONFIG_FILE" 2>/dev/null; then
            local api_key=$(grep "api_key:" "$CONFIG_FILE" | head -1 | sed 's/.*api_key:\s*//' | tr -d ' ')
            if [ -n "$api_key" ] && [ "$api_key" != "" ]; then
                return 0
            fi
        fi
    fi
    return 1
}

# 运行初始化向导
run_init() {
    echo -e "${YELLOW}首次使用需要配置 Darwin...${NC}"
    echo ""

    # 非交互模式生成基础配置，然后让用户手动配置
    darwin init --non-interactive || true

    echo ""
    echo -e "${YELLOW}配置已生成，请编辑配置文件添加 API Key：${NC}"
    echo -e "  ${GREEN}$CONFIG_FILE${NC}"
    echo ""
    echo "编辑完成后，重新启动容器即可。"
    echo ""

    # 检查 docker 环境
    if [ -f /.dockerenv ]; then
        echo -e "${YELLOW}注意：在 Docker 环境中，初始化向导需要交互式终端。${NC}"
        echo "建议："
        echo "  1. 先运行容器：docker run -it darwin-agent bash"
        echo "  2. 在容器内手动编辑配置：nano $CONFIG_FILE"
        echo "  3. 重新启动容器：exit 后重新 docker run"
    fi
}

# 启动 Darwin
start_darwin() {
    echo -e "${GREEN}启动 Darwin...${NC}"
    echo ""

    exec darwin start
}

# 主逻辑
main() {
    echo_banner

    if check_configured; then
        start_darwin
    else
        run_init
    fi
}

# 处理命令行参数
case "${1:-}" in
    --help|-h|"")
        echo "Darwin — 数字生命体"
        echo ""
        echo "用法: docker run darwin-agent [命令]"
        echo ""
        echo "命令:"
        echo "  (无参数)    启动 Darwin"
        echo "  --help      显示帮助"
        echo "  init        初始化配置"
        echo "  status      查看状态"
        echo "  chat        和 Darwin 对话"
        echo ""
        echo "示例:"
        echo "  docker run -it darwin-agent"
        echo "  docker run -it darwin-agent --help"
        echo "  docker run -it darwin-agent bash"
        ;;
    init)
        darwin init
        ;;
    start)
        start_darwin
        ;;
    status)
        darwin status
        ;;
    bash)
        echo "进入交互式 shell..."
        exec /bin/bash
        ;;
    *)
        exec darwin "$@"
        ;;
esac