# Metis MCP 架构说明

## 概述

Metis 已改造为支持 MCP (Model Context Protocol) 架构，将核心功能模块化为独立的 Skills/Tools，通过 JSON-RPC 2.0 协议提供服务。

## 架构设计

### 核心组件

1. **MCP Server** (`src/metis/mcp/server.py`)
   - 实现 JSON-RPC 2.0 协议
   - 管理 Skills 的注册和调用
   - 支持 stdio 传输方式

2. **Skills** (`src/metis/mcp/skills/`)
   - `BaseSkill`: Skill 基类，定义标准接口
   - `HTMLGeneratorSkill`: HTML 报告生成 Skill

### HTML 生成 Skill

HTML 生成功能已封装为独立的 MCP Skill (`HTMLGeneratorSkill`)，具有以下特点：

- **独立封装**: 将 HTML 生成逻辑从 CLI 中分离
- **标准化接口**: 通过 `BaseSkill` 定义统一的调用接口
- **向后兼容**: CLI 代码会自动检测并使用 MCP Skill，如果不可用则回退到传统方法

## 使用方法

### 1. 作为 MCP Server 运行

```bash
# 方式 1: 使用入口点
metis-mcp

# 方式 2: 使用 Python 模块
python -m metis.mcp
```

### 2. 在 CLI 中使用

CLI 会自动使用 MCP Skill 生成 HTML 报告（如果可用）：

```bash
metis report --output-file report.html
```

### 3. 通过 JSON-RPC 调用

MCP Server 接受 JSON-RPC 2.0 格式的请求：

#### 初始化

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

#### 列出所有 Tools

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

#### 调用 HTML 生成 Tool

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "generate_html_report",
    "arguments": {
      "report_data": {
        "reviews": [...]
      },
      "output_path": "reports/report.html"
    }
  }
}
```

## 扩展 Skills

要添加新的 Skill，只需：

1. 继承 `BaseSkill` 类
2. 实现必要的方法：
   - `get_name()`: 返回 Skill 名称
   - `get_description()`: 返回 Skill 描述
   - `get_schema()`: 返回 JSON Schema 定义
   - `execute()`: 实现核心逻辑

3. 在 `MetisMCPServer._register_default_skills()` 中注册

示例：

```python
from metis.mcp.skills.base import BaseSkill

class MyCustomSkill(BaseSkill):
    def get_name(self) -> str:
        return "my_custom_skill"
    
    def get_description(self) -> str:
        return "我的自定义 Skill"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        # 实现逻辑
        return {"success": True, "result": "..."}
```

## 优势

1. **模块化**: 功能独立封装，易于维护和测试
2. **可扩展**: 通过注册机制轻松添加新功能
3. **标准化**: 使用 JSON-RPC 2.0 标准协议
4. **向后兼容**: 不影响现有 CLI 功能
5. **可集成**: 可以与其他 MCP 客户端集成

## 未来计划

- [ ] 添加更多核心功能的 Skills (index, review, ask)
- [ ] 支持 HTTP with SSE 传输方式
- [ ] 添加资源管理功能
- [ ] 支持提示词模板管理

