# 侵入式修改指南

如果你想直接修改 Metis 的源码来添加自定义规则，有以下几种方式：

## 方法 1: 修改 `plugins.yaml` 文件（推荐）

### 方式 A: 修改源码中的 `plugins.yaml`

直接修改 `src/metis/plugins/plugins.yaml` 文件，添加你的自定义规则。

**优点**：
- 永久生效，不需要每次指定
- 可以修改所有语言的规则

**缺点**：
- 修改了源码，更新 Metis 时需要重新应用修改

### 示例：为 C 语言添加自定义规则

编辑 `src/metis/plugins/plugins.yaml`，找到 `c:` 部分，修改 `security_review_checks`：

```yaml
c:
  supported_extensions: [".c", ".h", ".cc"]
  splitting: &c_cpp_splitting
    chunk_lines: 40
    chunk_lines_overlap: 15
    max_chars: 1500
  prompts: &c_cpp_prompts
    security_review_checks: |-
      2. What to Check
         - Look for potential security issues such as:
           - Memory safety issues
           - Memory aliasing issues
           - Buffer overflows
           - Unsafe function usage
           # ========== 你的自定义规则 ==========
           - 自定义规则 1: 检查所有动态内存分配是否有对应的释放
             + 特别注意在错误路径上是否释放了内存
             + 检查循环中的内存分配是否在循环外释放
           - 自定义规则 2: 验证所有数组访问是否在边界内
             + 检查数组索引是否可能为负数
             + 检查数组索引是否可能超出数组大小
           - 自定义规则 3: 检查所有指针解引用前是否进行了空指针检查
             + 特别注意函数返回值可能为 NULL 的情况
           - 自定义规则 4: 检查所有文件操作是否检查了返回值
             + fopen, fread, fwrite 等函数必须检查返回值
           - 自定义规则 5: 检查所有网络操作是否设置了超时
             + socket 操作必须设置超时，防止无限等待
           # ====================================
           - Integer overflows
           - Integer underflows
           - Injection vulnerabilities
           - Concurrency issues
           - Use of insecure functions
           - Null pointer dereference
           - Use after free
           - Pay extra attention to variables that are externally controlled.
           - Do not report on issues that do not affect security.
```

### 方式 B: 在当前工作目录创建 `plugins.yaml`（覆盖默认配置）

根据 `config_path_fallback` 函数的逻辑，你可以在**当前工作目录**创建 `plugins.yaml` 文件来覆盖默认配置。

**优点**：
- 不修改源码
- 可以针对特定项目使用不同的规则

**缺点**：
- 需要在运行 Metis 的目录下创建文件
- 每次运行都要确保文件存在

**步骤**：

1. 在运行 Metis 的目录创建 `plugins.yaml`（或复制 `src/metis/plugins/plugins.yaml`）
2. 修改其中的规则
3. 运行 Metis，它会优先使用当前目录的 `plugins.yaml`

```bash
# 1. 复制默认配置
cp src/metis/plugins/plugins.yaml ./plugins.yaml

# 2. 编辑 plugins.yaml，添加你的自定义规则

# 3. 运行 Metis（会自动使用当前目录的 plugins.yaml）
uv run metis --codebase-path ./target
```

## 方法 2: 修改 `general_prompts`（全局规则）

如果你想添加适用于所有语言的全局规则，可以修改 `general_prompts` 部分：

```yaml
general_prompts:
  custom_guidance_precedence: |-
    Instruction precedence: When 'Custom Guidance' conflicts with any default
    instructions or checks below, follow 'Custom Guidance'. If guidance excludes
    certain issue classes, omit them from analysis and do not report them unless
    directly necessary to explain another issue.
  
  # 添加全局安全检查规则
  global_security_checks: |-
    全局安全检查规则（适用于所有语言）：
    - 所有用户输入必须经过验证
    - 所有敏感操作必须记录日志
    - 所有错误消息不能泄露系统信息
    - 所有密码和密钥不能硬编码
  
  retrieve_context: |-
    You are a senior software engineer and your task is to explain what the following FILE does and what its purpose is.
    Include any data flows, function calls, or dependencies that could impact security.
    Make sure you flag any function input that is externally controlled.
    FILE: {file_path}
```

**注意**：如果添加了新的 `general_prompts` 字段，需要修改代码来使用它。否则只修改现有字段即可。

## 方法 3: 修改提示词模板（高级）

你可以修改 `security_review_file`、`security_review`、`validation_review` 等提示词模板：

```yaml
c:
  prompts:
    security_review_file: |-
      You are a thorough security engineer specializing in C/C++.
      
      # 添加你的自定义指导
      SPECIAL INSTRUCTIONS:
      - Focus on memory safety issues specific to embedded systems
      - Pay extra attention to interrupt handlers and their memory access patterns
      - Check for potential issues with DMA operations
      
      Always tie your identified issues directly to the evidence in FILE and RELEVANT_CONTEXT.
      ...
```

## 方法 4: 创建自定义插件（最灵活）

如果你想完全控制某个语言的审查逻辑，可以创建自定义插件：

1. 创建新的插件类（继承 `BaseLanguagePlugin`）
2. 在 `pyproject.toml` 中注册插件
3. 实现自定义的提示词逻辑

**示例**：

```python
# src/metis/plugins/my_custom_c_plugin.py
from metis.plugins.base import BaseLanguagePlugin

class MyCustomCPlugin(BaseLanguagePlugin):
    def get_supported_extensions(self):
        return [".c", ".h"]
    
    def get_prompts(self):
        # 返回自定义的提示词
        return {
            "security_review_checks": """
            你的自定义规则...
            """
        }
```

然后在 `pyproject.toml` 中注册：

```toml
[project.entry-points."metis.plugins"]
c = "metis.plugins.my_custom_c_plugin:MyCustomCPlugin"
```

## 推荐方案

1. **快速测试**：使用方式 B（在当前目录创建 `plugins.yaml`）
2. **长期使用**：使用方式 A（修改源码中的 `plugins.yaml`）
3. **复杂需求**：使用方法 4（创建自定义插件）

## 验证修改是否生效

运行 Metis 后，检查日志输出：

```bash
uv run metis --codebase-path ./target --log-level INFO
```

你会看到类似这样的日志：
```
INFO:metis:Loading plugins.yaml from /path/to/plugins.yaml
```

这表明 Metis 正在使用你修改的配置文件。

