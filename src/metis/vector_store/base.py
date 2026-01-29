# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod


class BaseVectorStore(ABC):
    @abstractmethod
    def init(self):
        """Initialize vector storage components (e.g., vector store and storage context)."""
        pass

    @abstractmethod
    def get_query_engines(self, llm_provider, similarity_top_k, response_mode):
        """Return tuple of LangChain-style retrievers (code, docs)."""
        pass

    @abstractmethod
    def get_storage_contexts(self):
        """Return tuple of storage contexts (code, docs) for indexing."""
        pass

    def _build_llm(self, llm_provider):
        """Construct a provider-specific LlamaIndex LLM instance."""
        llm_class = llm_provider.get_query_engine_class()
        llm_kwargs = llm_provider.get_query_model_kwargs() or {}
        filtered_kwargs = {k: v for k, v in llm_kwargs.items() if v is not None}
        return llm_class(**filtered_kwargs)


class _Doc:
    def __init__(
        self, text: str, metadata: dict | None = None, score: float | None = None
    ):
        self.page_content = text
        self.metadata = metadata or {}
        self.score = score


class QueryEngineRetriever:
    """
    Adapter that wraps a LlamaIndex QueryEngine and exposes a
    LangChain-style retriever interface: `get_relevant_documents`.
    """

    def __init__(self, query_engine):
        self._qe = query_engine

    def _extract_docs_from_nodes(self, nodes):
        docs = []
        if not nodes:
            return docs
        for item in nodes:
            node = getattr(item, "node", item)
            score = getattr(item, "score", None)
            if score is None:
                score = getattr(item, "similarity", None)
            metadata = getattr(node, "metadata", None)
            text = getattr(node, "text", None)
            if text is None:
                text = getattr(node, "get_content", None)
                if callable(text):
                    text = text()
            if text is None:
                text = str(node)
            docs.append(_Doc(str(text), metadata=dict(metadata or {}), score=score))
        return docs

    def _retrieve_nodes(self, query: str):
        retrieve = getattr(self._qe, "retrieve", None)
        if callable(retrieve):
            return retrieve(query)
        retriever = getattr(self._qe, "retriever", None)
        if retriever is not None:
            retrieve = getattr(retriever, "retrieve", None)
            if callable(retrieve):
                return retrieve(query)
        internal = getattr(self._qe, "_retriever", None)
        if internal is not None:
            retrieve = getattr(internal, "retrieve", None)
            if callable(retrieve):
                return retrieve(query)
        return None

    def _query_response(self, query: str):
        query_fn = getattr(self._qe, "query", None)
        if callable(query_fn):
            return query_fn(query)
        return None

    def get_relevant_documents(self, query: str):
        nodes = None
        try:
            nodes = self._retrieve_nodes(query)
        except Exception:
            nodes = None

        if nodes:
            docs = self._extract_docs_from_nodes(nodes)
            if docs:
                return docs

        try:
            res = self._query_response(query)
        except Exception:
            res = None

        source_nodes = getattr(res, "source_nodes", None) if res is not None else None
        docs = self._extract_docs_from_nodes(source_nodes)
        if docs:
            return docs

        response_text = getattr(res, "response", None) if res is not None else None
        if response_text is None and res is not None:
            response_text = str(res)
        if not response_text:
            return []
        return [_Doc(str(response_text), metadata={"kind": "query_response"})]
