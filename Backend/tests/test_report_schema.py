from datetime import datetime

from app.schemas.report import ReviewResponse


def test_review_response_accepts_legacy_string_risks():
    review = ReviewResponse.model_validate(
        {
            "id": "review-1",
            "report_id": "report-1",
            "session_id": "session-1",
            "score": 82.0,
            "status": "PASS",
            "issues": [],
            "feedback": None,
            "hallucination_risks": ["Verify the broad claim against its source."],
            "citation_coverage": 0.8,
            "created_at": datetime.now(),
        }
    )

    assert review.hallucination_risks == ["Verify the broad claim against its source."]
