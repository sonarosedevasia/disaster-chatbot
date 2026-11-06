"""
Pure-Python Rule-Based Text Matcher
Maps free-text user responses to the nearest available decision-tree option
using token scoring, substring matching, and difflib similarity without ML dependencies.
"""

import difflib
import re
import string
from typing import List, Dict, Optional, Tuple, Any


def normalize_text(text: str) -> str:
    """Lowercases, removes standard ASCII punctuation, and normalizes whitespace while preserving Unicode scripts."""
    if not text:
        return ""
    # Strip standard ASCII punctuation without modifying Unicode vowels/matras
    translator = str.maketrans("", "", string.punctuation)
    cleaned = text.lower().translate(translator)
    return " ".join(cleaned.split())


def match_user_text_to_option(user_input: str, options: List[Dict[str, Any]], lang: str = "en", threshold: float = 0.45) -> Optional[Dict[str, Any]]:
    """
    Evaluates user input against a list of options.
    Each option has:
      - 'id': str
      - 'text': {'en': str, 'ml': str, 'hi': str}
    
    Returns the best matching option dict, or None if confidence is below threshold.
    """
    if not user_input or not options:
        return None

    raw_input = user_input.strip()
    norm_input = normalize_text(raw_input)
    if not norm_input:
        return None

    # Check for direct numerical selection (e.g. "1", "option 2", "#3")
    num_match = re.search(r"\b([1-9])\b", norm_input)
    if num_match:
        idx = int(num_match.group(1)) - 1
        if 0 <= idx < len(options):
            return options[idx]

    # Keyword synonyms lookup
    SYNONYMS = {
        "yes": ["yes", "yeah", "yep", "true", "correct", "sure", "അതെ", "ഉണ്ട്", "തീർച്ചയായും", "हाँ", "हा", "सही"],
        "no": ["no", "nope", "false", "never", "അല്ല", "ഇല്ല", "ഒന്നുമില്ല", "नहीं", "ना", "गलत"],
        "indoors": ["indoor", "indoors", "home", "house", "building", "inside", "വീട്", "മുറി", "കെട്ടിടം", "घर", "कमरा", "इमारत"],
        "outdoors": ["outdoor", "outdoors", "outside", "ground", "road", "street", "തുറസ്സായ", "പുറത്ത്", "റോഡ്", "मैदान", "सड़क", "बाहर"],
        "vehicle": ["car", "vehicle", "bus", "bike", "driving", "automobile", "വാഹനം", "കാർ", "വണ്ടി", "गाड़ी", "कार", "वाहन"]
    }

    best_score = 0.0
    best_opt: Optional[Dict[str, Any]] = None

    for idx, opt in enumerate(options):
        opt_text_dict = opt.get("text", {})
        target_text = opt_text_dict.get(lang, opt_text_dict.get("en", ""))
        norm_target = normalize_text(target_text)

        # 1. Exact match check
        if norm_input == norm_target:
            return opt

        # 2. Substring containment check
        if norm_input in norm_target or norm_target in norm_input:
            containment_score = len(norm_input) / max(len(norm_target), 1)
            score = max(0.85, containment_score)
            if score > best_score:
                best_score = score
                best_opt = opt

    # 3. Token-level Synonym matching
    input_tokens = set(norm_input.split())
    syn_scores: Dict[str, int] = {}
    for syn_key, syn_list in SYNONYMS.items():
        syn_set = set(syn_list)
        matched_tokens = input_tokens & syn_set
        if matched_tokens:
            for opt in options:
                opt_id = opt.get("id", "").lower()
                target_str = normalize_text(opt.get("text", {}).get(lang, "") + " " + opt.get("text", {}).get("en", ""))
                # If the syn_key or any matched token is in option id or text
                if syn_key in opt_id or syn_key in target_str or any(tok in target_str for tok in matched_tokens):
                    syn_scores[opt["id"]] = syn_scores.get(opt["id"], 0) + len(matched_tokens)

    if syn_scores:
        best_opt_id = max(syn_scores.items(), key=lambda x: x[1])[0]
        # Find matching option
        for opt in options:
            if opt["id"] == best_opt_id:
                return opt

        # 4. Token overlap (Jaccard similarity)
        input_tokens = set(norm_input.split())
        target_tokens = set(norm_target.split())
        if input_tokens and target_tokens:
            overlap = len(input_tokens & target_tokens)
            jaccard = overlap / len(input_tokens | target_tokens)
            if jaccard > best_score:
                best_score = jaccard
                best_opt = opt

        # 5. difflib SequenceMatcher string similarity
        seq_ratio = difflib.SequenceMatcher(None, norm_input, norm_target).ratio()
        if seq_ratio > best_score:
            best_score = seq_ratio
            best_opt = opt

    if best_score >= threshold and best_opt is not None:
        return best_opt

    return None
