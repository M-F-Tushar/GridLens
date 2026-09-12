"""Tests for rag/embeddings.py: determinism, normalization, similarity."""



from __future__ import annotations

from rag.embeddings import EMBEDDING_DIM, cosine_similarity, embed_text, tokenize


def test_embed_text_is_deterministic_across_calls():
    text = "Battery round-trip efficiency assumptions for GridLens."
    first = embed_text(text)
    second = embed_text(text)
    assert first == second


def test_embed_text_has_fixed_dimension():
    assert len(embed_text("short text")) == EMBEDDING_DIM
    assert len(embed_text("")) == EMBEDDING_DIM


def test_embed_text_is_l2_normalized_for_nonempty_text():
    vector = embed_text("solar generation forecast methodology")
    norm_squared = sum(v * v for v in vector)
    assert abs(norm_squared - 1.0) < 1e-9


def test_embed_text_empty_string_is_zero_vector():
    vector = embed_text("")
    assert all(v == 0.0 for v in vector)


def test_tokenize_lowercases_and_drops_stopwords():
    tokens = tokenize("The Battery Efficiency of the System")
    assert "the" not in tokens
    assert "of" not in tokens
    assert "battery" in tokens
    assert "efficiency" in tokens


def test_cosine_similarity_identical_vectors_is_one():
    vector = embed_text("carbon intensity of grid imports")
    assert abs(cosine_similarity(vector, vector) - 1.0) < 1e-9


def test_cosine_similarity_unrelated_topics_scores_lower_than_related():
    battery_text = embed_text("battery charge discharge state of charge efficiency")
    battery_text_2 = embed_text("battery discharge efficiency and state of charge")
    unrelated_text = embed_text("completely different unrelated topic about weather forecasting only")

    related_score = cosine_similarity(battery_text, battery_text_2)
    unrelated_score = cosine_similarity(battery_text, unrelated_text)
    assert related_score > unrelated_score


def test_cosine_similarity_rejects_mismatched_dimensions():
    import pytest

    with pytest.raises(ValueError):
        cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])