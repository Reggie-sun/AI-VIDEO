"""Dependency-free lexical ranking and rank fusion primitives."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Mapping, Sequence


_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+|[\u3400-\u4dbf\u4e00-\u9fff]+")
_CJK_RE = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff]+$")
LEXICAL_RELEVANCE_SCALE = 0.2


@dataclass(frozen=True)
class LexicalMatch:
    """A BM25 match identified by the stable indexed chunk ID."""

    chunk_id: str
    score: float


def tokenize(text: str) -> list[str]:
    """Tokenize identifiers, words and Chinese text without external models."""
    tokens: list[str] = []
    for match in _TOKEN_RE.finditer(text.lower()):
        token = match.group(0)
        tokens.append(token)
        if _CJK_RE.fullmatch(token) and len(token) > 1:
            tokens.extend(
                token[index : index + 2] for index in range(len(token) - 1)
            )
    return tokens


def rank_bm25(
    query: str,
    documents: Mapping[str, str],
    limit: int,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[LexicalMatch]:
    """Rank matching documents with BM25, returning only positive matches."""
    if limit < 1 or not documents:
        return []
    query_terms = tuple(dict.fromkeys(tokenize(query)))
    if not query_terms:
        return []

    tokenized = {chunk_id: tokenize(text) for chunk_id, text in documents.items()}
    document_count = len(tokenized)
    average_length = (
        sum(len(tokens) for tokens in tokenized.values()) / document_count
    ) or 1.0
    document_frequency = {
        term: sum(term in tokens for tokens in tokenized.values())
        for term in query_terms
    }

    matches: list[LexicalMatch] = []
    for chunk_id, tokens in tokenized.items():
        frequencies = Counter(tokens)
        document_length = len(tokens)
        score = 0.0
        for term in query_terms:
            frequency = frequencies.get(term, 0)
            if frequency == 0:
                continue
            frequency_in_corpus = document_frequency[term]
            inverse_document_frequency = math.log(
                1.0
                + (document_count - frequency_in_corpus + 0.5)
                / (frequency_in_corpus + 0.5)
            )
            denominator = frequency + k1 * (
                1.0 - b + b * document_length / average_length
            )
            score += inverse_document_frequency * frequency * (k1 + 1.0) / denominator
        if score > 0:
            matches.append(LexicalMatch(chunk_id=chunk_id, score=score))

    matches.sort(key=lambda match: (-match.score, match.chunk_id))
    return matches[:limit]


def lexical_relevance_score(raw_bm25_score: float) -> float:
    """Map a raw BM25 score to a fixed bounded admission score."""
    return 1.0 - math.exp(
        -max(raw_bm25_score, 0.0) / LEXICAL_RELEVANCE_SCALE
    )


def reciprocal_rank_fusion(
    rankings: Sequence[tuple[Sequence[str], float]],
    *,
    rank_constant: int = 60,
) -> dict[str, float]:
    """Return normalized weighted RRF scores keyed by stable chunk ID."""
    if rank_constant < 1:
        raise ValueError("rank_constant must be positive")
    total_weight = sum(weight for _, weight in rankings if weight > 0)
    if total_weight <= 0:
        return {}

    scores: dict[str, float] = {}
    for ranking, weight in rankings:
        if weight <= 0:
            continue
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + weight / (
                rank_constant + rank
            )

    maximum = total_weight / (rank_constant + 1)
    return {
        chunk_id: min(score / maximum, 1.0)
        for chunk_id, score in scores.items()
    }
