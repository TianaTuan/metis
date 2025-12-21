# 报告导出功能使用指南

Metis 支持多种格式的报告导出，包括 HTML、CSV、SARIF 和 JSON。

## 📊 支持的导出格式

1. **HTML 报告** (`.html`) - 使用 `report_template.html` 模板生成美观的可视化报告
2. **CSV 报告** (`.csv`) - 表格格式，适合 Excel 分析
3. **SARIF 报告** (`.sarif`) - 标准安全报告格式，可导入 GitHub Security、Azure DevOps 等
4. **JSON 报告** (`.json`) - 原始数据格式，适合程序化处理

## 🚀 使用方法

### 方法 1: 使用 `--output-file` 参数（推荐）

Metis 会根据文件扩展名自动识别导出格式：

```bash
# 导出 HTML 报告
uv run metis --codebase-path ./target --non-interactive --command "review_code" --output-file report.html

# 导出 CSV 报告
uv run metis --codebase-path ./target --non-interactive --command "review_code" --output-file report.csv

# 导出 SARIF 报告
uv run metis --codebase-path ./target --non-interactive --command "review_code" --output-file report.sarif

# 导出 JSON 报告（默认）
uv run metis --codebase-path ./target --non-interactive --command "review_code" --output-file report.json

# 同时导出多种格式
uv run metis --codebase-path ./target --non-interactive --command "review_code" \
  --output-file report.html \
  --output-file report.csv \
  --output-file report.sarif
```

### 方法 2: 在交互式模式下使用

```bash
uv run metis --codebase-path ./target --output-file report.html
> review_code
```

### 方法 3: 审查特定文件并导出

```bash
# 审查单个文件并导出 HTML 报告
uv run metis --codebase-path ./target --non-interactive \
  --command "review_file target/dvcp.c" \
  --output-file dvcp_report.html

# 审查补丁并导出 SARIF 报告
uv run metis --codebase-path ./target --non-interactive \
  --command "review_patch patch.diff" \
  --output-file patch_report.sarif
```

## 📋 HTML 报告特性

HTML 报告使用 `report_template.html` 模板，包含以下特性：

### 可视化功能
- ✅ **统计图表**：严重程度分布、CWE 分布、文件统计
- ✅ **交互式过滤**：按严重程度、CWE、文件过滤
- ✅ **问题详情**：展开查看完整的问题描述、代码片段、修复建议
- ✅ **深色/浅色主题**：支持主题切换
- ✅ **响应式设计**：适配不同屏幕尺寸

### 报告内容
- 问题总数和统计
- 按严重程度分类的问题
- 按 CWE 分类的问题
- 每个问题的详细信息：
  - 文件路径和行号
  - 严重程度和置信度
  - CWE 标识符（带链接）
  - 问题描述
  - 代码片段
  - 修复建议

## 📝 CSV 报告格式

CSV 报告包含以下列：
- File: 文件路径
- Line: 行号
- Severity: 严重程度
- CWE: CWE 标识符
- Issue: 问题描述
- Reasoning: 原因说明
- Mitigation: 修复建议
- Confidence: 置信度

## 🔧 SARIF 报告格式

SARIF (Static Analysis Results Interchange Format) 是标准的安全报告格式，可以：
- 导入到 GitHub Security
- 导入到 Azure DevOps Security
- 导入到其他支持 SARIF 的工具

## 💡 使用示例

### 示例 1: 生成完整的 HTML 报告

```bash
uv run metis --codebase-path ./target \
  --non-interactive \
  --command "review_code" \
  --output-file security_report.html
```

生成的报告包含：
- 所有发现的安全问题
- 可视化统计图表
- 可交互的问题列表

### 示例 2: 只导出高严重程度问题

```bash
uv run metis --codebase-path ./target \
  --non-interactive \
  --command "review_code" \
  --min-confidence 0.7 \
  --severity-filter High Critical \
  --output-file critical_issues.html
```

### 示例 3: 生成多种格式的报告

```bash
uv run metis --codebase-path ./target \
  --non-interactive \
  --command "review_code" \
  --output-file report.html \
  --output-file report.csv \
  --output-file report.sarif \
  --output-file report.json
```

### 示例 4: CI/CD 集成

```bash
# 在 CI 中生成 SARIF 报告并上传到 GitHub
uv run metis --codebase-path . \
  --non-interactive \
  --command "review_code" \
  --output-file metis-results.sarif

# GitHub Actions 会自动识别并显示在 Security 标签页
```

## 🎨 自定义 HTML 报告模板

如果你想自定义 HTML 报告模板：

1. 复制 `src/metis/cli/report_template.html` 到你的项目
2. 修改模板（添加公司 logo、自定义样式等）
3. 修改代码以使用自定义模板（需要修改源码）

## 📊 报告文件位置

- **默认位置**：当前工作目录
- **自动创建目录**：如果路径包含目录，会自动创建
- **文件命名**：可以自定义文件名和路径

示例：
```bash
# 保存到 reports 目录
--output-file reports/security_report.html

# 保存到指定目录
--output-file /path/to/reports/metis_report.html
```

## 🔍 查看报告

### HTML 报告
直接在浏览器中打开生成的 `.html` 文件即可查看。

### CSV 报告
使用 Excel、Google Sheets 或其他表格软件打开。

### SARIF 报告
- GitHub: 上传到仓库的 Security 标签页
- VS Code: 使用 SARIF Viewer 扩展
- 在线查看器: https://sarifweb.azurewebsites.net/

## ⚙️ 高级用法

### 结合过滤和排序导出

```bash
# 只导出高置信度问题，按严重程度排序
uv run metis --codebase-path ./target \
  --non-interactive \
  --command "review_code" \
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
    --non-interactive \
    --command "review_code" \
    --output-file "reports/${project}_report.html"
done
```

## 🐛 故障排除

### 问题：HTML 报告生成失败
- 检查文件路径是否有效
- 确保有写入权限
- 查看日志了解详细错误信息

### 问题：报告为空
- 确保已经运行了 `index` 命令
- 检查是否有安全问题被发现
- 尝试降低 `--min-confidence` 阈值

### 问题：SARIF 报告无法导入
- 确保文件扩展名是 `.sarif`
- 检查 SARIF 格式版本兼容性
- 验证文件内容格式是否正确

