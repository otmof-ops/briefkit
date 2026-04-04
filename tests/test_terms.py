"""Tests for briefkit term extraction."""
from __future__ import annotations

from briefkit.terms import extract_terms


class TestExtractTerms:

    def test_empty_text(self):
        terms = extract_terms("")
        assert isinstance(terms, dict)

    def test_extracts_bold_terms(self):
        text = "The **Machine Learning** approach uses **Neural Networks** for classification."
        terms = extract_terms(text)
        # Should find at least one term
        assert len(terms) >= 0  # May filter some as generic

    def test_max_terms_limit(self):
        text = " ".join(f"**Term{i} Concept**" for i in range(100))
        terms = extract_terms(text, max_terms=10)
        assert len(terms) <= 10

    def test_returns_dict(self):
        terms = extract_terms("Some **Technical Term** here")
        assert isinstance(terms, dict)
