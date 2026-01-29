# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
MCP Server 实现
基于 JSON-RPC 2.0 协议，将 Metis 功能暴露为 Tools/Skills
"""

import json
import sys
import logging
from typing import Any, Dict, List, Optional

from metis.mcp.skills.html_generator import HTMLGeneratorSkill
from metis.mcp.skills.base import BaseSkill

logger = logging.getLogger("metis.mcp")


class MetisMCPServer:
    """
    Metis MCP Server
    实现 JSON-RPC 2.0 协议，提供 Tools/Skills 调用接口
    """

    def __init__(self, engine=None):
        """
        初始化 MCP Server

        Args:
            engine: MetisEngine 实例（可选，用于需要引擎的 Skills）
        """
        self.engine = engine
        self.skills: Dict[str, BaseSkill] = {}
        self._register_default_skills()

    def _register_default_skills(self):
        """注册默认的 Skills"""
        # 注册 HTML 生成 Skill
        html_skill = HTMLGeneratorSkill()
        self.register_skill(html_skill)

    def register_skill(self, skill: BaseSkill):
        """
        注册一个 Skill

        Args:
            skill: 要注册的 Skill 实例
        """
        self.skills[skill.get_name()] = skill
        logger.info(f"Registered skill: {skill.get_name()}")

    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 JSON-RPC 请求

        Args:
            request: JSON-RPC 请求对象

        Returns:
            JSON-RPC 响应对象
        """
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        try:
            if method == "initialize":
                return self._handle_initialize(request_id, params)
            elif method == "tools/list":
                return self._handle_tools_list(request_id)
            elif method == "tools/call":
                return self._handle_tools_call(request_id, params)
            elif method == "ping":
                return {"jsonrpc": "2.0", "id": request_id, "result": "pong"}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                },
            }

    def _handle_initialize(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 initialize 请求"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "metis-mcp-server",
                    "version": "1.2.0",
                },
            },
        }

    def _handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """处理 tools/list 请求，返回所有可用的 Tools"""
        tools = []
        for skill in self.skills.values():
            schema = skill.get_schema()
            tools.append(
                {
                    "name": skill.get_name(),
                    "description": skill.get_description(),
                    "inputSchema": schema,
                }
            )

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools},
        }

    def _handle_tools_call(
        self, request_id: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理 tools/call 请求，执行指定的 Tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.skills:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Tool not found: {tool_name}",
                },
            }

        try:
            skill = self.skills[tool_name]
            result = skill.execute(**arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2),
                        }
                    ],
                    "isError": not result.get("success", True),
                },
            }
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {"success": False, "error": str(e)}, ensure_ascii=False
                            ),
                        }
                    ],
                    "isError": True,
                },
            }

    def run_stdio(self):
        """
        运行 MCP Server，使用 stdio 传输
        从 stdin 读取 JSON-RPC 请求，向 stdout 写入响应
        """
        logger.info("Starting Metis MCP Server (stdio mode)")

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = self._handle_request(request)
                print(json.dumps(response, ensure_ascii=False), flush=True)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}",
                    },
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}",
                    },
                }
                print(json.dumps(error_response), flush=True)

