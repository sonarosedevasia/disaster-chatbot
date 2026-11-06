"""
Test Suite: DisasterSafe TreeEngine & Session Management
Tests core navigation, session state snapshots, undo/back, restart,
rule-based text matching, and personalized summary generation.
"""

import pytest
from engine.tree_engine import tree_engine
from engine.session import session_manager
from engine.matcher import match_user_text_to_option
from engine.summary import generate_personalized_summary


def test_tree_engine_hazard_list():
    """Verify hazard list retrieval in English and Malayalam."""
    hazards_en = tree_engine.get_hazard_list("en")
    ids = [h["id"] for h in hazards_en]
    assert "flood" in ids
    assert "earthquake" in ids
    assert "landslide" in ids

    hazards_ml = tree_engine.get_hazard_list("ml")
    ml_names = [h["name"] for h in hazards_ml]
    assert any("വെള്ളപ്പൊക്കം" in n for n in ml_names)


def test_start_conversation_all_hazards():
    """Verify start conversation produces valid initial state for all 3 hazards."""
    for hid in ["flood", "earthquake", "landslide"]:
        res = tree_engine.start_conversation(hid, lang="en")
        assert res["status"] == "success"
        assert res["session_id"] is not None
        assert res["hazard_id"] == hid
        assert len(res["options"]) > 0
        assert "welcome_message" in res
        assert not res["is_complete"]
        assert not res["can_go_back"]


def test_rule_based_text_matcher():
    """Verify matcher converts synonyms and fuzzy strings to option IDs."""
    options = [
        {"id": "opt_indoors", "text": {"en": "Indoors (at home/building)", "ml": "വീട്ടിലോ", "hi": "घर के अंदर"}},
        {"id": "opt_outdoors", "text": {"en": "Outdoors", "ml": "പുറത്ത്", "hi": "बाहर"}},
        {"id": "opt_vehicle", "text": {"en": "Inside a vehicle", "ml": "വാഹനത്തിൽ", "hi": "वाहन में"}}
    ]

    # Exact match
    m = match_user_text_to_option("Indoors (at home/building)", options, "en")
    assert m is not None and m["id"] == "opt_indoors"

    # Synonym matches
    assert match_user_text_to_option("inside my house", options, "en")["id"] == "opt_indoors"
    assert match_user_text_to_option("outside on road", options, "en")["id"] == "opt_outdoors"
    assert match_user_text_to_option("driving my car", options, "en")["id"] == "opt_vehicle"
    assert match_user_text_to_option("1", options, "en")["id"] == "opt_indoors"
    assert match_user_text_to_option("2", options, "en")["id"] == "opt_outdoors"

    # Multilingual inputs
    assert match_user_text_to_option("വീട്", options, "ml")["id"] == "opt_indoors"
    assert match_user_text_to_option("गाड़ी", options, "hi")["id"] == "opt_vehicle"

    # Completely unmatchable gibberish should return None
    assert match_user_text_to_option("xylophone pizza spaceship 999", options, "en") is None


def test_back_button_undo_step():
    """Verify going back reverts session to previous question without dead-ends."""
    start = tree_engine.start_conversation("flood", "en")
    sid = start["session_id"]
    initial_q = start["question"]

    # Step 1: Answer Indoors
    step1 = tree_engine.process_answer(sid, "Indoors (at home/building)")
    assert step1["status"] == "success"
    assert step1["can_go_back"] is True
    assert step1["question"] != initial_q

    # Step 2: Answer Yes (low lying)
    step2 = tree_engine.process_answer(sid, "Yes")
    assert step2["status"] == "success"
    assert step2["can_go_back"] is True

    # Undo Step 2
    back2 = tree_engine.go_back(sid)
    assert back2["status"] == "success"
    assert back2["current_node_id"] == step1["current_node_id"]

    # Undo Step 1
    back1 = tree_engine.go_back(sid)
    assert back1["status"] == "success"
    assert back1["current_node_id"] == start["current_node_id"]
    assert back1["can_go_back"] is False

    # Attempting to go back further should safely return an error without crash
    back0 = tree_engine.go_back(sid)
    assert back0["status"] == "error"


def test_restart_conversation():
    """Verify restart resets the session to initial question."""
    start = tree_engine.start_conversation("earthquake", "en")
    sid = start["session_id"]

    # Answer step
    step1 = tree_engine.process_answer(sid, "Indoors (low-rise house/building)")
    assert step1["status"] == "success"

    # Restart
    restarted = tree_engine.restart_conversation(sid)
    assert restarted["status"] == "success"
    assert restarted["current_node_id"] == start["current_node_id"]
    assert not restarted["is_complete"]


def test_summary_generator_severity():
    """Verify summary correctly tags critical risk and compiles action items."""
    crit_tags = ["call_emergency_112", "water_ingress", "abandon_vehicle"]
    sum_crit = generate_personalized_summary("flood", crit_tags, [], lang="en")
    assert sum_crit["risk_level"] == "CRITICAL EMERGENCY"
    assert any("112" in act for act in sum_crit["immediate_actions"])

    mod_tags = ["shelter_in_place", "monitoring"]
    sum_mod = generate_personalized_summary("flood", mod_tags, [], lang="en")
    assert sum_mod["risk_level"] == "MODERATE"
    assert len(sum_mod["next_steps"]) > 0

