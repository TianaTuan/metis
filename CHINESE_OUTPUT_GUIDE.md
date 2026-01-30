# 中文输出配置指南

## 概述

Metis 现在支持中文输出，包括：
1. CLI 界面文本（命令提示、状态信息等）
2. LLM 审查结果（问题描述、原因分析、修复建议等）
3. 报告生成（HTML、CSV、SARIF）

## 配置方式

### 方式 1：命令行参数（推荐）

```bash
metis --codebase-path <路径> --language zh_CN
```

### 方式 2：配置文件

在 `metis.yaml` 中添加：

```yaml
language: zh_CN  # 或 "en_US" 使用英文
```

### 方式 3：环境变量

```bash
export METIS_LANGUAGE=zh_CN
metis --codebase-path <路径>
```

## 语言选项

- `zh_CN` 或 `zh` - 简体中文（默认）
- `en_US` 或 `en` - 英文

## LLM 提示词配置

为了确保 LLM 输出中文，提示词已自动添加中文要求。如果需要自定义，可以在 `plugins.yaml` 的提示词中添加：

```
IMPORTANT: All your responses (issue descriptions, reasoning, mitigation suggestions) must be in Chinese (Simplified).
```

## 使用示例

### 基本使用

```bash
# 使用中文输出（默认）
metis --codebase-path . --language zh_CN

# 在交互式命令行中
> index
> review_code
```

### 输出示例

中文输出示例：

```
文件: src/main.c
发现问题 1: 缓冲区溢出风险
    代码片段: char buffer[10]; strcpy(buffer, user_input);
    行号: 42
    严重程度: 高
    原因: 使用 strcpy 函数时未检查输入长度，可能导致缓冲区溢出
    修复建议: 使用 strncpy 或 snprintf 函数，并检查输入长度
    置信度: 0.9
    CWE: CWE-120
```

## 修改的组件

### 1. CLI 输出

- 所有命令提示信息
- 状态消息
- 错误信息
- 审查结果展示

### 2. LLM 提示词

- `plugins.yaml` 中的提示词已添加中文要求
- `general_prompts.retrieve_context` 添加中文要求
- `general_prompts.security_review_report` 添加中文要求
- 各语言的 `security_review_file` 和 `security_review` 提示词添加中文要求

### 3. 报告生成

- HTML 报告中的文本（通过 LLM 生成的内容）
- CSV 报告列名（可通过修改代码自定义）
- SARIF 报告（标准格式，语言由 LLM 输出决定）

## 自定义翻译

如果需要修改翻译文本，编辑 `src/metis/i18n/__init__.py`：

```python
ZH_CN_TEXTS = {
    "your_key": "你的翻译文本",
    ...
}
```

## 注意事项

1. **LLM 输出语言**：虽然提示词要求中文，但某些 LLM 可能仍会输出英文。如果遇到，可以在自定义提示词中更明确地要求中文。

2. **报告格式**：HTML 报告中的内容由 LLM 生成，语言取决于 LLM 的响应。

3. **向后兼容**：如果不设置语言，默认使用中文（zh_CN）。

4. **混合语言**：某些技术术语（如 CWE、函数名）可能保持英文，这是正常的。

## 故障排查

### LLM 仍然输出英文

1. 检查 `plugins.yaml` 中的提示词是否包含中文要求
2. 在 `metis.yaml` 中添加自定义提示词文件，明确要求中文
3. 检查 LLM 模型是否支持中文

### CLI 输出不是中文

1. 检查 `--language` 参数是否正确
2. 检查 `metis.yaml` 中的 `language` 配置
3. 确认 `src/metis/i18n/__init__.py` 文件存在且正确

