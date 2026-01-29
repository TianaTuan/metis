# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
调用图分析器
提取代码中的函数定义和调用关系
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path

logger = logging.getLogger("metis.rag")


class CallGraphAnalyzer:
    """
    分析代码中的函数调用关系
    支持多种语言的函数定义和调用提取
    """

    def __init__(self):
        self.function_patterns = {
            "python": [
                (r"def\s+(\w+)\s*\(", r"\b(\w+)\s*\("),  # def func(, func(
                (r"class\s+(\w+)", r"\b(\w+)\s*\("),  # class Class, Class(
            ],
            "javascript": [
                (r"function\s+(\w+)\s*\(", r"\b(\w+)\s*\("),
                (r"const\s+(\w+)\s*=\s*(?:async\s+)?\(?", r"\b(\w+)\s*\("),
                (r"(\w+)\s*:\s*(?:async\s+)?\(?", r"\b(\w+)\s*\("),
            ],
            "typescript": [
                (r"function\s+(\w+)\s*\(", r"\b(\w+)\s*\("),
                (r"const\s+(\w+)\s*[:=]\s*(?:async\s+)?\(?", r"\b(\w+)\s*\("),
                (r"(\w+)\s*[:=]\s*(?:async\s+)?\(?", r"\b(\w+)\s*\("),
            ],
            "c": [
                (r"(\w+)\s+(\w+)\s*\(", r"\b(\w+)\s*\("),  # type func(, func(
            ],
            "cpp": [
                (r"(\w+)\s+(\w+)\s*\(", r"\b(\w+)\s*\("),
                (r"(\w+)::(\w+)\s*\(", r"\b(\w+)::(\w+)\s*\("),
            ],
            "go": [
                (r"func\s+(\w+)\s*\(", r"\b(\w+)\s*\("),
                (r"func\s+\([^)]+\)\s+(\w+)\s*\(", r"\b(\w+)\s*\("),
            ],
            "rust": [
                (r"fn\s+(\w+)\s*\(", r"\b(\w+)\s*\("),
            ],
        }

    def extract_functions(self, code: str, language: str = "python") -> Dict[str, List[Tuple[int, str]]]:
        """
        提取代码中的函数定义
        
        Returns:
            {function_name: [(line_number, function_signature)]}
        """
        functions = {}
        patterns = self.function_patterns.get(language, self.function_patterns["python"])
        
        lines = code.split("\n")
        for line_num, line in enumerate(lines, 1):
            for def_pattern, _ in patterns:
                match = re.search(def_pattern, line)
                if match:
                    # 提取函数名：优先使用最后一个非空组
                    groups = match.groups()
                    func_name = None
                    for group in reversed(groups):
                        if group:
                            func_name = group
                            break
                    if func_name:
                        if func_name not in functions:
                            functions[func_name] = []
                        functions[func_name].append((line_num, line.strip()))
        
        return functions

    def extract_calls(self, code: str, language: str = "python") -> Dict[str, Set[Tuple[int, str]]]:
        """
        提取代码中的函数调用
        
        Returns:
            {function_name: {(line_number, call_context)}}
        """
        calls = {}
        patterns = self.function_patterns.get(language, self.function_patterns["python"])
        
        lines = code.split("\n")
        defined_functions = set()
        
        # 先提取所有定义的函数
        for line in lines:
            for def_pattern, _ in patterns:
                match = re.search(def_pattern, line)
                if match:
                    # 提取函数名：优先使用最后一个非空组
                    groups = match.groups()
                    func_name = None
                    for group in reversed(groups):
                        if group:
                            func_name = group
                            break
                    if func_name:
                        defined_functions.add(func_name)
        
        # 提取函数调用
        for line_num, line in enumerate(lines, 1):
            for _, call_pattern in patterns:
                matches = re.finditer(call_pattern, line)
                for match in matches:
                    # 提取函数名：优先使用第一个组（通常是函数名）
                    groups = match.groups()
                    func_name = groups[0] if groups and groups[0] else None
                    if func_name and func_name in defined_functions:
                        if func_name not in calls:
                            calls[func_name] = set()
                        calls[func_name].add((line_num, line.strip()))
        
        return calls

    def build_call_graph(self, code: str, language: str = "python") -> Dict[str, Set[str]]:
        """
        构建调用图
        
        Returns:
            {function_name: {called_functions}}
        """
        functions = self.extract_functions(code, language)
        calls = self.extract_calls(code, language)
        
        call_graph = {}
        
        # 为每个定义的函数初始化调用关系
        for func_name in functions.keys():
            call_graph[func_name] = set()
        
        # 分析每个函数内部的调用
        lines = code.split("\n")
        current_function = None
        function_start = {}
        
        # 确定每个函数的起始行
        for func_name, positions in functions.items():
            for line_num, _ in positions:
                if func_name not in function_start or line_num < function_start[func_name]:
                    function_start[func_name] = line_num
        
        # 按行号排序函数
        sorted_functions = sorted(function_start.items(), key=lambda x: x[1])
        
        # 分析调用关系
        for i, (func_name, start_line) in enumerate(sorted_functions):
            end_line = sorted_functions[i + 1][1] if i + 1 < len(sorted_functions) else len(lines)
            
            # 提取这个函数内部的调用
            func_code = "\n".join(lines[start_line - 1 : end_line - 1])
            func_calls = self.extract_calls(func_code, language)
            
            for called_func in func_calls.keys():
                if called_func in call_graph:
                    call_graph[func_name].add(called_func)
        
        return call_graph

    def find_callees(self, function_name: str, call_graph: Dict[str, Set[str]]) -> Set[str]:
        """
        找到函数调用的所有被调用函数（直接调用）
        """
        return call_graph.get(function_name, set())

    def find_callers(self, function_name: str, call_graph: Dict[str, Set[str]]) -> Set[str]:
        """
        找到所有调用指定函数的函数（直接调用者）
        """
        callers = set()
        for caller, callees in call_graph.items():
            if function_name in callees:
                callers.add(caller)
        return callers

    def find_call_chain(self, function_name: str, call_graph: Dict[str, Set[str]], depth: int = 2) -> Set[str]:
        """
        找到函数的调用链（递归查找，包含被调用函数和调用者）
        
        Args:
            function_name: 起始函数名
            call_graph: 调用图
            depth: 递归深度
        
        Returns:
            调用链中的所有函数名
        """
        chain = {function_name}
        
        def _traverse(func: str, current_depth: int):
            if current_depth >= depth:
                return
            
            # 查找被调用的函数
            callees = call_graph.get(func, set())
            for callee in callees:
                if callee not in chain:
                    chain.add(callee)
                    _traverse(callee, current_depth + 1)
            
            # 查找调用者
            callers = self.find_callers(func, call_graph)
            for caller in callers:
                if caller not in chain:
                    chain.add(caller)
                    _traverse(caller, current_depth + 1)
        
        _traverse(function_name, 0)
        return chain


def analyze_code_file(file_path: str, code: str, language: str = "python") -> Dict:
    """
    分析代码文件，提取调用图信息
    
    Returns:
        包含函数定义、调用关系和调用图的字典
    """
    analyzer = CallGraphAnalyzer()
    
    try:
        functions = analyzer.extract_functions(code, language)
        calls = analyzer.extract_calls(code, language)
        call_graph = analyzer.build_call_graph(code, language)
        
        return {
            "file_path": file_path,
            "functions": functions,
            "calls": {k: list(v) for k, v in calls.items()},
            "call_graph": {k: list(v) for k, v in call_graph.items()},
        }
    except Exception as e:
        logger.warning(f"Failed to analyze call graph for {file_path}: {e}")
        return {
            "file_path": file_path,
            "functions": {},
            "calls": {},
            "call_graph": {},
        }

