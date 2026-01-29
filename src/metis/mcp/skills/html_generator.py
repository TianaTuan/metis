# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
HTML 报告生成 Skill
将 HTML 报告生成功能封装为独立的 MCP Skill
"""

import json
from pathlib import Path
from typing import Any, Dict

from importlib.resources import files, as_file

from metis.cli.exporters import export_html, _flatten_issues
from metis.mcp.skills.base import BaseSkill
from metis.version import __version__


class HTMLGeneratorSkill(BaseSkill):
    """
    HTML 报告生成 Skill
    将安全审查结果生成为 HTML 报告
    """

    def __init__(self):
        """初始化 HTML 生成器 Skill"""
        self._template = None

    def get_name(self) -> str:
        """返回 Skill 名称"""
        return "generate_html_report"

    def get_description(self) -> str:
        """返回 Skill 描述"""
        return (
            "生成安全审查结果的 HTML 报告。"
            "接受审查结果数据，生成包含统计信息、问题列表和可视化图表的 HTML 报告。"
        )

    def get_schema(self) -> Dict[str, Any]:
        """返回 Skill 的 JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "report_data": {
                    "type": "object",
                    "description": "安全审查结果数据，包含 reviews 字段",
                    "required": True,
                },
                "output_path": {
                    "type": "string",
                    "description": "输出 HTML 文件的路径",
                    "default": "reports/metis_report.html",
                },
                "template_path": {
                    "type": "string",
                    "description": "自定义 HTML 模板路径（可选）",
                    "default": None,
                },
            },
            "required": ["report_data"],
        }

    def _load_template(self, template_path: str | None = None) -> str:
        """
        加载 HTML 模板

        Args:
            template_path: 自定义模板路径，如果为 None 则使用默认模板

        Returns:
            模板内容字符串
        """
        if self._template is not None:
            return self._template

        if template_path and Path(template_path).exists():
            self._template = Path(template_path).read_text(encoding="utf-8")
        else:
            # 使用默认模板
            resource = files("metis.cli") / "report_template.html"
            if not resource.is_file():
                raise FileNotFoundError("Default HTML template not found")
            with as_file(resource) as real_path:
                self._template = real_path.read_text(encoding="utf-8")

        return self._template

    def execute(
        self,
        report_data: Dict[str, Any],
        output_path: str = "reports/metis_report.html",
        template_path: str | None = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行 HTML 报告生成

        Args:
            report_data: 安全审查结果数据
            output_path: 输出文件路径
            template_path: 自定义模板路径（可选）
            **kwargs: 其他参数（忽略）

        Returns:
            包含生成结果的字典
        """
        try:
            # 加载模板
            template = self._load_template(template_path)

            # 生成 HTML
            output_file = Path(output_path)
            html_path = export_html(
                report_data=report_data,
                output_path=output_file,
                template=template,
                metis_version=__version__,
            )

            # 统计信息
            issues = _flatten_issues(report_data)
            total_issues = len(issues)

            return {
                "success": True,
                "html_path": str(html_path),
                "total_issues": total_issues,
                "message": f"HTML report generated successfully at {html_path}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate HTML report: {e}",
            }

