"""
Test Suite: Flask REST API & Web Route Verification
Tests start, answer, back, restart, summary, export, triage, feedback,
invalid input, expired session, and security compliance headers.
"""

import json
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert "flood" in data["hazards_loaded"]


def test_api_hazards(client):
    res = client.get("/api/hazards?lang=en")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["hazards"]) == 3


def test_api_start_valid_and_invalid(client):
    # Valid
    res = client.post("/api/start", data=json.dumps({"hazard_id": "flood", "lang": "en"}))
    assert res.status_code == 200
    data = res.get_json()
    assert "session_id" in data
    assert data["hazard_id"] == "flood"

    # Invalid hazard
    res_bad = client.post("/api/start", data=json.dumps({"hazard_id": "meteor_strike"}))
    assert res_bad.status_code == 400


def test_api_answer_flow_and_errors(client):
    # 1. Start
    res_start = client.post("/api/start", data=json.dumps({"hazard_id": "flood"}))
    sid = res_start.get_json()["session_id"]

    # 2. Answer with valid choice
    res_ans = client.post("/api/answer", data=json.dumps({
        "session_id": sid,
        "choice": "opt_indoors"
    }))
    assert res_ans.status_code == 200
    data = res_ans.get_json()
    assert data["status"] == "success"
    assert data["can_go_back"] is True

    # 3. Missing session ID (clear cookie first)
    client.set_cookie("ds_session_id", "")
    res_no_sid = client.post("/api/answer", data=json.dumps({"choice": "Yes"}))
    assert res_no_sid.status_code == 400
    assert res_no_sid.get_json()["code"] == "MISSING_SESSION"

    # 4. Missing choice
    res_no_choice = client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": ""}))
    assert res_no_choice.status_code == 400
    assert res_no_choice.get_json()["code"] == "INVALID_INPUT"

    # 5. Non-existent session
    res_bad_sid = client.post("/api/answer", data=json.dumps({
        "session_id": "non-existent-uuid-1234",
        "choice": "Yes"
    }))
    assert res_bad_sid.status_code == 200
    assert res_bad_sid.get_json()["code"] == "SESSION_EXPIRED"


def test_api_back_and_restart(client):
    # Start and answer 2 steps
    res = client.post("/api/start", data=json.dumps({"hazard_id": "flood"}))
    sid = res.get_json()["session_id"]

    client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": "opt_indoors"}))
    client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": "opt_in_lowlying_yes"}))

    # Back
    res_back = client.post("/api/back", data=json.dumps({"session_id": sid}))
    assert res_back.status_code == 200
    assert res_back.get_json()["status"] == "success"

    # Restart
    res_restart = client.post("/api/restart", data=json.dumps({"session_id": sid}))
    assert res_restart.status_code == 200
    assert res_restart.get_json()["status"] == "success"
    assert res_restart.get_json()["can_go_back"] is False


def test_api_summary_and_export(client):
    # Run full conversation
    res = client.post("/api/start", data=json.dumps({"hazard_id": "flood"}))
    sid = res.get_json()["session_id"]

    client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": "opt_indoors"}))
    client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": "opt_in_lowlying_no"}))
    client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": "opt_water_in_no"}))
    client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": "opt_vuln_no"}))
    client.post("/api/answer", data=json.dumps({"session_id": sid, "choice": "opt_trapped_no"}))

    # Get summary
    res_sum = client.get(f"/api/summary?session_id={sid}")
    assert res_sum.status_code == 200
    sum_data = res_sum.get_json()["summary"]
    assert "risk_level" in sum_data

    # Export plain text
    res_txt = client.get(f"/api/export/txt?session_id={sid}")
    assert res_txt.status_code == 200
    assert "DISASTERSAFE" in res_txt.data.decode("utf-8")

    # Export JSON
    res_json = client.get(f"/api/export/json?session_id={sid}")
    assert res_json.status_code == 200
    assert res_json.get_json()["hazard_id"] == "flood"


def test_api_triage_and_feedback(client):
    # Triage
    res_t = client.post("/api/triage", data=json.dumps({"phenomenon": "ground shaking tremors"}))
    assert res_t.status_code == 200
    assert res_t.get_json()["hazard"] == "earthquake"

    # Feedback
    res_f = client.post("/api/feedback", data=json.dumps({"hazard_id": "flood", "rating": "up", "comment": "Excellent guidance"}))
    assert res_f.status_code == 200


def test_security_headers(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_html_views(client):
    views = ["/", "/chat?hazard=flood", "/flowchart?hazard=flood", "/kit", "/quiz", "/about"]
    for v in views:
        res = client.get(v)
        assert res.status_code == 200, f"View {v} returned {res.status_code}"


def test_removed_views_return_404(client):
    """Confirm /plan and /insights return 404 Not Found rather than crashing."""
    for removed in ["/plan", "/insights"]:
        res = client.get(removed)
        assert res.status_code == 404, f"Removed route {removed} did not return 404"
