from core.response import validate_kb_citations


def test_citation_rejection_on_threshold_and_source():
    citations = [
        {
            "source_title": "WSAVA",
            "organization": "WSAVA",
            "publication_year": 2024,
            "section_reference": "1.1",
            "url": "",
            "similarity_score": 0.8,
        },
        {
            "source_title": "Unknown Blog",
            "organization": "Blog",
            "publication_year": 2024,
            "section_reference": "2.1",
            "url": "",
            "similarity_score": 0.9,
        },
        {
            "source_title": "WSAVA",
            "organization": "WSAVA",
            "publication_year": 2024,
            "section_reference": "3.1",
            "url": "",
            "similarity_score": 0.6,
        },
    ]
    validated = validate_kb_citations(citations, ["WSAVA"], min_similarity=0.75)
    assert len(validated) == 1
    assert validated[0].source_title == "WSAVA"
