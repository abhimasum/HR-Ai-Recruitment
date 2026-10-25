import json
import re


def parse_screening_response(text: str) -> dict:
    """Parse the screening model's JSON response and validate its fields."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    match = re.search(r"\{[\s\S]*\}", cleaned)
    payload = match.group(0) if match else cleaned
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("The screening model returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise ValueError("The screening model response must be a JSON object.")
    score = data.get("score")
    reasoning = data.get("reasoning")
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("The screening model did not return an integer score.")
    if not 0 <= score <= 100:
        raise ValueError("The screening model returned a score outside 0-100.")
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise ValueError("The screening model did not return screening reasoning.")
    return {"score": score, "reasoning": reasoning.strip()}


def screening_status(score: int, accept_threshold: int, reject_threshold: int) -> str:
    if score > accept_threshold:
        return "AUTO_ACCEPTED"
    if score >= reject_threshold:
        return "PENDING_HUMAN_REVIEW"
    return "AUTO_REJECTED"


def relevance_route(relevant: bool, retries: int, max_rewrites: int) -> str:
    if relevant:
        return "generate"
    if retries >= max_rewrites:
        return "fallback"
    return "rewrite"
