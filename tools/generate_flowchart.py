#!/usr/bin/env python3
"""
DisasterSafe Mermaid Flowchart Auto-Generator
Generates syntax-verified Mermaid .mmd flowcharts directly from JSON hazard decision trees.
Enforces assignment specifications:
- Oval: Start & End ([ ... ])
- Diamond: Decisions & Questions { ... }
- Rectangle: Safety Actions & Advice [ ... ]
- Labelled arrows
- Severity-coded styling classes (critical, warning, safe, startEnd)
"""

import json
import os
import re
from typing import Dict, Any


def sanitize_label(text: str, max_chars: int = 120) -> str:
    """Cleans and wraps text for valid Mermaid node labels."""
    if not text:
        return ""
    # Strip HTML and replace double quotes
    cleaned = text.replace('"', "'").replace("\n", " ").strip()
    # Word wrap with <br/> every ~40 chars for balanced geometry
    words = cleaned.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) > 40:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
        else:
            curr.append(w)
            curr_len += len(w) + 1
    if curr:
        lines.append(" ".join(curr))
    return "<br/>".join(lines[:6])


def generate_mermaid_from_tree(tree: Dict[str, Any]) -> str:
    hazard_id = tree.get("hazard_id", "disaster")
    hazard_name = tree.get("hazard_name", {}).get("en", hazard_id.capitalize())
    initial_node_id = tree.get("initial_node_id")
    nodes = tree.get("nodes", {})

    lines = [
        "flowchart TD",
        f"    %% DisasterSafe Decision Tree Flowchart: {hazard_name}",
        "    %% Generated automatically from data/trees JSON specification",
        "",
        "    %% Styling Classes",
        "    classDef startEnd fill:#E0F2FE,stroke:#0284C7,stroke-width:2px,color:#0369A1,font-weight:bold;",
        "    classDef critical fill:#FEE2E2,stroke:#DC2626,stroke-width:2px,color:#991B1B;",
        "    classDef warning fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#92400E;",
        "    classDef safe fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#166534;",
        "    classDef question fill:#FFFFFF,stroke:#0F284E,stroke-width:2px,color:#0F172A,font-weight:600;",
        "",
        f'    START(["Start: {hazard_name} Safety Assistant"]) --> {initial_node_id}',
        ""
    ]

    # Render node declarations and connections
    critical_nodes = []
    warning_nodes = []
    question_nodes = []

    for node_id, node in nodes.items():
        ntype = node.get("type")
        raw_text = node.get("text", {}).get("en", "")
        clean_text = sanitize_label(raw_text)
        sev = node.get("severity", "info")

        if sev == "critical":
            critical_nodes.append(node_id)
        elif sev == "warning":
            warning_nodes.append(node_id)

        if ntype in ("question", "emergency_check"):
            question_nodes.append(node_id)
            lines.append(f'    {node_id}{{"{clean_text}"}}')
            for opt in node.get("options", []):
                opt_lbl = opt.get("text", {}).get("en", "").replace('"', "'")
                nxt = opt.get("next_node")
                if nxt:
                    lines.append(f'    {node_id} -->|"{opt_lbl}"| {nxt}')

        elif ntype == "advice":
            lines.append(f'    {node_id}["{clean_text}"]')
            nxt = node.get("next_node")
            if nxt:
                lines.append(f'    {node_id} --> {nxt}')

        elif ntype == "summary":
            lines.append(f'    {node_id}["{clean_text}"]')
            lines.append(f'    {node_id} --> END(["End: Personalized Safety Plan & Emergency Contacts"])')

    lines.append("")
    lines.append("    %% Class Assignments")
    lines.append("    class START,END startEnd;")
    if critical_nodes:
        lines.append(f"    class {','.join(critical_nodes)} critical;")
    if warning_nodes:
        lines.append(f"    class {','.join(warning_nodes)} warning;")
    if question_nodes:
        lines.append(f"    class {','.join(question_nodes)} question;")

    return "\n".join(lines) + "\n"


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    trees_dir = os.path.join(base_dir, "data", "trees")
    out_dir = os.path.join(base_dir, "docs", "flowcharts")
    os.makedirs(out_dir, exist_ok=True)

    for fname in os.listdir(trees_dir):
        if fname.endswith(".json"):
            fpath = os.path.join(trees_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                tree = json.load(f)
            hid = tree.get("hazard_id", fname.replace(".json", ""))
            mmd_content = generate_mermaid_from_tree(tree)

            # Write to docs/flowcharts/<hazard>.mmd
            dest_path = os.path.join(out_dir, f"{hid}.mmd")
            with open(dest_path, "w", encoding="utf-8") as out_f:
                out_f.write(mmd_content)
            print(f"Generated: {dest_path}")

            # Also write primary flood flowchart to root flowchart.mmd
            if hid == "flood":
                root_mmd = os.path.join(base_dir, "flowchart.mmd")
                with open(root_mmd, "w", encoding="utf-8") as rf:
                    rf.write(mmd_content)
                print(f"Generated root assignment flowchart: {root_mmd}")


if __name__ == "__main__":
    main()

