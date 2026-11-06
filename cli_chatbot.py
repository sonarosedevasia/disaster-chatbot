#!/usr/bin/env python3
"""
DisasterSafe CLI Chatbot
Terminal interactive interface for multi-hazard safety guidance.
Runs the exact same rule-based decision tree engine as the web application.
"""

import sys
import argparse
from engine.tree_engine import tree_engine

# ANSI Terminal Colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"


def print_banner():
    print(f"\n{BLUE}{BOLD}========================================================================{RESET}")
    print(f"{CYAN}{BOLD}   SafeKerala / DisasterSafe – Multi-Hazard Safety Guidance CLI{RESET}")
    print(f"{BLUE}   Official Disaster Protocols (NDMA & KSDMA) • Offline Ready{RESET}")
    print(f"{BLUE}{BOLD}========================================================================{RESET}\n")


def select_hazard_and_lang(cli_hazard=None, cli_lang=None):
    valid_hazards = {"flood", "earthquake", "landslide"}
    valid_langs = {"en", "ml", "hi"}

    if cli_hazard and cli_hazard.lower() in valid_hazards:
        hazard_id = cli_hazard.lower()
    else:
        print(f"{BOLD}Select Hazard Type:{RESET}")
        print("  [1] Flood Emergency (വെള്ളപ്പൊക്കം / बाढ़)")
        print("  [2] Earthquake Safety (ഭൂകമ്പം / भूकंप)")
        print("  [3] Landslide Hazard (ഉരുൾപൊട്ടൽ / भूस्खलन)")
        h_choice = input(f"\nEnter choice [1-3, default 1]: {RESET}").strip()
        h_map = {"1": "flood", "2": "earthquake", "3": "landslide"}
        hazard_id = h_map.get(h_choice, "flood")

    if cli_lang and cli_lang.lower() in valid_langs:
        lang = cli_lang.lower()
    else:
        print(f"\n{BOLD}Select Language / ഭാഷ തിരഞ്ഞെടുക്കുക:{RESET}")
        print("  [1] English")
        print("  [2] Malayalam (മലയാളം)")
        print("  [3] Hindi (हिन्दी)")
        l_choice = input(f"\nEnter language [1-3, default 1]: {RESET}").strip()
        l_map = {"1": "en", "2": "ml", "3": "hi"}
        lang = l_map.get(l_choice, "en")

    return hazard_id, lang


def run_cli(hazard_override=None, lang_override=None):
    print_banner()
    hazard_id, lang = select_hazard_and_lang(hazard_override, lang_override)

    state = tree_engine.start_conversation(hazard_id, lang=lang)
    session_id = state["session_id"]

    print(f"\n{CYAN}{BOLD}[BOT]{RESET} {state['welcome_message']}\n")

    while not state.get("is_complete"):
        # Print Question
        print(f"{BLUE}{BOLD}[BOT]{RESET} {BOLD}{state['question']}{RESET}")
        options = state.get("options", [])
        for idx, opt in enumerate(options, 1):
            print(f"  [{idx}] {opt['text']}")

        print(f"\n{YELLOW}(Options: Enter 1-{len(options)}, type your answer, 'b' to go back, 'r' to restart, 'q' to quit){RESET}")
        user_input = input(f"{GREEN}{BOLD}[YOU]{RESET} > ").strip()

        if user_input.lower() in ("q", "quit", "exit"):
            print("\nExiting DisasterSafe CLI. In life-threatening emergencies, dial 112 immediately.\n")
            sys.exit(0)

        if user_input.lower() == "r":
            print(f"\n{YELLOW}Restarting assessment...{RESET}\n")
            state = tree_engine.restart_conversation(session_id)
            session_id = state["session_id"]
            continue

        if user_input.lower() == "b":
            back_state = tree_engine.go_back(session_id)
            if back_state.get("status") == "success":
                print(f"\n{YELLOW}Reverted to previous question.{RESET}\n")
                state = back_state
                continue
            else:
                print(f"\n{RED}{back_state.get('message')}{RESET}\n")
                continue

        # Convert index to option ID or use raw text
        choice = user_input
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(options):
                choice = options[idx]["id"]

        state = tree_engine.process_answer(session_id, choice)

        if state.get("status") == "unmatched":
            print(f"\n{RED}{state['message']}{RESET}\n")
            continue

        # Print Advice Chain
        advice_list = state.get("advice", [])
        if advice_list:
            print()
            for adv in advice_list:
                sev = adv.get("severity", "info")
                if sev == "critical":
                    prefix = f"{RED}{BOLD}⚠ CRITICAL SAFETY ACTION:{RESET}"
                elif sev == "warning":
                    prefix = f"{YELLOW}{BOLD}⚡ ADVISORY PRECAUTION:{RESET}"
                else:
                    prefix = f"{BLUE}{BOLD}ℹ GUIDANCE:{RESET}"
                print(f"{prefix} {adv['text']}")
            print()

    # Final Summary Screen
    summary = state.get("summary", {})
    print(f"\n{BLUE}{BOLD}========================================================================{RESET}")
    print(f"{CYAN}{BOLD}              PERSONALIZED DISASTER SAFETY PLAN{RESET}")
    print(f"{BLUE}{BOLD}========================================================================{RESET}")
    risk = summary.get("risk_level", "MODERATE")
    risk_color = RED if "CRITICAL" in risk else (YELLOW if "HIGH" in risk else GREEN)
    print(f"ASSESSMENT STATUS : {risk_color}{BOLD}{risk}{RESET}")
    print(f"HAZARD EVALUATED  : {BOLD}{summary.get('hazard_id', '').upper()}{RESET}\n")

    immed = summary.get("immediate_actions", [])
    if immed:
        print(f"{RED}{BOLD}⚡ IMMEDIATE PRIORITY ACTIONS:{RESET}")
        for act in immed:
            print(f"  • {act}")
        print()

    nexts = summary.get("next_steps", [])
    if nexts:
        print(f"{CYAN}{BOLD}✓ NEXT STEPS & MITIGATION:{RESET}")
        for step in nexts:
            print(f"  • {step}")
        print()

    prep = summary.get("preparation", [])
    if prep:
        print(f"{YELLOW}{BOLD}🎒 PREPARATION & PACKING:{RESET}")
        for item in prep:
            print(f"  • {item}")
        print()

    print(f"{BOLD}EMERGENCY RESCUE HELPLINES (INDIA):{RESET}")
    for num, desc in summary.get("emergency_numbers", {}).items():
        print(f"  • {RED}{BOLD}{num}{RESET} : {desc}")
    print()

    print(f"{YELLOW}{summary.get('disclaimer', '')}{RESET}")
    print(f"{BLUE}{BOLD}========================================================================{RESET}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SafeKerala / DisasterSafe CLI – Rule-Based Multi-Hazard Emergency Safety Assistant"
    )
    parser.add_argument(
        "--hazard",
        choices=["flood", "earthquake", "landslide"],
        help="Preselect hazard (flood, earthquake, landslide)",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "ml", "hi"],
        help="Preselect language (en=English, ml=Malayalam, hi=Hindi)",
    )
    parser.add_argument(
        "--list-hazards",
        action="store_true",
        help="List all supported hazards and exits",
    )

    args = parser.parse_args()

    if args.list_hazards:
        print_banner()
        print("Supported Disaster Hazards:")
        for h in tree_engine.get_hazard_list():
            print(f"  • {h['id'].upper()}: {h['name']}")
        sys.exit(0)

    try:
        run_cli(hazard_override=args.hazard, lang_override=args.lang)
    except (KeyboardInterrupt, EOFError):
        print("\nSession ended. Stay safe! Dial 112 in life-threatening emergencies.")
        sys.exit(0)

