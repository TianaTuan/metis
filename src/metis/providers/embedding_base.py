# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    独立的 Embedding Provider 基类，用于将 embedding 功能从 LLM Provider 中分离出来。
    这样可以让 embedding 和 chat 使用不同的模型。
    """

    @abstractmethod
    def get_embed_model_code(self):
        """返回用于代码的 embedding 模型实例。"""
        pass

    @abstractmethod
    def get_embed_model_docs(self):
        """返回用于文档的 embedding 模型实例。"""
        pass

