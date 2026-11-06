"""
Test Suite: Exhaustive Decision Tree Path Traversal & Safety Regression
Covers:
- Automated traversal of EVERY possible path in all 3 hazard trees
- Explicit flood test paths 1-5 with assertions on advice and summary checklist
- Equivalent paths for earthquake and landslide
- Safety regression assertions (no walking/swimming/driving in water, no electricity in water)
"""

import pytest
from engine.tree_engine import tree_engine


# =============================================================================
# 1. EXHAUSTIVE PATH ENUMERATION (EVERY POSSIBLE PATH IN ALL TREES)
# =============================================================================

def enumerate_all_tree_paths(hazard_id: str):
    """Recursively walks every option branch to verify that all paths terminate at summary."""
    tree = tree_engine.get_tree(hazard_id)
    initial_id = tree["initial_node_id"]

    def walk(node_id, current_path, visited_nodes):
        node = tree["nodes"][node_id]
        ntype = node["type"]

        if ntype == "summary":
            return [current_path + [node_id]]

        if node_id in visited_nodes:
            raise RuntimeError(f"Infinite loop detected at node '{node_id}' in hazard '{hazard_id}'")

        new_visited = visited_nodes | {node_id}

        if ntype in ("question", "emergency_check"):
            all_paths = []
            for opt in node.get("options", []):
                nxt = opt.get("next_node")
                paths = walk(nxt, current_path + [(node_id, opt["id"])], new_visited)
                all_paths.extend(paths)
            return all_paths

        elif ntype == "advice":
            nxt = node.get("next_node")
            return walk(nxt, current_path + [node_id], new_visited)

        return []

    return walk(initial_id, [], set())


@pytest.mark.parametrize("hazard_id", ["flood", "earthquake", "landslide"])
def test_exhaustive_path_traversal(hazard_id):
    """Asserts that 100% of enumerated paths across the tree successfully terminate at a summary node."""
    paths = enumerate_all_tree_paths(hazard_id)
    assert len(paths) >= 4, f"Hazard {hazard_id} must have multiple unique paths (found {len(paths)})"

    # Verify that every path can actually be executed via the engine
    for p in paths:
        # Extract the sequence of option choices
        choices = [item[1] for item in p if isinstance(item, tuple)]
        res = tree_engine.start_conversation(hazard_id, lang="en")
        sid = res["session_id"]
        for c in choices:
            res = tree_engine.process_answer(sid, c)
            assert res["status"] == "success"

        assert res["is_complete"] is True
        assert res["summary"] is not None
        assert "risk_level" in res["summary"]


# =============================================================================
# 2. THE 5 MANDATORY FLOOD PATHS WITH SPECIFIC ASSERTIONS
# =============================================================================

def test_flood_path_1_indoors_lowlying_water_trapped():
    """Path 1: Indoors -> Low-lying -> Floodwater entering -> Injured/trapped."""
    res = tree_engine.start_conversation("flood", "en")
    sid = res["session_id"]

    # 1. Indoors
    res = tree_engine.process_answer(sid, "opt_indoors")
    assert "flood-prone or low-lying area" in res["question"]

    # 2. Low-lying Yes
    res = tree_engine.process_answer(sid, "opt_in_lowlying_yes")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "higher floors" in advice_texts
    assert "Switch off electricity and gas ONLY if it is safe to do so" in advice_texts
    assert "Is floodwater entering your house?" in res["question"]

    # 3. Water entering Yes
    res = tree_engine.process_answer(sid, "opt_water_in_yes")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "Move IMMEDIATELY to a higher floor" in advice_texts
    assert "Do NOT touch electrical appliances" in advice_texts
    assert "Do NOT enter floodwater" in advice_texts

    # 4. Vulnerable question -> opt_vuln_yes
    res = tree_engine.process_answer(sid, "opt_vuln_yes")
    assert "Are you injured or trapped?" in res["question"]

    # 5. Injured / Trapped Yes
    res = tree_engine.process_answer(sid, "opt_trapped_yes")
    assert res["is_complete"] is True

    summary = res["summary"]
    assert summary["risk_level"] == "CRITICAL EMERGENCY"
    assert any("112" in act for act in summary["immediate_actions"])
    assert any("highest floor" in act.lower() for act in summary["immediate_actions"])
    assert any("electricity" in step.lower() for step in summary["next_steps"] + summary["immediate_actions"])


def test_flood_path_2_indoors_not_lowlying_no_water_not_injured():
    """Path 2: Indoors -> Not low-lying -> No water entering -> Not injured."""
    res = tree_engine.start_conversation("flood", "en")
    sid = res["session_id"]

    # 1. Indoors
    res = tree_engine.process_answer(sid, "opt_indoors")

    # 2. Low-lying No
    res = tree_engine.process_answer(sid, "opt_in_lowlying_no")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "monitor official weather" in advice_texts

    # 3. Water entering No
    res = tree_engine.process_answer(sid, "opt_water_in_no")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "Stay indoors if the building is safe" in advice_texts

    # 4. Vulnerable No
    res = tree_engine.process_answer(sid, "opt_vuln_no")

    # 5. Trapped No
    res = tree_engine.process_answer(sid, "opt_trapped_no")
    assert res["is_complete"] is True

    summary = res["summary"]
    assert summary["risk_level"] == "MODERATE"
    assert len(summary["next_steps"]) > 0


def test_flood_path_3_outdoors_blocked_near_river():
    """Path 3: Outdoors -> Floodwater blocking path -> Near river."""
    res = tree_engine.start_conversation("flood", "en")
    sid = res["session_id"]

    # 1. Outdoors
    res = tree_engine.process_answer(sid, "opt_outdoors")
    assert "floodwater blocking your path" in res["question"]

    # 2. Path blocked Yes
    res = tree_engine.process_answer(sid, "opt_path_blocked_yes")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "Never walk, swim, or drive through floodwater" in advice_texts
    assert "Turn Around, Don't Drown" in advice_texts

    # 3. Near river Yes
    res = tree_engine.process_answer(sid, "opt_river_yes")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "Move away immediately" in advice_texts
    assert "Riverbanks can collapse" in advice_texts

    # 4. Vulnerable No
    res = tree_engine.process_answer(sid, "opt_vuln_no")

    # 5. Trapped No
    res = tree_engine.process_answer(sid, "opt_trapped_no")
    assert res["is_complete"] is True

    summary = res["summary"]
    assert summary["risk_level"] in ("CRITICAL EMERGENCY", "HIGH RISK")
    assert any("Turn Around, Don't Drown" in act for act in summary["immediate_actions"])


def test_flood_path_4_vehicle_surrounded():
    """Path 4: Vehicle -> Surrounded by floodwater."""
    res = tree_engine.start_conversation("flood", "en")
    sid = res["session_id"]

    # 1. Inside vehicle
    res = tree_engine.process_answer(sid, "opt_vehicle")
    assert "vehicle surrounded by or entering floodwater" in res["question"]

    # 2. Surrounded Yes
    res = tree_engine.process_answer(sid, "opt_veh_surrounded_yes")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "Stop driving immediately" in advice_texts
    assert "Never attempt to drive through floodwater" in advice_texts
    assert "leave the vehicle and move to higher ground" in advice_texts

    # 3. Vulnerable No
    res = tree_engine.process_answer(sid, "opt_vuln_no")

    # 4. Trapped Yes
    res = tree_engine.process_answer(sid, "opt_trapped_yes")
    assert res["is_complete"] is True

    summary = res["summary"]
    assert summary["risk_level"] == "CRITICAL EMERGENCY"
    assert any("Abandon your vehicle" in act for act in summary["immediate_actions"])


def test_flood_path_5_vehicle_no_floodwater_not_injured():
    """Path 5: Vehicle -> No floodwater -> Not injured."""
    res = tree_engine.start_conversation("flood", "en")
    sid = res["session_id"]

    # 1. Inside vehicle
    res = tree_engine.process_answer(sid, "opt_vehicle")

    # 2. Surrounded No
    res = tree_engine.process_answer(sid, "opt_veh_surrounded_no")
    advice_texts = " ".join([a["text"] for a in res["advice"]])
    assert "Avoid flooded roads" in advice_texts

    # 3. Vulnerable No
    res = tree_engine.process_answer(sid, "opt_vuln_no")

    # 4. Trapped No
    res = tree_engine.process_answer(sid, "opt_trapped_no")
    assert res["is_complete"] is True

    summary = res["summary"]
    assert summary["risk_level"] == "MODERATE"


# =============================================================================
# 3. EQUIVALENT PATHS FOR EARTHQUAKE & LANDSLIDE
# =============================================================================

def test_earthquake_path_highrise_gas_leak_trapped():
    """Earthquake Path: High-rise -> Gas smell -> Coastal -> Trapped."""
    res = tree_engine.start_conversation("earthquake", "en")
    sid = res["session_id"]

    # 1. High-rise
    res = tree_engine.process_answer(sid, "opt_eq_highrise")
    adv_text = " ".join([a["text"] for a in res["advice"]])
    assert "NEVER USE ELEVATORS" in adv_text

    # 2. Gas leak Yes
    res = tree_engine.process_answer(sid, "opt_gas_yes")
    adv_text = " ".join([a["text"] for a in res["advice"]])
    assert "Do NOT strike matches" in adv_text

    # 3. Coastal Yes
    res = tree_engine.process_answer(sid, "opt_coastal_yes")
    adv_text = " ".join([a["text"] for a in res["advice"]])
    assert "TSUNAMI RISK" in adv_text

    # 4. Trapped Yes
    res = tree_engine.process_answer(sid, "opt_eq_trapped_yes")
    assert res["is_complete"] is True
    summary = res["summary"]
    assert summary["risk_level"] == "CRITICAL EMERGENCY"
    assert any("Drop, Cover, and Hold On" in act for act in summary["immediate_actions"])


def test_landslide_path_slope_active_signs():
    """Landslide Path: House on slope -> Active ground cracks -> Trapped."""
    res = tree_engine.start_conversation("landslide", "en")
    sid = res["session_id"]

    # 1. House on slope
    res = tree_engine.process_answer(sid, "opt_ls_house_slope")

    # 2. Active signs Yes
    res = tree_engine.process_answer(sid, "opt_signs_yes")
    adv_text = " ".join([a["text"] for a in res["advice"]])
    assert "EVACUATE IMMEDIATELY" in adv_text
    assert "PERPENDICULAR" in adv_text
    assert "NEVER run downhill" in adv_text

    # 3. Trapped No
    res = tree_engine.process_answer(sid, "opt_ls_trapped_no")
    assert res["is_complete"] is True
    summary = res["summary"]
    assert any("PERPENDICULAR" in act for act in summary["immediate_actions"])


# =============================================================================
# 4. STRICT SAFETY REGRESSION TESTS
# =============================================================================

def test_safety_regression_never_walk_or_drive_in_floodwater():
    """Asserts that no advice string anywhere recommends walking, swimming, or driving through floodwater."""
    flood_tree = tree_engine.get_tree("flood")
    for nid, node in flood_tree["nodes"].items():
        if node.get("type") == "advice":
            text_en = node["text"]["en"].lower()
            # Must explicitly warn AGAINST walking/swimming/driving
            if "walk" in text_en or "drive" in text_en or "swim" in text_en:
                assert ("never" in text_en or "avoid" in text_en or "do not" in text_en or "stop" in text_en), (
                    f"Node {nid} has unsafe driving/walking recommendation: {text_en}"
                )


def test_safety_regression_no_switching_power_in_water():
    """Asserts that no advice tells the user to touch electrical systems while in water."""
    for hid in ["flood", "earthquake", "landslide"]:
        tree = tree_engine.get_tree(hid)
        for nid, node in tree["nodes"].items():
            if node.get("type") == "advice":
                text_en = node["text"]["en"].lower()
                if "electricity" in text_en or "switches" in text_en or "gas" in text_en:
                    # Must emphasize ONLY IF SAFE / NEVER IN WATER / NO MATCHES
                    assert ("safe to do so" in text_en or "never touch" in text_en or "do not touch" in text_en or "strike matches" in text_en), (
                        f"Node {nid} in {hid} has unsafe electrical advice: {text_en}"
                    )
