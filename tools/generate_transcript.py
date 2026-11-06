#!/usr/bin/env python3
"""
DisasterSafe Real Transcript Generator
Runs scripted end-to-end conversations through the actual TreeEngine logic
and generates verified transcript files for all mandatory assignment and multi-hazard paths.
"""

import os
import sys
from datetime import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from engine.tree_engine import tree_engine


def run_conversation(hazard_id: str, script_answers: list, scenario_name: str, lang: str = "en") -> str:
    """Executes a scripted path through the engine and returns formatted transcript text."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"DISASTERSAFE / SAFEKERALA - OFFICIAL CONVERSATION TRANSCRIPT")
    lines.append(f"HAZARD    : {hazard_id.upper()}")
    lines.append(f"SCENARIO  : {scenario_name}")
    lines.append(f"GENERATED : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Automated Engine Run)")
    lines.append(f"AUTHORITY : National Disaster Management Authority (NDMA) & KSDMA Protocols")
    lines.append("=" * 80)
    lines.append("")

    # Start
    res = tree_engine.start_conversation(hazard_id, lang=lang)
    session_id = res["session_id"]

    lines.append(f"[BOT] {res['welcome_message']}")
    lines.append("")

    step_num = 1
    answer_idx = 0

    while not res.get("is_complete"):
        q_text = res.get("question", "")
        options = res.get("options", [])
        lines.append(f"[BOT Q{step_num}] {q_text}")
        for idx, opt in enumerate(options, 1):
            lines.append(f"    ({idx}) {opt['text']}")
        lines.append("")

        if answer_idx >= len(script_answers):
            lines.append(f"[ERROR] Script ran out of answers at Q{step_num}")
            break

        user_choice = script_answers[answer_idx]
        lines.append(f"[USER] > {user_choice}")
        lines.append("-" * 60)

        # Process through engine
        res = tree_engine.process_answer(session_id, user_choice)
        answer_idx += 1
        step_num += 1

        # Print any intermediate advice chain
        for adv in res.get("advice", []):
            sev = adv.get("severity", "info").upper()
            src = adv.get("source_id", "NDMA")
            lines.append(f"[BOT ADVICE - {sev}] (Ref: {src})")
            lines.append(f"  {adv['text']}")
            lines.append("")

    # If complete, render summary
    if res.get("is_complete"):
        summary = res.get("summary", {})
        lines.append("=" * 80)
        lines.append("                  PERSONALIZED DISASTER SAFETY PLAN")
        lines.append("=" * 80)
        lines.append(f"ASSESSMENT STATUS : {summary.get('risk_level')}")
        lines.append(f"HAZARD            : {hazard_id.upper()}")
        lines.append("")

        lines.append("⚡ IMMEDIATE PRIORITY SAFETY ACTIONS:")
        for act in summary.get("immediate_actions", []):
            lines.append(f"  • {act}")
        lines.append("")

        lines.append("✓ NEXT STEPS & PERSONALIZED CHECKLIST:")
        for step in summary.get("next_steps", []):
            lines.append(f"  • {step}")
        lines.append("")

        lines.append("🎒 PREPARATION & EVACUATION PACKING:")
        for item in summary.get("preparation", []):
            lines.append(f"  • {item}")
        lines.append("")

        lines.append("📞 VERIFIED EMERGENCY HELPLINES (INDIA):")
        for num, desc in summary.get("emergency_numbers", {}).items():
            lines.append(f"  • {num.ljust(6)}: {desc}")
        lines.append("")

        lines.append(f"DISCLAIMER:")
        lines.append(f"  {summary.get('disclaimer')}")
        lines.append("=" * 80)
        lines.append("[ASSESSMENT COMPLETED SUCCESSFULLY]")
        lines.append("")

    return "\n".join(lines)


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(base_dir, "docs", "transcripts")
    os.makedirs(out_dir, exist_ok=True)

    transcripts = [
        # Path 1: Indoors -> Low-lying -> Floodwater entering -> Vulnerable -> Injured/trapped
        (
            "flood",
            ["Indoors (at home/building)", "Yes", "Yes", "Yes", "Yes"],
            "Flood Path 1: Indoors -> Low-Lying Area -> Water Ingress -> Trapped / Injured",
            "flood_path_1.txt",
            True  # Primary transcript for assignment
        ),
        # Path 2: Indoors -> Not low-lying -> No water entering -> No vulnerable -> Not injured
        (
            "flood",
            ["Indoors (at home/building)", "No", "No", "No", "No"],
            "Flood Path 2: Indoors -> Non Low-Lying -> No Ingress -> Not Injured",
            "flood_path_2.txt",
            False
        ),
        # Path 3: Outdoors -> Floodwater blocking path -> Near river -> No vulnerable -> Not injured
        (
            "flood",
            ["Outdoors", "Yes", "Yes", "No", "No"],
            "Flood Path 3: Outdoors -> Path Blocked -> Near Overflowing River",
            "flood_path_3.txt",
            False
        ),
        # Path 4: Vehicle -> Surrounded by floodwater -> No vulnerable -> Injured/Trapped
        (
            "flood",
            ["Inside a vehicle", "Yes", "No", "Yes"],
            "Flood Path 4: Vehicle -> Surrounded by Floodwater -> Trapped",
            "flood_path_4.txt",
            False
        ),
        # Path 5: Vehicle -> No floodwater -> No vulnerable -> Not injured
        (
            "flood",
            ["Inside a vehicle", "No", "No", "No"],
            "Flood Path 5: Vehicle -> Clear Elevated Route -> Not Injured",
            "flood_path_5.txt",
            False
        ),
        # Earthquake Path 1: High-rise -> Gas smell -> Coastal -> Trapped
        (
            "earthquake",
            ["Inside a high-rise / multi-storey apartment", "Yes", "Yes", "Yes"],
            "Earthquake Path 1: High-Rise -> Gas Smell Detected -> Coastal Tsunami Risk -> Trapped Rubble",
            "earthquake_path_1.txt",
            False
        ),
        # Landslide Path 1: House on slope -> Active signs -> Injured/Trapped
        (
            "landslide",
            ["Inside a house or building on a hill slope", "Yes, active signs observed", "Yes"],
            "Landslide Path 1: Hill Slope Residence -> Ground Cracks Observed -> Trapped Debris",
            "landslide_path_1.txt",
            False
        )
    ]

    for hazard_id, answers, scenario, fname, is_primary in transcripts:
        output_text = run_conversation(hazard_id, answers, scenario)
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Generated transcript: {fpath}")

        if is_primary:
            root_sample = os.path.join(base_dir, "sample_transcript.txt")
            with open(root_sample, "w", encoding="utf-8") as rf:
                rf.write(output_text)
            print(f"Saved primary assignment transcript: {root_sample}")


if __name__ == "__main__":
    main()
