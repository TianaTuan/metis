# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
MCP Server 入口点
可以通过 python -m metis.mcp 启动 MCP Server
"""

import logging
import sys

from metis.mcp.server import MetisMCPServer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # 日志输出到 stderr，避免干扰 JSON-RPC 通信
)

def main():
    """MCP Server 主入口函数"""
    server = MetisMCPServer()
    try:
        server.run_stdio()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

