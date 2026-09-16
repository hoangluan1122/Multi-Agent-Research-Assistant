from types import SimpleNamespace

from app.agents.reading_agent import ReadingAgent
from app.agents.summarization_agent import SummarizationAgent


def test_missing_reading_fields_are_explicit_not_generic_defaults():
    extracted = ReadingAgent._normalize_extraction({"method": "", "results": "Measured recall improved."})

    assert extracted["method"] == "Chưa trích xuất được dữ liệu."
    assert extracted["dataset"] == "Chưa trích xuất được dữ liệu."
    assert extracted["results"] == "Measured recall improved."
    assert "Standard Research Dataset" not in str(extracted)


def test_comparison_matrix_uses_missing_marker_instead_of_fixed_claims():
    paper = SimpleNamespace(
        title="Evidence-driven retrieval",
        year=2025,
        analysis=SimpleNamespace(method=None, dataset=None, results=None, limitations=None),
    )

    matrix = SummarizationAgent()._generate_markdown_table([paper])

    assert matrix.count("Chưa trích xuất được dữ liệu.") == 4
    assert "Deep Learning Baseline" not in matrix
    assert "Public Benchmarks" not in matrix
    assert "High Performance" not in matrix

