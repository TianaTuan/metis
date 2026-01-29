# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
增强的 RAG 检索器
支持多轮检索和函数调用链追踪
"""

import logging
import re
from typing import List, Dict, Set, Any, Optional
from collections import defaultdict

from metis.rag.call_graph import CallGraphAnalyzer, analyze_code_file
from metis.engine.graphs.utils import retrieve_documents

logger = logging.getLogger("metis.rag")


class EnhancedRetriever:
    """
    增强的检索器，支持：
    1. 多轮检索（语义检索 + 调用链检索）
    2. 函数调用关系追踪
    3. 增强的上下文构建
    """

    def __init__(self, retriever_code, retriever_docs, call_graph_cache: Optional[Dict] = None):
        """
        初始化增强检索器
        
        Args:
            retriever_code: 代码检索器
            retriever_docs: 文档检索器
            call_graph_cache: 调用图缓存 {file_path: call_graph_data}
        """
        self.retriever_code = retriever_code
        self.retriever_docs = retriever_docs
        self.call_graph_cache = call_graph_cache or {}
        self.analyzer = CallGraphAnalyzer()

    def _extract_function_names_from_query(self, query: str, snippet: str = "", language: str = "python") -> Set[str]:
        """从查询和代码片段中提取可能的函数名"""
        function_names = set()
        
        # 从代码片段中提取函数定义
        if snippet:
            try:
                # 尝试指定语言，如果失败则尝试其他语言
                try:
                    functions = self.analyzer.extract_functions(snippet, language)
                    if functions:
                        function_names.update(functions.keys())
                except Exception:
                    # 回退：尝试多种语言
                    for lang in ["python", "javascript", "typescript", "c", "cpp", "go", "rust"]:
                        try:
                            functions = self.analyzer.extract_functions(snippet, lang)
                            if functions:
                                function_names.update(functions.keys())
                                break  # 找到就停止
                        except Exception:
                            continue
            except Exception:
                pass
        
        # 从查询中提取可能的函数名（简单的启发式方法）
        # 查找 "function X" 或 "X()" 模式
        patterns = [
            r"function\s+(\w+)",
            r"(\w+)\s*\(",
            r"def\s+(\w+)",
            r"fn\s+(\w+)",
        ]
        for pattern in patterns:
            try:
                matches = re.findall(pattern, query, re.IGNORECASE)
                # 处理元组结果
                for match in matches:
                    if isinstance(match, tuple):
                        function_names.update(m for m in match if m)
                    else:
                        function_names.add(match)
            except Exception:
                continue
        
        return function_names

    def _find_related_functions(
        self, function_names: Set[str], call_graph_cache: Dict
    ) -> Set[str]:
        """根据调用图找到相关函数"""
        related = set(function_names)
        
        for file_data in call_graph_cache.values():
            call_graph = {
                k: set(v) for k, v in file_data.get("call_graph", {}).items()
            }
            
            for func_name in function_names:
                # 查找被调用的函数
                callees = self.analyzer.find_callees(func_name, call_graph)
                related.update(callees)
                
                # 查找调用者
                callers = self.analyzer.find_callers(func_name, call_graph)
                related.update(callers)
                
                # 查找调用链
                chain = self.analyzer.find_call_chain(func_name, call_graph, depth=2)
                related.update(chain)
        
        return related

    def _build_function_query(self, function_names: Set[str]) -> str:
        """构建基于函数名的查询"""
        if not function_names:
            return ""
        
        queries = []
        for func_name in list(function_names)[:5]:  # 限制数量
            queries.append(f"function {func_name}")
            queries.append(f"{func_name}(")
        
        return " OR ".join(queries)

    def retrieve_with_call_graph(
        self,
        query: str,
        snippet: str = "",
        similarity_top_k: int = 5,
        min_retrieval_score: Optional[float] = None,
        enable_call_graph: bool = True,
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        增强的检索，包含调用链信息
        
        Args:
            query: 原始查询
            snippet: 当前代码片段
            similarity_top_k: 每轮检索返回的最大文档数
            min_retrieval_score: 最小相关性分数
            enable_call_graph: 是否启用调用图增强
            language: 代码语言（用于函数提取）
        
        Returns:
            包含检索结果的字典
        """
        # 第一轮：基于语义相似度的检索
        code_docs_round1 = retrieve_documents(
            self.retriever_code,
            query,
            min_score=min_retrieval_score,
            max_docs=similarity_top_k,
        )
        docs_docs_round1 = retrieve_documents(
            self.retriever_docs,
            query,
            min_score=min_retrieval_score,
            max_docs=similarity_top_k,
        )
        
        all_code_docs = list(code_docs_round1)
        all_docs_docs = list(docs_docs_round1)
        
        # 第二轮：基于调用图的检索（如果启用）
        if enable_call_graph and self.call_graph_cache:
            try:
                # 提取函数名
                function_names = self._extract_function_names_from_query(query, snippet, language)
                
                if function_names:
                    # 查找相关函数
                    related_functions = self._find_related_functions(
                        function_names, self.call_graph_cache
                    )
                    
                    if related_functions:
                        # 构建函数查询
                        function_query = self._build_function_query(related_functions)
                        
                        if function_query:
                            # 检索相关函数的代码
                            code_docs_round2 = retrieve_documents(
                                self.retriever_code,
                                function_query,
                                min_score=min_retrieval_score,
                                max_docs=similarity_top_k // 2,  # 第二轮检索较少文档
                            )
                            
                            # 合并结果，去重
                            seen_content = {
                                getattr(doc, "page_content", "") for doc in all_code_docs
                            }
                            for doc in code_docs_round2:
                                content = getattr(doc, "page_content", "")
                                if content and content not in seen_content:
                                    all_code_docs.append(doc)
                                    seen_content.add(content)
                            
                            logger.debug(
                                f"Call graph retrieval found {len(code_docs_round2)} additional documents"
                            )
            except Exception as e:
                logger.warning(f"Call graph retrieval failed: {e}")
        
        # 限制最终结果数量
        all_code_docs = all_code_docs[:similarity_top_k * 2]  # 允许更多上下文
        all_docs_docs = all_docs_docs[:similarity_top_k]
        
        return {
            "code_docs": all_code_docs,
            "docs_docs": all_docs_docs,
            "round1_code_count": len(code_docs_round1),
            "round1_docs_count": len(docs_docs_round1),
            "total_code_count": len(all_code_docs),
            "total_docs_count": len(all_docs_docs),
        }

    def build_enhanced_context(
        self,
        code_docs: List,
        docs_docs: List,
        snippet: str = "",
        include_call_info: bool = True,
    ) -> str:
        """
        构建增强的上下文，包含调用关系信息
        
        Args:
            code_docs: 检索到的代码文档
            docs_docs: 检索到的文档
            snippet: 当前代码片段
            include_call_info: 是否包含调用关系信息
        
        Returns:
            增强的上下文字符串
        """
        parts = []
        
        # 添加代码上下文
        if code_docs:
            code_parts = []
            for doc in code_docs:
                content = getattr(doc, "page_content", "") or ""
                metadata = getattr(doc, "metadata", {}) or {}
                
                if content:
                    # 尝试提取文件路径
                    file_path = (
                        metadata.get("file_path")
                        or metadata.get("file_name")
                        or metadata.get("source")
                        or "unknown"
                    )
                    
                    # 如果启用调用图，尝试添加调用关系信息
                    if include_call_info and self.call_graph_cache:
                        file_data = self.call_graph_cache.get(file_path, {})
                        call_graph = file_data.get("call_graph", {})
                        
                        # 提取当前文档中的函数
                        functions = self.analyzer.extract_functions(content)
                        if functions:
                            func_info = []
                            for func_name in functions.keys():
                                callees = self.analyzer.find_callees(
                                    func_name, {k: set(v) for k, v in call_graph.items()}
                                )
                                callers = self.analyzer.find_callers(
                                    func_name, {k: set(v) for k, v in call_graph.items()}
                                )
                                
                                if callees or callers:
                                    info_parts = []
                                    if callees:
                                        info_parts.append(f"calls: {', '.join(list(callees)[:3])}")
                                    if callers:
                                        info_parts.append(f"called by: {', '.join(list(callers)[:3])}")
                                    if info_parts:
                                        func_info.append(f"{func_name}({'; '.join(info_parts)})")
                            
                            if func_info:
                                code_parts.append(
                                    f"// File: {file_path}\n"
                                    f"// Call relationships: {', '.join(func_info)}\n"
                                    f"{content}"
                                )
                                continue
                    
                    code_parts.append(f"// File: {file_path}\n{content}")
            
            if code_parts:
                parts.append("=== CODE CONTEXT ===\n" + "\n\n".join(code_parts))
        
        # 添加文档上下文
        if docs_docs:
            docs_parts = []
            for doc in docs_docs:
                content = getattr(doc, "page_content", "") or ""
                if content:
                    docs_parts.append(content)
            
            if docs_parts:
                parts.append("=== DOCUMENTATION CONTEXT ===\n" + "\n\n".join(docs_parts))
        
        return "\n\n".join(parts)

