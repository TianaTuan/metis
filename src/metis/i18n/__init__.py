# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
国际化支持
"""

# 默认语言
DEFAULT_LANGUAGE = "zh_CN"

# 语言映射
LANGUAGES = {
    "zh_CN": "zh_CN",
    "zh": "zh_CN",
    "chinese": "zh_CN",
    "en_US": "en_US",
    "en": "en_US",
    "english": "en_US",
}

# 中文文本
ZH_CN_TEXTS = {
    # CLI 命令提示
    "indexing_codebase": "正在索引代码库...",
    "indexing_completed": "索引完成。",
    "embedding_indexes": "正在生成嵌入向量...",
    "reviewing_codebase": "正在审查代码库...",
    "reviewing_file": "正在审查文件 {file_path}...",
    "reviewing_patch": "正在审查补丁...",
    "updating_index": "正在更新索引...",
    "index_update_completed": "索引更新完成。",
    "thinking": "正在思考...",
    "generating_report": "正在生成报告...",
    "report_generated": "报告已生成，发现 {count} 个问题。",
    "no_output_file_specified": "未指定输出文件，使用默认: {path}",
    
    # Help 文本
    "help_commands": "输入以下命令之一（带参数）",
    "help_report": "生成 HTML/CSV/SARIF 报告",
    "help_exit": "退出工具",
    "help_show": "显示此消息",
    "help_options": "选项",
    "help_backend": "使用的向量后端（默认：chroma）",
    "help_output_file": "将分析结果保存到此文件",
    "help_custom_prompt": "自定义提示词文件（.md 或 .txt）以指导分析",
    "help_project_schema": "（可选）如果使用 postgresql，项目标识符",
    "help_chroma_dir": "（可选）存储 ChromaDB 数据的目录（默认：./chromadb）",
    "help_verbose": "（可选）在终端窗口中显示详细输出",
    "help_version": "（可选）显示程序版本",
    "ask_example": "给我一个代码概览",
    
    # 输出消息
    "html_report_saved": "HTML 报告已保存到 {path}",
    "csv_report_saved": "CSV 报告已保存到 {path}",
    "sarif_report_saved": "SARIF 报告已保存到 {path}",
    "json_report_saved": "JSON 报告已保存到 {path}",
    "failed_to_generate_html": "生成 HTML 报告失败。",
    "failed_to_generate_csv": "生成 CSV 报告失败。",
    "failed_to_generate_sarif": "生成 SARIF 报告失败。",
    
    # 审查结果
    "file": "文件",
    "line": "行号",
    "severity": "严重程度",
    "issue": "问题",
    "reasoning": "原因",
    "mitigation": "修复建议",
    "confidence": "置信度",
    "cwe": "CWE",
    "no_issues_found": "未发现安全问题",
    "issues_found": "发现 {count} 个安全问题",
    
    # 严重程度
    "severity_critical": "严重",
    "severity_high": "高",
    "severity_medium": "中",
    "severity_low": "低",
    
    # Metis Answer
    "metis_answer": "Metis 回答：",
    "code_context": "代码上下文：",
    "documentation_context": "文档上下文：",
    
    # 审查结果详情
    "code_snippet": "代码片段",
    "no_issues_in_file": "文件 {file} 中未发现问题",
    "issues_found": "发现问题 {count}",
}

# 英文文本（默认）
EN_US_TEXTS = {
    "indexing_codebase": "Indexing codebase...",
    "indexing_completed": "Indexing completed successfully.",
    "reviewing_codebase": "Reviewing codebase...",
    "reviewing_file": "Reviewing file {file_path}...",
    "reviewing_patch": "Reviewing patch...",
    "updating_index": "Updating index...",
    "index_update_completed": "Index update completed.",
    "thinking": "Thinking...",
    "generating_report": "Generating report...",
    "report_generated": "Report generated with {count} issue(s) found.",
    
    "html_report_saved": "HTML report saved to {path}",
    "csv_report_saved": "CSV report saved to {path}",
    "sarif_report_saved": "SARIF report saved to {path}",
    "json_report_saved": "JSON report saved to {path}",
    "failed_to_generate_html": "Failed to generate HTML report.",
    "failed_to_generate_csv": "Failed to generate CSV report.",
    "failed_to_generate_sarif": "Failed to generate SARIF report.",
    
    "file": "File",
    "line": "Line",
    "severity": "Severity",
    "issue": "Issue",
    "reasoning": "Reasoning",
    "mitigation": "Mitigation",
    "confidence": "Confidence",
    "cwe": "CWE",
    "no_issues_found": "No security issues found",
    "issues_found": "Found {count} security issue(s)",
    
    "severity_critical": "Critical",
    "severity_high": "High",
    "severity_medium": "Medium",
    "severity_low": "Low",
    
    "metis_answer": "Metis Answer:",
    "code_context": "Code Context:",
    "documentation_context": "Documentation Context:",
}

# 文本字典
TEXTS = {
    "zh_CN": ZH_CN_TEXTS,
    "en_US": EN_US_TEXTS,
}

# 当前语言
_current_language = DEFAULT_LANGUAGE


def set_language(language: str):
    """设置当前语言"""
    global _current_language
    normalized = LANGUAGES.get(language.lower(), DEFAULT_LANGUAGE)
    _current_language = normalized


def get_language() -> str:
    """获取当前语言"""
    return _current_language


def t(key: str, **kwargs) -> str:
    """
    翻译文本
    
    Args:
        key: 文本键
        **kwargs: 格式化参数
    
    Returns:
        翻译后的文本
    """
    texts = TEXTS.get(_current_language, EN_US_TEXTS)
    text = texts.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text

