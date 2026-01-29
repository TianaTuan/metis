# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
MCP Skill 基类
定义 Skill 的标准接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSkill(ABC):
    """
    MCP Skill 基类
    所有 Skill 都应该继承此类并实现必要的方法
    """

    @abstractmethod
    def get_name(self) -> str:
        """返回 Skill 的名称"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """返回 Skill 的描述"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        返回 Skill 的 JSON Schema 定义
        用于描述输入参数
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行 Skill 的核心逻辑

        Args:
            **kwargs: Skill 的输入参数

        Returns:
            包含执行结果的字典
        """
        pass

