# Embedding 批量大小限制修复

## 问题描述

在索引代码库时，遇到错误：
```
batch size is invalid, it should not be larger than 25
```

这是因为 embedding API 有硬性限制：单次请求的 `contents` 数组不能超过 25 条内容。

## 修复方案

### 1. 自动设置批量大小限制

在 `OpenAICompatibleEmbeddingProvider` 和 `OpenAICompatibleProvider` 的 `_build_embedding_model` 方法中：

- **默认批量大小**：设置为 20（留 5 的余量，避免超过 API 限制）
- **用户配置**：如果用户在 `extra_kwargs` 中指定了 `batch_size`，会验证并确保不超过 25
- **自动修正**：如果用户配置的 `batch_size` 超过 25，会自动调整为 20 并记录警告

### 2. 修改的文件

1. **`src/metis/providers/embedding_openai.py`**
   - 添加了 `batch_size` 参数设置
   - 添加了 logger 用于记录警告

2. **`src/metis/providers/openai_compatible.py`**
   - 在 `_build_embedding_model` 方法中添加了 `batch_size` 限制

### 3. 配置方式

#### 方式 1：使用默认值（推荐）

不需要任何配置，系统会自动使用 `batch_size=20`。

#### 方式 2：在 metis.yaml 中自定义

```yaml
llm_provider:
  name: "openai"
  code_embedding_model: "text-embedding-v1"
  docs_embedding_model: "text-embedding-v1"
  code_embedding_extra_kwargs:
    batch_size: 20  # 可选：自定义批量大小（最大 25）
  docs_embedding_extra_kwargs:
    batch_size: 20
```

#### 方式 3：使用独立的 embedding_provider

```yaml
embedding_provider:
  name: "openai_compatible"
  code_embedding_model: "text-embedding-v1"
  docs_embedding_model: "text-embedding-v1"
  code_embedding_extra_kwargs:
    batch_size: 20
  docs_embedding_extra_kwargs:
    batch_size: 20
```

## 工作原理

1. **初始化时**：在创建 `OpenAIEmbedding` 实例时，会自动设置 `batch_size=20`
2. **验证**：如果用户配置的 `batch_size > 25`，会自动调整为 20
3. **传递**：`batch_size` 参数会传递给 `OpenAIEmbedding`，由 llama_index 在内部使用

## 验证修复

修复后，重新运行索引：

```bash
metis --codebase-path <路径>
> index
```

应该不会再出现 "batch size is invalid" 错误。

## 注意事项

1. **性能影响**：较小的 `batch_size` 可能会稍微降低索引速度，但可以避免 API 错误
2. **API 限制**：不同的 embedding API 可能有不同的批量限制，当前修复针对 25 的限制
3. **向后兼容**：如果用户已经配置了 `batch_size`，会尊重用户配置（但会验证不超过 25）

## 技术细节

`llama_index` 的 `OpenAIEmbedding` 类支持 `batch_size` 参数，该参数控制：
- 单次 API 调用处理的文本数量
- 内部批处理逻辑

通过设置 `batch_size=20`，确保每次 API 调用最多处理 20 条内容，不会超过 API 的 25 条限制。

