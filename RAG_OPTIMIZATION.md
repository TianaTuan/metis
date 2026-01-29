# RAG 优化说明

## 概述

Metis 的 RAG（Retrieval-Augmented Generation）系统已优化，现在支持：
1. **函数调用关系追踪**：自动分析代码中的函数调用链
2. **多轮检索**：先进行语义检索，再基于调用关系进行补充检索
3. **增强的上下文构建**：包含函数调用关系信息

## 核心功能

### 1. 调用图分析 (`src/metis/rag/call_graph.py`)

`CallGraphAnalyzer` 类可以：
- 提取函数定义
- 提取函数调用
- 构建调用图
- 查找调用链（被调用函数和调用者）

支持的语言：
- Python
- JavaScript/TypeScript
- C/C++
- Go
- Rust

### 2. 增强检索器 (`src/metis/rag/enhanced_retriever.py`)

`EnhancedRetriever` 类提供：
- **多轮检索**：
  - 第一轮：基于语义相似度的检索
  - 第二轮：基于函数调用关系的检索
- **智能查询构建**：从代码片段中提取函数名，构建函数查询
- **增强上下文**：在上下文中包含函数调用关系信息

### 3. 集成到 Review Graph

增强的检索已集成到 `review_node_retrieve` 中：
- 自动检测是否启用调用图
- 如果可用，使用增强检索器
- 如果不可用，回退到传统检索方法

## 使用方法

### 启用调用图增强

调用图增强默认启用。可以通过配置禁用：

```python
engine = MetisEngine(
    ...,
    enable_call_graph=False,  # 禁用调用图增强
)
```

### 配置参数

在 `metis.yaml` 中可以配置：

```yaml
metis_engine:
  enable_call_graph: true  # 启用调用图增强（默认：true）
  similarity_top_k: 5      # 每轮检索的文档数
  min_retrieval_score: 0.7 # 最小相关性分数
```

## 工作原理

### 索引阶段

1. 代码文件被解析和分块
2. 对每个代码文件分析调用图
3. 调用图信息存储在 `_call_graph_cache` 中

### 检索阶段

1. **第一轮检索**：基于语义相似度检索相关代码
2. **函数提取**：从查询和代码片段中提取函数名
3. **调用链查找**：根据调用图找到相关函数（被调用函数、调用者、调用链）
4. **第二轮检索**：基于函数名检索相关代码
5. **上下文构建**：合并两轮检索结果，添加调用关系信息

### 上下文增强

增强的上下文包含：
- 代码片段
- 文件路径
- 函数调用关系（如：`func_name(calls: func1, func2; called by: func3)`）

## 优势

1. **更完整的上下文**：不仅包含语义相似的代码，还包含调用相关的代码
2. **函数调用追踪**：能够追踪函数间的调用关系
3. **向后兼容**：如果调用图不可用，自动回退到传统方法
4. **性能优化**：调用图缓存避免重复分析

## 示例

### 调用图分析

```python
from metis.rag.call_graph import CallGraphAnalyzer

analyzer = CallGraphAnalyzer()
code = """
def process_data(data):
    result = validate(data)
    return transform(result)

def validate(data):
    return data.strip()

def transform(data):
    return data.upper()
"""

call_graph = analyzer.build_call_graph(code, "python")
# 结果: {'process_data': {'validate', 'transform'}, 
#        'validate': set(), 'transform': set()}

# 查找调用链
chain = analyzer.find_call_chain('process_data', call_graph, depth=2)
# 结果: {'process_data', 'validate', 'transform'}
```

### 增强检索

```python
from metis.rag.enhanced_retriever import EnhancedRetriever

retriever = EnhancedRetriever(
    retriever_code=code_retriever,
    retriever_docs=docs_retriever,
    call_graph_cache=call_graph_cache,
)

result = retriever.retrieve_with_call_graph(
    query="process user input",
    snippet=current_code,
    similarity_top_k=5,
    enable_call_graph=True,
)

context = retriever.build_enhanced_context(
    code_docs=result["code_docs"],
    docs_docs=result["docs_docs"],
    snippet=current_code,
    include_call_info=True,
)
```

## 性能考虑

- **索引时间**：调用图分析会增加索引时间，但通常可以接受
- **检索时间**：多轮检索会增加检索时间，但提供更完整的上下文
- **内存使用**：调用图缓存会占用一些内存，但对于大多数项目来说可以接受

## 未来改进

- [ ] 支持更多语言的调用图分析
- [ ] 支持跨文件的调用关系追踪
- [ ] 支持类和方法调用关系
- [ ] 优化调用图构建性能
- [ ] 支持增量更新调用图

