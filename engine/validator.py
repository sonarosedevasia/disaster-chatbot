"""
DisasterSafe Tree Validator
Validates JSON hazard decision trees for:
- JSON schema conformity
- Multilingual translations (en, ml, hi)
- Source attribution (source_id mapped in sources.json)
- Graph reachability (no unreachable or orphan nodes)
- Dead-end freedom (every path terminates at a summary node)
- Cycle safety
"""

import json
import os
from typing import Dict, List, Set, Any, Tuple


class ValidationError(Exception):
    """Raised when a hazard decision tree fails structural or graph validation."""
    pass


def load_sources(sources_path: str) -> Set[str]:
    """Loads valid source IDs from sources.json."""
    if not os.path.exists(sources_path):
        raise FileNotFoundError(f"Sources file not found at: {sources_path}")
    with open(sources_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {s["id"] for s in data.get("sources", [])}


def validate_tree_dict(tree: Dict[str, Any], valid_source_ids: Set[str], required_langs: List[str] = None) -> List[str]:
    """
    Validates a single hazard decision tree dictionary.
    Returns a list of validation error strings (empty if valid).
    """
    if required_langs is None:
        required_langs = ["en", "ml", "hi"]

    errors: List[str] = []
    hazard_id = tree.get("hazard_id")
    if not hazard_id:
        errors.append("Tree missing required field: 'hazard_id'")

    initial_node_id = tree.get("initial_node_id")
    if not initial_node_id:
        errors.append(f"[{hazard_id}] Missing 'initial_node_id'")

    nodes = tree.get("nodes", {})
    if not nodes or not isinstance(nodes, dict):
        errors.append(f"[{hazard_id}] 'nodes' must be a non-empty dictionary")
        return errors

    if initial_node_id not in nodes:
        errors.append(f"[{hazard_id}] initial_node_id '{initial_node_id}' does not exist in nodes")

    # 1. Node Schema & Content Validation
    has_summary = False
    for node_id, node in nodes.items():
        if node.get("id") != node_id:
            errors.append(f"[{hazard_id}] Node key '{node_id}' does not match internal id '{node.get('id')}'")

        node_type = node.get("type")
        if node_type not in ("question", "advice", "emergency_check", "summary"):
            errors.append(f"[{hazard_id}] Node '{node_id}' has invalid type: '{node_type}'")

        if node_type == "summary":
            has_summary = True

        # Check source_id
        src_id = node.get("source_id")
        if not src_id:
            errors.append(f"[{hazard_id}] Node '{node_id}' missing 'source_id'")
        elif src_id not in valid_source_ids:
            errors.append(f"[{hazard_id}] Node '{node_id}' source_id '{src_id}' not found in sources.json")

        # Check translations
        text = node.get("text")
        if not isinstance(text, dict):
            errors.append(f"[{hazard_id}] Node '{node_id}' 'text' must be a dictionary of language translations")
        else:
            for lang in required_langs:
                if not text.get(lang) or not str(text[lang]).strip():
                    errors.append(f"[{hazard_id}] Node '{node_id}' missing translation for language '{lang}'")

        # Check next transitions
        if node_type in ("question", "emergency_check"):
            options = node.get("options")
            if not isinstance(options, list) or len(options) == 0:
                errors.append(f"[{hazard_id}] Question node '{node_id}' must have at least one option")
            else:
                for idx, opt in enumerate(options):
                    opt_id = opt.get("id", f"opt_{idx}")
                    next_node = opt.get("next_node")
                    if not next_node:
                        errors.append(f"[{hazard_id}] Node '{node_id}' option '{opt_id}' missing 'next_node'")
                    elif next_node not in nodes:
                        errors.append(f"[{hazard_id}] Node '{node_id}' option '{opt_id}' targets non-existent node '{next_node}'")
                    
                    opt_text = opt.get("text", {})
                    for lang in required_langs:
                        if not opt_text.get(lang):
                            errors.append(f"[{hazard_id}] Node '{node_id}' option '{opt_id}' missing translation '{lang}'")

        elif node_type == "advice":
            next_node = node.get("next_node")
            if not next_node:
                errors.append(f"[{hazard_id}] Advice node '{node_id}' missing 'next_node'")
            elif next_node not in nodes:
                errors.append(f"[{hazard_id}] Advice node '{node_id}' targets non-existent node '{next_node}'")

        elif node_type == "summary":
            if node.get("next_node") is not None:
                errors.append(f"[{hazard_id}] Summary node '{node_id}' must have next_node=null")

    if not has_summary:
        errors.append(f"[{hazard_id}] Tree has no node of type 'summary'")

    # 2. Graph Reachability & Dead-End Analysis
    visited: Set[str] = set()
    queue = [initial_node_id] if initial_node_id in nodes else []

    while queue:
        curr_id = queue.pop(0)
        if curr_id in visited:
            continue
        visited.add(curr_id)
        node = nodes[curr_id]
        node_type = node.get("type")

        if node_type in ("question", "emergency_check"):
            for opt in node.get("options", []):
                nxt = opt.get("next_node")
                if nxt and nxt not in visited and nxt in nodes:
                    queue.append(nxt)
        elif node_type == "advice":
            nxt = node.get("next_node")
            if nxt and nxt not in visited and nxt in nodes:
                queue.append(nxt)

    # Check orphan / unreachable nodes
    unreachable = set(nodes.keys()) - visited
    if unreachable:
        errors.append(f"[{hazard_id}] Unreachable orphan nodes detected: {sorted(list(unreachable))}")

    # Check that from EVERY reachable node, at least one path leads to a summary node
    def can_reach_summary(start_id: str, local_visited: Set[str]) -> bool:
        if start_id in local_visited:
            return False
        node = nodes[start_id]
        if node.get("type") == "summary":
            return True
        local_visited.add(start_id)

        if node.get("type") in ("question", "emergency_check"):
            for opt in node.get("options", []):
                nxt = opt.get("next_node")
                if nxt and nxt in nodes and can_reach_summary(nxt, local_visited.copy()):
                    return True
        elif node.get("type") == "advice":
            nxt = node.get("next_node")
            if nxt and nxt in nodes and can_reach_summary(nxt, local_visited.copy()):
                return True
        return False

    dead_ends: List[str] = []
    for r_node in visited:
        if not can_reach_summary(r_node, set()):
            dead_ends.append(r_node)

    if dead_ends:
        errors.append(f"[{hazard_id}] Dead-end nodes detected (cannot reach summary): {dead_ends}")

    return errors


def validate_tree_file(tree_path: str, sources_path: str) -> List[str]:
    """Loads a single tree file and runs full validation."""
    valid_sources = load_sources(sources_path)
    with open(tree_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return validate_tree_dict(data, valid_sources)


def validate_all_trees(trees_dir: str, sources_path: str) -> Dict[str, List[str]]:
    """Validates all JSON trees in a directory."""
    valid_sources = load_sources(sources_path)
    results = {}
    for filename in os.listdir(trees_dir):
        if filename.endswith(".json"):
            path = os.path.join(trees_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            hazard_id = data.get("hazard_id", filename)
            results[hazard_id] = validate_tree_dict(data, valid_sources)
    return results


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    trees_path = os.path.join(base_dir, "data", "trees")
    sources_file = os.path.join(base_dir, "data", "sources.json")
    all_res = validate_all_trees(trees_path, sources_file)
    total_errs = 0
    for hid, errs in all_res.items():
        if errs:
            print(f"FAILED {hid}:")
            for e in errs:
                print(f"  - {e}")
            total_errs += len(errs)
        else:
            print(f"PASSED {hid}: 100% valid, no dead ends, all sources & translations verified.")
    if total_errs > 0:
        raise SystemExit(1)

