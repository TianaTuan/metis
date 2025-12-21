# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated, Literal, get_args, get_origin

from metis.engine.helpers import apply_custom_guidance
from .schemas import ReviewIssueModel

logger = logging.getLogger("metis")


def retrieve_text(retriever, query, min_score=None, max_docs=None):
    """
    Retrieve context using a retriever with get_relevant_documents.
    Enhanced with relevance filtering and result limiting.
    
    Args:
        retriever: The retriever instance
        query: Query string
        min_score: Minimum relevance score threshold (if retriever supports scoring)
        max_docs: Maximum number of documents to return (default: None, use retriever's top_k)
    
    Returns:
        Concatenated text from retrieved documents
    """
    try:
        docs = retriever.get_relevant_documents(query)
        if not docs:
            return ""
        
        # Filter by relevance score if available and min_score is set
        filtered_docs = []
        for doc in docs:
            # Check if document has a score attribute (some retrievers provide this)
            score = getattr(doc, 'score', None)
            if score is None:
                # Try to get score from metadata
                metadata = getattr(doc, 'metadata', {})
                score = metadata.get('score', None)
            
            # Filter by minimum score if specified and score is available
            if min_score is not None and score is not None:
                if score < min_score:
                    continue
            
            filtered_docs.append(doc)
            
            # Limit number of documents if specified
            if max_docs is not None and len(filtered_docs) >= max_docs:
                break
        
        # If no docs after filtering but we had docs originally, use original docs
        if not filtered_docs and docs:
            filtered_docs = docs[:max_docs] if max_docs else docs
        
        # Join document contents
        contents = []
        for doc in filtered_docs:
            content = getattr(doc, "page_content", str(doc))
            if content:
                contents.append(content)
        
        return "\n\n".join(contents)
    except Exception as e:
        logger.warning(f"Error retrieving context: {e}")
        return ""


def synthesize_context(code_text, doc_text):
    """
    Compose the retrieval context used in prompts.
    Only includes retrieved code/docs text, not the retrieval question itself.
    """
    parts = []
    if code_text:
        parts.append(code_text)
    if doc_text:
        parts.append(doc_text)
    return "\n\n".join(p for p in parts if p)


def _is_string_field(annotation):
    if annotation is str:
        return True
    if isinstance(annotation, type) and issubclass(annotation, str):
        return True
    origin = get_origin(annotation)
    if origin is None:
        return False
    if origin is str:
        return True
    if origin is Literal:
        return all(isinstance(arg, str) for arg in get_args(annotation))
    if origin is Annotated:
        base, *_ = get_args(annotation)
        return _is_string_field(base)
    return False


_REQUIRED_REVIEW_STR_FIELDS = tuple(
    name
    for name, field in ReviewIssueModel.model_fields.items()
    if _is_string_field(field.annotation)
)


def sanitize_review_payload(payload):
    """
    Normalize review entries so that required keys always exist.
    Missing string fields become empty strings and confidence defaults to 0.0.
    """
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):
        return []

    sanitized: list[dict] = []
    for idx, review in enumerate(reviews):
        if not isinstance(review, dict):
            logger.debug(
                "Structured review entry %s is not a dict; normalizing to empty fields",
                idx,
            )
            empty_entry = {field: "" for field in _REQUIRED_REVIEW_STR_FIELDS}
            empty_entry["confidence"] = 0.0
            empty_entry["issue"] = str(review)
            sanitized.append(empty_entry)
            continue

        normalized = dict(review)
        for field in _REQUIRED_REVIEW_STR_FIELDS:
            value = normalized.get(field)
            if isinstance(value, str):
                normalized[field] = value.strip()
            elif value is None:
                normalized[field] = ""
            else:
                normalized[field] = str(value).strip()

        confidence_raw = normalized.get("confidence")
        confidence_value = None
        if isinstance(confidence_raw, (int, float)):
            confidence_value = float(confidence_raw)
        elif isinstance(confidence_raw, str):
            try:
                confidence_value = float(confidence_raw.strip())
            except ValueError:
                confidence_value = None
        normalized["confidence"] = (
            confidence_value if confidence_value is not None else 0.0
        )

        # Ensure required keys exist even if review provided none of them
        for field in _REQUIRED_REVIEW_STR_FIELDS:
            if field not in normalized or normalized[field] is None:
                normalized[field] = ""

        sanitized.append(normalized)

    return sanitized


def build_review_system_prompt(
    language_prompts,
    default_prompt_key,
    report_prompt,
    custom_prompt_text,
    custom_guidance_precedence,
    schema_prompt_section,
):
    """Compose the system prompt for a review in a single place."""
    base = (
        f"{language_prompts[default_prompt_key]} \n "
        f"{language_prompts['security_review_checks']} \n {report_prompt}"
    )
    placeholder = "[[REVIEW_SCHEMA_FIELDS]]"

    # Fail early here since REVIEW_SCHEMA_FIELDS are required for having a structured output
    if placeholder not in base:
        raise ValueError(
            "Schema prompt placeholder missing from review prompt template"
        )

    base = base.replace(placeholder, schema_prompt_section)
    return apply_custom_guidance(
        base, custom_prompt_text, custom_guidance_precedence or ""
    )
