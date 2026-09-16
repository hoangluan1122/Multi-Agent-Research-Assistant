from types import SimpleNamespace

from app.agents.writing_agent import WritingAgent


def make_paper(paper_id, title, result):
    return SimpleNamespace(
        id=paper_id,
        title=title,
        authors=["Nguyen Van A"],
        year=2025,
        venue="Test Conference",
        abstract=f"Abstract for {title}",
        analysis=SimpleNamespace(
            method="Transformer encoder",
            dataset="Evaluation Dataset",
            metrics="F1-score",
            results=result,
            limitations="Small evaluation sample",
            summary="Structured paper analysis",
        ),
    )


def test_evidence_fallback_is_grounded_in_current_session_data():
    session = SimpleNamespace(
        topic="Vietnamese legal document retrieval",
        research_question="Which retrieval methods improve legal search?",
    )
    paper = make_paper("paper-1", "Dense Retrieval for Vietnamese Law", "Improved recall on legal queries")
    citation = SimpleNamespace(
        citation_key="[1]",
        citation_text="Nguyen, Dense Retrieval for Vietnamese Law, 2025.",
    )

    report = WritingAgent._build_evidence_grounded_report(
        session=session,
        papers=[paper],
        citations=[citation],
        citation_map={"paper-1": "[1]"},
        comparison_table="| Paper | Result |\n| --- | --- |\n| Dense Retrieval | Improved recall |",
        synthesized_summary="The selected evidence emphasizes dense retrieval.",
        retrieved_chunks=[{"text": "The model improves recall for Vietnamese legal queries.", "metadata": {"paper_title": paper.title, "page_number": 4}}],
        feedback=None,
    )

    assert "Vietnamese legal document retrieval" in report
    assert "Dense Retrieval for Vietnamese Law" in report
    assert "Improved recall on legal queries" in report
    assert "[1]" in report
    assert "Dấu vết chứng cứ" in report
    assert "smoking" not in report.casefold()


def test_evidence_fallback_changes_with_the_selected_papers():
    session = SimpleNamespace(topic="Medical image segmentation", research_question=None)
    paper = make_paper("paper-2", "U-Net for Retinal Images", "Higher Dice score")

    report = WritingAgent._build_evidence_grounded_report(
        session=session,
        papers=[paper],
        citations=[],
        citation_map={},
        comparison_table=None,
        synthesized_summary=None,
        retrieved_chunks=[],
        feedback=None,
    )

    assert "Medical image segmentation" in report
    assert "U-Net for Retinal Images" in report
    assert "Higher Dice score" in report
    assert "Vietnamese legal document retrieval" not in report

