"""
DisasterSafe Tree Engine
Loads, navigates, and executes data-driven hazard decision trees.
Integrates session tracking, advice chaining, matcher fallback, and personalized summary synthesis.
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from engine.session import Session, session_manager
from engine.matcher import match_user_text_to_option
from engine.summary import generate_personalized_summary
from engine.validator import validate_tree_dict, load_sources


class TreeEngine:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        self.data_dir = data_dir
        self.trees_dir = os.path.join(data_dir, "trees")
        self.sources_path = os.path.join(data_dir, "sources.json")
        self.trees: Dict[str, Dict[str, Any]] = {}
        self.sources: Dict[str, Any] = {}
        self.load_all()

    def load_all(self):
        """Loads all hazard decision trees and official sources."""
        if os.path.exists(self.sources_path):
            with open(self.sources_path, "r", encoding="utf-8") as f:
                self.sources = json.load(f)

        valid_source_ids = {s["id"] for s in self.sources.get("sources", [])}

        if os.path.exists(self.trees_dir):
            for fname in os.listdir(self.trees_dir):
                if fname.endswith(".json"):
                    fpath = os.path.join(self.trees_dir, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        tree_data = json.load(f)
                    hid = tree_data.get("hazard_id")
                    if hid:
                        errs = validate_tree_dict(tree_data, valid_source_ids)
                        if errs:
                            print(f"[WARNING] Tree {hid} validation warnings: {errs}")
                        self.trees[hid] = tree_data

    def get_hazard_list(self, lang: str = "en") -> List[Dict[str, Any]]:
        """Returns metadata for available hazard trees."""
        hazards = []
        for hid, tree in self.trees.items():
            name_dict = tree.get("hazard_name", {})
            hazards.append({
                "id": hid,
                "name": name_dict.get(lang, name_dict.get("en", hid.capitalize())),
                "initial_node": tree.get("initial_node_id")
            })
        return hazards

    def get_tree(self, hazard_id: str) -> Optional[Dict[str, Any]]:
        return self.trees.get(hazard_id)

    def start_conversation(self, hazard_id: str, lang: str = "en") -> Dict[str, Any]:
        """
        Initializes a new session for the specified hazard.
        Returns welcome greeting, initial question, and option pills.
        """
        if hazard_id not in self.trees:
            raise ValueError(f"Hazard '{hazard_id}' not found. Available: {list(self.trees.keys())}")

        tree = self.trees[hazard_id]
        session = session_manager.create_session(hazard_id, lang)
        initial_node_id = tree.get("initial_node_id")
        session.current_node_id = initial_node_id
        session.path_history.append(initial_node_id)

        node = tree["nodes"][initial_node_id]
        # Collect node tags
        for t in node.get("tags", []):
            session.collected_tags.add(t)

        welcome_dict = tree.get("welcome_message", {})
        welcome_text = welcome_dict.get(lang, welcome_dict.get("en", ""))

        node_text_dict = node.get("text", {})
        question_text = node_text_dict.get(lang, node_text_dict.get("en", ""))

        options = self._format_options(node.get("options", []), lang)

        return {
            "status": "success",
            "session_id": session.session_id,
            "hazard_id": hazard_id,
            "lang": lang,
            "welcome_message": welcome_text,
            "current_node_id": initial_node_id,
            "node_type": node.get("type"),
            "severity": node.get("severity", "info"),
            "question": question_text,
            "options": options,
            "is_complete": False,
            "path_history": session.path_history,
            "can_go_back": False
        }

    def process_answer(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        Processes a user choice (by option id, exact label, or free text).
        Chains intermediate advice nodes and returns guidance, next question, or final summary.
        """
        session = session_manager.get_session(session_id)
        if not session:
            return {
                "status": "error",
                "code": "SESSION_EXPIRED",
                "message": "Session expired or invalid. Please restart the assessment."
            }

        tree = self.trees.get(session.hazard_id)
        if not tree:
            return {"status": "error", "message": f"Tree '{session.hazard_id}' not found."}

        curr_node = tree["nodes"].get(session.current_node_id)
        if not curr_node:
            return {"status": "error", "message": f"Current node '{session.current_node_id}' invalid."}

        # 1. Match user input to current options
        options = curr_node.get("options", [])
        matched_option = None

        clean_input = user_input.strip()

        # Check by option ID
        for opt in options:
            if opt.get("id") == clean_input:
                matched_option = opt
                break

        # Check by text or rule-based fuzzy matching
        if not matched_option:
            matched_option = match_user_text_to_option(clean_input, options, lang=session.lang)

        if not matched_option:
            # Fallback: couldn't match input
            node_text = curr_node.get("text", {}).get(session.lang, "")
            return {
                "status": "unmatched",
                "message": "I didn't quite catch that. Please select one of the options below.",
                "session_id": session.session_id,
                "current_node_id": session.current_node_id,
                "question": node_text,
                "options": self._format_options(options, session.lang),
                "is_complete": False,
                "can_go_back": len(session.step_history) > 0
            }

        # Save snapshot for UNDO / BACK
        session.step_history.append(session.snapshot())

        # Record answer
        opt_text = matched_option.get("text", {}).get(session.lang, clean_input)
        session.answers.append({
            "node_id": session.current_node_id,
            "option_id": matched_option.get("id"),
            "option_text": opt_text
        })

        target_node_id = matched_option.get("next_node")
        advice_chain: List[Dict[str, Any]] = []

        # Traverse target node, auto-advancing through advice nodes
        while target_node_id:
            session.path_history.append(target_node_id)
            nxt_node = tree["nodes"].get(target_node_id)
            if not nxt_node:
                break

            for t in nxt_node.get("tags", []):
                session.collected_tags.add(t)

            ntype = nxt_node.get("type")

            if ntype == "advice":
                adv_text = nxt_node.get("text", {}).get(session.lang, nxt_node.get("text", {}).get("en", ""))
                advice_chain.append({
                    "id": target_node_id,
                    "text": adv_text,
                    "severity": nxt_node.get("severity", "info"),
                    "source_id": nxt_node.get("source_id"),
                    "tags": nxt_node.get("tags", [])
                })
                target_node_id = nxt_node.get("next_node")

            elif ntype in ("question", "emergency_check"):
                session.current_node_id = target_node_id
                q_text = nxt_node.get("text", {}).get(session.lang, nxt_node.get("text", {}).get("en", ""))
                opts = self._format_options(nxt_node.get("options", []), session.lang)
                return {
                    "status": "success",
                    "session_id": session.session_id,
                    "user_selection": opt_text,
                    "advice": advice_chain,
                    "current_node_id": target_node_id,
                    "node_type": ntype,
                    "severity": nxt_node.get("severity", "info"),
                    "question": q_text,
                    "options": opts,
                    "is_complete": False,
                    "path_history": session.path_history,
                    "can_go_back": True
                }

            elif ntype == "summary":
                session.current_node_id = target_node_id
                summary = generate_personalized_summary(
                    session.hazard_id,
                    list(session.collected_tags),
                    session.answers,
                    lang=session.lang
                )
                session_manager.mark_completed(session.session_id, summary)

                sum_text = nxt_node.get("text", {}).get(session.lang, "")
                return {
                    "status": "success",
                    "session_id": session.session_id,
                    "user_selection": opt_text,
                    "advice": advice_chain,
                    "current_node_id": target_node_id,
                    "node_type": "summary",
                    "severity": "info",
                    "message": sum_text,
                    "summary": summary,
                    "is_complete": True,
                    "path_history": session.path_history,
                    "can_go_back": True
                }

        return {"status": "error", "message": "Encountered terminal state without summary."}

    def go_back(self, session_id: str) -> Dict[str, Any]:
        """Reverts the last step and returns the previous question state."""
        session = session_manager.get_session(session_id)
        if not session or not session.step_history:
            return {
                "status": "error",
                "message": "Cannot undo further. Already at start of assessment."
            }

        prev_session = session_manager.pop_step(session_id)
        if not prev_session:
            return {"status": "error", "message": "Failed to restore previous step."}

        tree = self.trees.get(prev_session.hazard_id)
        node = tree["nodes"].get(prev_session.current_node_id)
        q_text = node.get("text", {}).get(prev_session.lang, "")
        opts = self._format_options(node.get("options", []), prev_session.lang)

        return {
            "status": "success",
            "session_id": prev_session.session_id,
            "current_node_id": prev_session.current_node_id,
            "node_type": node.get("type"),
            "severity": node.get("severity", "info"),
            "question": q_text,
            "options": opts,
            "is_complete": False,
            "path_history": prev_session.path_history,
            "can_go_back": len(prev_session.step_history) > 0
        }

    def restart_conversation(self, session_id: str) -> Dict[str, Any]:
        """Restarts the conversation for the current session's hazard."""
        session = session_manager.get_session(session_id)
        hazard_id = session.hazard_id if session else "flood"
        lang = session.lang if session else "en"
        return self.start_conversation(hazard_id, lang)

    def _format_options(self, options: List[Dict[str, Any]], lang: str) -> List[Dict[str, str]]:
        formatted = []
        for opt in options:
            text_dict = opt.get("text", {})
            opt_text = text_dict.get(lang, text_dict.get("en", ""))
            formatted.append({
                "id": opt.get("id"),
                "text": opt_text
            })
        return formatted


# Singleton Engine Instance
tree_engine = TreeEngine()

