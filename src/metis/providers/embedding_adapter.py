# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

"""
适配器：将 LLMProvider 适配为 EmbeddingProvider，用于向后兼容。
当没有配置独立的 embedding_provider 时，可以使用 LLMProvider 的 embedding 功能。
"""

from metis.providers.embedding_base import EmbeddingProvider
from metis.providers.base import LLMProvider


class LLMProviderEmbeddingAdapter(EmbeddingProvider):
    """
    将 LLMProvider 适配为 EmbeddingProvider 的适配器类。
    这样可以在不修改现有代码的情况下，将 LLMProvider 用作 EmbeddingProvider。
    """

    def __init__(self, llm_provider: LLMProvider):
        """
        初始化适配器。

        Args:
            llm_provider: 实现了 embedding 方法的 LLMProvider 实例
        """
        self.llm_provider = llm_provider

    def get_embed_model_code(self):
        """委托给 LLMProvider 的 get_embed_model_code 方法。"""
        return self.llm_provider.get_embed_model_code()

    def get_embed_model_docs(self):
        """委托给 LLMProvider 的 get_embed_model_docs 方法。"""
        return self.llm_provider.get_embed_model_docs()
