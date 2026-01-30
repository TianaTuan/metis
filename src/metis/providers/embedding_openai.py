# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import Any, Dict

from llama_index.embeddings.openai import (
    OpenAIEmbedding,
    OpenAIEmbeddingModelType,
)

from metis.providers.embedding_base import EmbeddingProvider
from metis.providers.embedding_registry import register_embedding_provider

logger = logging.getLogger("metis.providers.embedding")

_ALLOWED_OPENAI_EMBED_MODELS = {member.value for member in OpenAIEmbeddingModelType}


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """
    独立的 OpenAI 兼容 Embedding Provider。
    只负责 embedding 功能，不包含 chat 功能。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 OpenAI 兼容的 Embedding Provider。

        Args:
            config: 配置字典，应包含：
                - code_embedding_model: 代码 embedding 模型名称
                - docs_embedding_model: 文档 embedding 模型名称
                - llm_api_key (可选): API 密钥
                - openai_api_base 或 base_url (可选): API 基础 URL
                - openai_default_headers 或 default_headers (可选): 默认请求头
                - code_embedding_extra_kwargs (可选): 代码 embedding 的额外参数
                - docs_embedding_extra_kwargs (可选): 文档 embedding 的额外参数
        """
        self.config = config
        self.api_key = config.get("llm_api_key") or config.get("api_key")
        self.base_url = (
            config.get("openai_api_base")
            or config.get("api_base")
            or config.get("base_url")
        )
        self.default_headers = (
            config.get("openai_default_headers") or config.get("default_headers") or {}
        )
        self.code_embedding_model = config.get("code_embedding_model")
        self.docs_embedding_model = config.get("docs_embedding_model")
        self.code_embedding_extra_kwargs = config.get("code_embedding_extra_kwargs", {})
        self.docs_embedding_extra_kwargs = config.get("docs_embedding_extra_kwargs", {})

    def get_embed_model_code(self):
        """返回代码 embedding 模型实例。"""
        return self._build_embedding_model(
            self.code_embedding_model,
            self.code_embedding_extra_kwargs,
            "code_embedding_model",
        )

    def get_embed_model_docs(self):
        """返回文档 embedding 模型实例。"""
        return self._build_embedding_model(
            self.docs_embedding_model,
            self.docs_embedding_extra_kwargs,
            "docs_embedding_model",
        )

    def _build_embedding_model(
        self,
        model_name: str | None,
        extra_kwargs: Dict[str, Any],
        config_key: str,
    ):
        """构建 embedding 模型实例。"""
        print("\n" + "="*50)
        print("!!! HIT THE PROVIDER !!!")
        print(f"Model: {model_name}")
        print("="*50 + "\n")
        if not model_name:
            raise ValueError(f"Missing '{config_key}' in configuration")

        params: Dict[str, Any] = {}
        params["model"] = (
            model_name
            if model_name in _ALLOWED_OPENAI_EMBED_MODELS
            else OpenAIEmbeddingModelType.TEXT_EMBED_ADA_002.value
        )
        if self.api_key:
            params["api_key"] = self.api_key
        if self.base_url:
            params["api_base"] = self.base_url
        if self.default_headers:
            params["default_headers"] = self.default_headers
        
        # 1. 确定最终要使用的安全 batch_size
        final_batch_size = 20
        user_batch_size = extra_kwargs.get("batch_size")
        
        if user_batch_size is not None:
            if user_batch_size > 25:
                logger.warning(f"batch_size {user_batch_size} 超过 API 限制 25，已自动调整为 20")
                final_batch_size = 20
            else:
                final_batch_size = user_batch_size
        
        # 2. 实例化对象
        # 注意：这里我们显式传入 batch_size
        embed = OpenAIEmbedding(
            model=model_name,
            batch_size=final_batch_size, 
            **extra_kwargs
        )
        
        # 3. 【最关键的一步】强制覆盖属性
        # 有些版本的 LlamaIndex 会从配置中覆盖这个值，手动赋值最稳妥
        embed.batch_size = final_batch_size

        # 4. 兼容性处理
        if model_name not in _ALLOWED_OPENAI_EMBED_MODELS:
            embed._query_engine = model_name
            embed._text_engine = model_name
            embed.model_name = model_name
            
        # 5. 打印确认（调试用，成功后可删除）
        print(f"--- 确认：当前 Embedding 批处理大小已设为: {embed.batch_size} ---")
        print(f"\n🚀 DEBUG: 正在运行修改后的代码！当前 batch_size 是: {embed.batch_size}\n")
        return embed


class OpenAIEmbeddingProvider(OpenAICompatibleEmbeddingProvider):
    """
    OpenAI 官方的 Embedding Provider。
    继承自 OpenAICompatibleEmbeddingProvider，但要求必须设置 OPENAI_API_KEY。
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI embedding provider but not set."
            )


# 注册 embedding providers
register_embedding_provider("openai", OpenAIEmbeddingProvider)
register_embedding_provider("openai_compatible", OpenAICompatibleEmbeddingProvider)
