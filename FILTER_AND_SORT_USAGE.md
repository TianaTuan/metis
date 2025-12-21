# 结果排序和过滤功能使用指南

## 功能概述

已实现两个主要优化功能：

1. **结果排序和过滤**：按严重程度和置信度排序，并可过滤低置信度问题
2. **上下文检索优化**：提高 RAG 检索的相关性，过滤低相关性结果

## 1. 结果排序和过滤

### 命令行参数

```bash
# 设置最小置信度阈值（0.0-1.0）
--min-confidence 0.7

# 按严重程度过滤（可以指定多个）
--severity-filter High Critical
```

### 使用示例

```bash
# 只显示置信度 >= 0.8 的问题
uv run metis --codebase-path ./target --non-interactive --command "review_code" --min-confidence 0.8

# 只显示 High 和 Critical 级别的问题
uv run metis --codebase-path ./target --non-interactive --command "review_code" --severity-filter High Critical

# 组合使用：只显示 High/Critical 且置信度 >= 0.7 的问题
uv run metis --codebase-path ./target --non-interactive --command "review_code" \
  --min-confidence 0.7 \
  --severity-filter High Critical
```

### 排序规则

问题按以下优先级排序：
1. **严重程度**：Critical > High > Medium > Low
2. **置信度**：高置信度优先

### 配置示例

在交互式模式下，这些参数也会生效：

```bash
uv run metis --codebase-path ./target --min-confidence 0.7
> review_code
```

## 2. 上下文检索优化

### 配置方式

在 `metis.yaml` 文件中添加检索优化配置：

```yaml
query:
  similarity_top_k: 5
  response_mode: "tree_summarize"
  max_tokens: 5000
  temperature: 0.0
  # 可选：最小相关性分数阈值（0.0-1.0）
  # 只有相似度分数 >= min_retrieval_score 的文档才会被使用
  min_retrieval_score: 0.7
```

### 工作原理

1. **相关性过滤**：如果检索器支持相似度分数，会自动过滤掉低于阈值的文档
2. **文档数量限制**：使用 `similarity_top_k` 限制返回的文档数量
3. **智能回退**：如果过滤后没有文档，会使用原始结果（最多 `similarity_top_k` 个）

### 优化效果

- **提高准确性**：只使用高相关性的上下文，减少噪音
- **减少 Token 消耗**：过滤低相关性文档，节省 API 调用成本
- **提升性能**：减少传递给 LLM 的上下文长度，加快响应速度

## 3. 完整配置示例

```yaml
# metis.yaml
metis_engine:
  max_token_length: 250000
  max_workers: 10
  embed_dim: 3072

llm_provider:
  name: "openai"
  model: "gpt-4o-mini"
  code_embedding_model: "text-embedding-3-small"
  docs_embedding_model: "text-embedding-3-small"

query:
  similarity_top_k: 5
  response_mode: "tree_summarize"
  max_tokens: 5000
  temperature: 0.0
  # 检索优化：只使用相似度 >= 0.7 的文档
  min_retrieval_score: 0.7
```

## 4. 使用建议

### 结果过滤建议

- **开发阶段**：使用较低的置信度阈值（0.5-0.6），查看所有潜在问题
- **CI/CD 集成**：使用较高的置信度阈值（0.7-0.8），只报告高置信度问题
- **安全审计**：使用最高置信度（0.8-0.9），只关注确认的问题

### 检索优化建议

- **小型项目**：可以不设置 `min_retrieval_score`，使用所有检索结果
- **大型项目**：设置 `min_retrieval_score: 0.7`，过滤低相关性结果
- **高精度需求**：设置 `min_retrieval_score: 0.8`，只使用高相关性上下文

## 5. 性能影响

### 结果排序和过滤
- **性能影响**：几乎无影响（内存操作）
- **内存占用**：可忽略
- **适用场景**：所有场景

### 上下文检索优化
- **性能影响**：轻微提升（减少传递给 LLM 的上下文）
- **Token 节省**：根据项目大小，可节省 10-30% 的 Token
- **准确性提升**：减少不相关上下文带来的噪音

## 6. 注意事项

1. **置信度阈值**：设置过高可能漏掉真实问题，设置过低可能产生误报
2. **检索分数**：不是所有检索器都支持相似度分数，如果不支持，该功能会自动回退
3. **兼容性**：这些功能向后兼容，不影响现有配置

## 7. 故障排除

如果遇到问题：

1. **检查配置**：确保 `metis.yaml` 格式正确
2. **查看日志**：使用 `--verbose` 查看详细信息
3. **测试参数**：先使用默认值测试，再逐步调整

