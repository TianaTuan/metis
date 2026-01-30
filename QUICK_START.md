# Metis 快速启动指南

## 前置要求

1. **Python 3.12+**
2. **uv** 包管理器（推荐）或 pip
3. **LLM Provider** 配置（OpenAI、Qwen 等）

## 安装步骤

### 1. 安装依赖

使用 `uv`（推荐）：
```bash
# 创建虚拟环境
uv venv

# 安装 Metis
uv pip install .

# 或安装到系统（不推荐）
uv pip install . --system
```

使用 `pip`：
```bash
pip install .
```

### 2. 配置 LLM Provider

#### 方式 1：使用环境变量（OpenAI）
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

#### 方式 2：配置 metis.yaml

在项目根目录或工作目录创建 `metis.yaml`：

**使用 Qwen（示例）**：
```yaml
llm_provider:
  name: "openai"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-max"
  code_embedding_model: "text-embedding-v1"
  docs_embedding_model: "text-embedding-v1"

query:
  similarity_top_k: 5
  response_mode: "tree_summarize"
  max_tokens: 5000
  temperature: 0.0
  min_retrieval_score: 0.7  # 可选：最小相关性分数

metis_engine:
  max_token_length: 250000
  max_workers: 10
  enable_call_graph: true  # 启用调用图增强（默认：true）
```

**使用 OpenAI**：
```yaml
llm_provider:
  name: "openai"
  model: "gpt-4o-mini"
  code_embedding_model: "text-embedding-3-small"
  docs_embedding_model: "text-embedding-3-small"
```

**使用 Ollama（本地）**：
```yaml
llm_provider:
  name: "ollama"
  model: "llama3.1"
  base_url: "http://localhost:11434/v1"
  code_embedding_model: "all-minilm"
  docs_embedding_model: "all-minilm"
```

## 启动方式

### 方式 1：交互式 CLI（推荐）

```bash
# 基本启动
metis --codebase-path <你的代码库路径>

# 或使用 uv run
uv run metis --codebase-path <你的代码库路径>

# 带详细日志
metis --codebase-path <路径> --verbose

# 指定后端（ChromaDB 或 PostgreSQL）
metis --codebase-path <路径> --backend chroma
metis --codebase-path <路径> --backend postgres --project-schema myproject
```

启动后，在交互式命令行中输入命令：

```
> index              # 索引代码库
> review_code        # 审查整个代码库
> review_file <文件路径>  # 审查单个文件
> review_patch <diff文件>  # 审查补丁
> ask "你的问题"     # 询问代码库相关问题
> report             # 生成报告
> help               # 查看帮助
> exit               # 退出
```

### 方式 2：非交互式模式（适合 CI/CD）

```bash
# 索引代码库
metis --non-interactive --command "index" --codebase-path <路径>

# 审查代码
metis --non-interactive --command "review_code" --codebase-path <路径> --output-file results.json

# 审查单个文件
metis --non-interactive --command "review_file src/main.py" --codebase-path <路径>

# 生成报告
metis --non-interactive --command "report" --codebase-path <路径> --output-file report.html
```

## 完整使用流程

### 1. 首次使用

```bash
# 1. 进入你的项目目录
cd /path/to/your/project

# 2. 创建 metis.yaml（如果还没有）
# 参考上面的配置示例

# 3. 启动 Metis
metis --codebase-path .

# 4. 在交互式命令行中：
> index              # 索引代码库（首次必须运行）
```

### 2. 进行安全审查

```bash
# 在 Metis 交互式命令行中：
> review_code        # 审查整个代码库
> review_file src/main.py  # 审查特定文件
> review_patch changes.diff  # 审查补丁文件
```

### 3. 生成报告

```bash
# 在 Metis 交互式命令行中：
> report             # 生成 HTML 报告（默认）

# 或指定输出格式
> report --output-file report.html
> report --output-file report.csv
> report --output-file report.sarif
```

### 4. 询问代码库问题

```bash
# 在 Metis 交互式命令行中：
> ask "这个项目使用了哪些加密算法？"
> ask "如何验证用户输入？"
```

## 常用命令行选项

```bash
# 基本选项
--codebase-path <路径>      # 指定代码库路径（必需）
--backend chroma|postgres   # 选择向量存储后端（默认：chroma）
--verbose                   # 显示详细输出
--quiet                     # 静默模式
--output-file <文件>        # 指定输出文件

# 高级选项
--custom-prompt <文件>      # 自定义提示词文件（.md 或 .txt）
--project-schema <名称>     # PostgreSQL 项目模式名称
--chroma-dir <目录>         # ChromaDB 数据目录
--log-level DEBUG|INFO|WARNING|ERROR  # 日志级别

# 过滤和排序（用于 report 命令）
--min-confidence <0.0-1.0>  # 最小置信度阈值
--severity-filter Critical|High|Medium|Low  # 严重程度过滤
```

## 使用示例

### 示例 1：审查 Python 项目

```bash
# 1. 进入项目目录
cd /path/to/python/project

# 2. 启动 Metis
metis --codebase-path . --verbose

# 3. 索引
> index

# 4. 审查
> review_code

# 5. 生成报告
> report --output-file security_report.html
```

### 示例 2：审查单个文件

```bash
metis --codebase-path . --non-interactive \
  --command "review_file src/auth.py" \
  --output-file auth_review.json
```

### 示例 3：使用 PostgreSQL 后端

```bash
# 1. 启动 PostgreSQL（使用 Docker）
docker compose up -d

# 2. 运行 Metis
metis \
  --codebase-path . \
  --backend postgres \
  --project-schema myproject_main \
  --verbose
```

### 示例 4：使用自定义提示词

```bash
# 创建 .metis.md 文件（在项目根目录）
echo "# 安全审查规则
- 检查所有用户输入验证
- 检查 SQL 注入风险
- 检查 XSS 漏洞" > .metis.md

# 启动 Metis（会自动加载 .metis.md）
metis --codebase-path .
```

## 故障排查

### 1. 模块未找到错误

```bash
# 确保已安装
uv pip install .

# 或使用 uv run
uv run metis --codebase-path .
```

### 2. LLM Provider 配置错误

检查：
- `metis.yaml` 文件是否存在且配置正确
- API Key 是否设置（如需要）
- base_url 是否正确（对于自定义端点）

### 3. 索引失败

- 检查代码库路径是否正确
- 检查文件权限
- 查看详细日志：`--verbose --log-level DEBUG`

### 4. 调用图增强未工作

- 检查 `metis.yaml` 中 `enable_call_graph: true`
- 查看日志确认调用图是否构建成功

## 下一步

- 查看 [README.md](README.md) 了解详细功能
- 查看 [RAG_OPTIMIZATION.md](RAG_OPTIMIZATION.md) 了解 RAG 优化
- 查看 [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md) 了解 MCP 架构

## 获取帮助

```bash
# 在 Metis 交互式命令行中
> help

# 或查看版本
> version
```

