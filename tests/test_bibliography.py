"""Tests for bibliography extraction."""
from briefkit.bibliography import extract_bibliography


class TestAuthorYearCitations:
    def test_author_et_al(self):
        text = "According to Thompson et al. (2023), the results show..."
        refs = extract_bibliography(text)
        assert any(r["authors"] == "Thompson et al." and r["year"] == "2023" for r in refs)

    def test_single_author(self):
        text = "As noted by Smith (2020), this approach works well."
        refs = extract_bibliography(text)
        assert any(r["authors"] == "Smith" and r["year"] == "2020" for r in refs)

    def test_two_authors(self):
        text = "Liu and Chen (2019) demonstrated that..."
        refs = extract_bibliography(text)
        assert any("Liu" in r["authors"] and r["year"] == "2019" for r in refs)

    def test_bracketed_citation(self):
        text = "This was shown in previous work [Smith 2021]."
        refs = extract_bibliography(text)
        assert any(r["authors"] == "Smith" and r["year"] == "2021" for r in refs)


class TestLegislationCitations:
    def test_australian_act(self):
        text = "The Privacy Act 1988 (Cth) requires..."
        refs = extract_bibliography(text)
        assert any("Privacy Act 1988" in r["title"] for r in refs)

    def test_generic_act(self):
        text = "Under the Data Protection Act 2018, organisations must..."
        refs = extract_bibliography(text)
        assert any("Data Protection Act 2018" in r["title"] for r in refs)


class TestRFCCitations:
    def test_rfc_reference(self):
        text = "As specified in RFC 7231, HTTP semantics..."
        refs = extract_bibliography(text)
        assert any("RFC 7231" in r["title"] for r in refs)


class TestCaseLawCitations:
    def test_case_citation(self):
        text = "In the case of Smith v Jones, the court held..."
        refs = extract_bibliography(text)
        assert any("Smith v Jones" in r["title"] for r in refs)


class TestDeduplication:
    def test_duplicate_citations_deduplicated(self):
        text = "Smith (2020) and later Smith (2020) confirmed..."
        refs = extract_bibliography(text)
        smith_refs = [r for r in refs if r["authors"] == "Smith" and r["year"] == "2020"]
        assert len(smith_refs) == 1


class TestEmptyInput:
    def test_no_citations(self):
        text = "This is plain text with no academic citations at all."
        refs = extract_bibliography(text)
        assert refs == []

    def test_empty_string(self):
        refs = extract_bibliography("")
        assert refs == []
