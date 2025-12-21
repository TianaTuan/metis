# 报告导出功能快速指南

## 🎯 快速开始

### 方法 1: 使用新的 `report` 命令（最简单）

```bash
# 生成 HTML 报告（默认格式）
uv run metis --codebase-path ./target report

# 生成指定格式的报告
uv run metis --codebase-path ./target report --output-file report.html
uv run metis --codebase-path ./target report --output-file report.csv
uv run metis --codebase-path ./target report --output-file report.sarif
```

### 方法 2: 在审查命令中使用 `--output-file`

```bash
# 审查代码并导出 HTML 报告
uv run metis --codebase-path ./target \
  --non-interactive \
  --command "review_code" \
  --output-file report.html
```

## 📊 支持的格式

| 格式 | 扩展名 | 用途 | 特点 |
|------|--------|------|------|
| **HTML** | `.html` | 可视化报告 | 交互式图表、过滤、主题切换 |
| **CSV** | `.csv` | 数据分析 | Excel 兼容、易于处理 |
| **SARIF** | `.sarif` | CI/CD 集成 | GitHub Security、Azure DevOps |
| **JSON** | `.json` | 程序处理 | 原始数据、API 集成 |

## 💡 使用示例

### 示例 1: 生成完整的 HTML 报告

```bash
uv run metis --codebase-path ./target report --output-file security_report.html
```

生成的报告包含：
- 📊 统计图表（严重程度、CWE 分布）
- 🔍 交互式过滤
- 📝 详细的问题信息
- 🎨 深色/浅色主题

### 示例 2: 生成过滤后的报告

```bash
# 只包含高严重程度和高置信度的问题
uv run metis --codebase-path ./target \
  report \
  --min-confidence 0.7 \
  --severity-filter High Critical \
  --output-file critical_issues.html
```

### 示例 3: 生成多种格式

```bash
uv run metis --codebase-path ./target \
  report \
  --output-file report.html \
  --output-file report.csv \
  --output-file report.sarif
```

### 示例 4: CI/CD 集成

```bash
# 在 CI 中生成 SARIF 报告
uv run metis --codebase-path . \
  --non-interactive \
  --command "report" \
  --output-file metis-results.sarif
```

## 📁 报告模板说明

### HTML 报告模板 (`report_template.html`)

HTML 报告使用 `src/metis/cli/report_template.html` 模板，包含：

1. **统计面板**
   - 问题总数
   - 按严重程度分类
   - 按 CWE 分类
   - 按文件/文件夹分类

2. **交互式图表**
   - 使用 ECharts 库
   - 可点击查看详情
   - 支持最大化查看

3. **问题列表**
   - 可展开查看详情
   - 显示代码片段
   - 显示修复建议
   - 链接到 CWE 定义

4. **过滤功能**
   - 按严重程度过滤
   - 按 CWE 过滤
   - 按文件过滤

5. **主题切换**
   - 深色主题（默认）
   - 浅色主题

## 🔧 高级用法

### 自定义报告输出位置

```bash
# 保存到指定目录
uv run metis --codebase-path ./target \
  report \
  --output-file reports/2025/security_report.html
```

### 结合过滤和排序

```bash
uv run metis --codebase-path ./target \
  report \
  --min-confidence 0.8 \
  --severity-filter High Critical \
  --output-file filtered_report.html
```

### 批量生成报告

```bash
#!/bin/bash
# 为多个项目生成报告
for project in project1 project2 project3; do
  uv run metis --codebase-path "./$project" \
    report \
    --output-file "reports/${project}_report.html"
done
```

## 📖 查看报告

### HTML 报告
直接在浏览器中打开 `.html` 文件即可。

### CSV 报告
使用 Excel、Google Sheets 或其他表格软件打开。

### SARIF 报告
- **GitHub**: 上传到仓库的 Security 标签页
- **VS Code**: 使用 SARIF Viewer 扩展
- **在线查看器**: https://sarifweb.azurewebsites.net/

## 🎨 HTML 报告功能演示

打开 HTML 报告后，你可以：

1. **查看统计图表**
   - 点击图表查看详情
   - 使用最大化按钮全屏查看

2. **过滤问题**
   - 使用顶部的过滤器下拉菜单
   - 按严重程度、CWE、文件过滤

3. **查看问题详情**
   - 点击问题标题展开
   - 查看代码片段、修复建议
   - 点击 CWE 链接查看详细定义

4. **切换主题**
   - 点击右上角的主题切换按钮
   - 在深色和浅色主题间切换

## ⚠️ 注意事项

1. **必须先索引**：运行 `report` 前需要先运行 `index` 命令
2. **文件格式**：根据文件扩展名自动识别格式（`.html`, `.csv`, `.sarif`, `.json`）
3. **默认位置**：如果不指定 `--output-file`，默认保存到 `reports/` 目录

## 🚀 完整工作流程

```bash
# 1. 索引代码库
uv run metis --codebase-path ./target index

# 2. 生成报告
uv run metis --codebase-path ./target report --output-file report.html

# 3. 在浏览器中查看
open report.html
```

## 📝 报告内容说明

### HTML 报告包含：
- ✅ 问题统计（总数、按严重程度、按 CWE）
- ✅ 交互式图表
- ✅ 详细的问题列表
- ✅ 代码片段
- ✅ 修复建议
- ✅ CWE 链接

### CSV 报告包含：
- File, Line, Severity, CWE, Issue, Reasoning, Mitigation, Confidence

### SARIF 报告包含：
- 标准 SARIF 格式的所有字段
- 可用于 CI/CD 集成

