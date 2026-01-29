# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
MCP (Model Context Protocol) Server for Metis
将 Metis 的核心功能通过 MCP 协议暴露为 Tools/Skills
"""

from metis.mcp.server import MetisMCPServer
from metis.mcp.skills.html_generator import HTMLGeneratorSkill

__all__ = ["MetisMCPServer", "HTMLGeneratorSkill"]

