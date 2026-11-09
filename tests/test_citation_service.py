from src.citation_service import Citation, dedupe_citations


def test_dedupe_keeps_first_citation_for_each_source():
    items = [
        Citation("A", "https://example.test/a", "first"),
        Citation("A revised", "https://example.test/a", "duplicate URL"),
        Citation("B", "https://example.test/b", "second"),
    ]
    assert dedupe_citations(items) == [items[0], items[2]]
