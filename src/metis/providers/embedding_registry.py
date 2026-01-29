# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from importlib import import_module
from typing import Dict, Type

from metis.providers.embedding_base import EmbeddingProvider

_EMBEDDING_PROVIDERS: Dict[str, Type[EmbeddingProvider]] = {}
_EMBEDDING_LOADERS: Dict[str, str] = {}


def register_embedding_provider(
    name: str, provider_cls: Type[EmbeddingProvider]
) -> None:
    """Register an embedding provider under a case-insensitive name."""
    key = name.lower()
    _EMBEDDING_PROVIDERS[key] = provider_cls


def register_embedding_provider_loader(name: str, dotted_path: str) -> None:
    """
    Register a deferred loader for an embedding provider. The dotted path should be
    formatted as ``"module.submodule:ClassName"``.
    """
    key = name.lower()
    _EMBEDDING_LOADERS[key] = dotted_path


def _load_embedding_provider_from_path(
    name: str, dotted_path: str
) -> Type[EmbeddingProvider]:
    module_path, class_name = dotted_path.split(":", 1)
    module = import_module(module_path)

    # Provider modules can self-register on import.
    key = name.lower()
    if key in _EMBEDDING_PROVIDERS:
        return _EMBEDDING_PROVIDERS[key]

    provider_cls = getattr(module, class_name)
    register_embedding_provider(name, provider_cls)
    return provider_cls


def get_embedding_provider(name: str) -> Type[EmbeddingProvider]:
    """Fetch a previously registered embedding provider class."""
    key = name.lower()
    if key in _EMBEDDING_PROVIDERS:
        return _EMBEDDING_PROVIDERS[key]

    dotted_path = _EMBEDDING_LOADERS.get(key)
    if dotted_path:
        try:
            return _load_embedding_provider_from_path(name, dotted_path)
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                f"Embedding provider '{name}' is registered but required dependencies are missing."
            ) from exc

    raise ValueError(f"Unsupported embedding provider: {name}")


def registered_embedding_providers() -> Dict[str, Type[EmbeddingProvider]]:
    """Return a copy of the embedding provider registry."""
    return dict(_EMBEDDING_PROVIDERS)


# Built-in embedding provider loaders (lazy import until requested)
# 默认使用 OpenAI 兼容的 embedding provider
register_embedding_provider_loader(
    "openai", "metis.providers.embedding_openai:OpenAIEmbeddingProvider"
)
register_embedding_provider_loader(
    "openai_compatible",
    "metis.providers.embedding_openai:OpenAICompatibleEmbeddingProvider",
)

