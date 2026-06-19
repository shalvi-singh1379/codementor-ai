import json
from datetime import datetime, timezone, timedelta
from app.memory.database import get_session, User, Review, KnowledgeGap

# thresholds by severity (from our design discussion)
THRESHOLDS = {
    "error": 2,
    "warning": 3,
    "convention": 5,
}

# only count occurrences within this many days (recency window)
RECENCY_WINDOW_DAYS = 30


def ensure_user_exists(user_id: str):
    """creates a user record if it doesn't already exist"""
    session = get_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(user_id=user_id)
            session.add(user)
            session.commit()
        return user
    finally:
        session.close()


def save_review(user_id: str, code: str, lint_result: dict):
    """saves a review and updates knowledge gap tracking"""
    session = get_session()
    try:
        # save the review record
        review = Review(
            user_id=user_id,
            code_submitted=code,
            lint_issues_json=json.dumps(lint_result)
        )
        session.add(review)
        session.commit()

        # update knowledge gaps based on this review's issues
        _update_knowledge_gaps(session, user_id, lint_result)

    finally:
        session.close()


def _update_knowledge_gaps(session, user_id: str, lint_result: dict):
    """internal: increments occurrence counts for each issue found"""
    all_issues = (
        [(i["symbol"], "error") for i in lint_result.get("errors", [])] +
        [(i["symbol"], "warning") for i in lint_result.get("warnings", [])] +
        [(i["symbol"], "convention") for i in lint_result.get("conventions", [])]
    )

    for symbol, issue_type in all_issues:
        gap = session.query(KnowledgeGap).filter_by(
            user_id=user_id,
            issue_symbol=symbol
        ).first()

        if gap:
            gap.occurrence_count += 1
            gap.last_seen_at = datetime.now(timezone.utc)
        else:
            gap = KnowledgeGap(
                user_id=user_id,
                issue_symbol=symbol,
                issue_type=issue_type,
                occurrence_count=1,
                last_seen_at=datetime.now(timezone.utc)
            )
            session.add(gap)

    session.commit()


def get_active_knowledge_gaps(user_id: str) -> list[dict]:
    """
    returns knowledge gaps that meet the threshold for their severity
    AND were seen within the recency window.
    """
    session = get_session()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=RECENCY_WINDOW_DAYS)

        gaps = session.query(KnowledgeGap).filter(
            KnowledgeGap.user_id == user_id,
            KnowledgeGap.last_seen_at >= cutoff
        ).all()

        active_gaps = []
        for gap in gaps:
            threshold = THRESHOLDS.get(gap.issue_type, 5)
            if gap.occurrence_count >= threshold:
                active_gaps.append({
                    "symbol": gap.issue_symbol,
                    "type": gap.issue_type,
                    "occurrence_count": gap.occurrence_count,
                    "last_seen_at": gap.last_seen_at.isoformat()
                })

        return active_gaps
    finally:
        session.close()


def format_knowledge_gaps_for_prompt(gaps: list[dict]) -> str:
    """formats active knowledge gaps into a string for the agent's context"""
    if not gaps:
        return ""

    lines = ["KNOWN KNOWLEDGE GAPS FOR THIS USER (from past sessions):"]
    for gap in gaps:
        lines.append(
            f"- {gap['symbol']} ({gap['type']}) — seen {gap['occurrence_count']} times"
        )
    lines.append(
        "\nIf the current code relates to any of these gaps, mention that "
        "this is a recurring pattern and give extra explanation."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    # test the flow
    test_user = "test-user-123"
    ensure_user_exists(test_user)

    fake_lint_result = {
        "errors": [{"symbol": "undefined-variable", "message": "..."}],
        "warnings": [{"symbol": "unspecified-encoding", "message": "..."}],
        "conventions": []
    }

    # simulate 3 reviews with the same issues
    for i in range(3):
        save_review(test_user, f"fake code {i}", fake_lint_result)

    gaps = get_active_knowledge_gaps(test_user)
    print(f"active knowledge gaps after 3 reviews: {len(gaps)}")
    for g in gaps:
        print(f"  {g}")

    print("\nformatted for prompt:")
    print(format_knowledge_gaps_for_prompt(gaps))