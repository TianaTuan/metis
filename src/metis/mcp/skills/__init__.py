# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
MCP Skills for Metis
将 Metis 的功能模块封装为独立的 Skills
"""

from metis.mcp.skills.html_generator import HTMLGeneratorSkill
from metis.mcp.skills.base import BaseSkill

__all__ = ["HTMLGeneratorSkill", "BaseSkill"]

