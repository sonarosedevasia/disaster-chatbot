"""
DisasterSafe Personalized Summary Generator
Synthesizes user session tags, choices, and path into an ordered, severity-ranked
disaster safety plan with immediate actions, preparation, and communication guidelines.
"""

from typing import Dict, List, Any


def generate_personalized_summary(hazard_id: str, tags: List[str], answers: List[Dict[str, Any]], lang: str = "en") -> Dict[str, Any]:
    """
    Builds a personalized emergency safety plan.
    Outputs:
      - risk_level: "CRITICAL EMERGENCY" | "HIGH RISK" | "MODERATE"
      - immediate_actions: List of highest priority immediate life-safety actions
      - next_steps: Practical step-by-step guidance
      - preparation: Emergency packing and utility mitigation
      - communication: Rescue signaling and contact protocols
      - emergency_numbers: Verified helplines
      - disclaimer: Official disclaimer
    """
    is_critical = any(t in tags for t in [
        "call_emergency_112", "water_ingress", "riverbank_danger",
        "abandon_vehicle", "tsunami_evacuation", "trapped_rubble",
        "perpendicular_evacuation", "gas_leak_protocol"
    ])
    
    is_high_risk = any(t in tags for t in [
        "topography_risk", "turn_around_dont_drown", "outdoor_navigation",
        "highrise_evacuation", "early_warning_detection", "soil_saturation"
    ])

    if is_critical:
        risk_level = "CRITICAL EMERGENCY"
    elif is_high_risk:
        risk_level = "HIGH RISK"
    else:
        risk_level = "MODERATE"

    immediate_actions: List[str] = []
    next_steps: List[str] = []
    preparation: List[str] = []
    communication: List[str] = []

    # 1. Hazard-specific synthesis
    if hazard_id == "flood":
        if "water_ingress" in tags or "immediate_evacuation" in tags:
            immediate_actions.append("Move to highest floor or safe elevated roof area immediately. Do not stay on ground level.")
            immediate_actions.append("Do NOT touch electrical switches or breakers; turn off electricity ONLY if completely dry and safe to do so.")
            next_steps.append("Never wade through indoor or outdoor floodwaters. Hidden hazards and live currents exist.")
        elif "topography_risk" in tags:
            immediate_actions.append("Prepare for rapid evacuation; move critical medications and valuables to higher storeys.")
            next_steps.append("Switch off electricity and gas only if completely dry and safe to do so.")
        else:
            next_steps.append("Stay sheltered indoors if the building structure is sound; avoid unnecessary road travel.")

        if "turn_around_dont_drown" in tags:
            immediate_actions.append("Turn Around, Don't Drown! Just 30 cm of water can float and sweep away vehicles.")
            next_steps.append("Stay clear of drainage canals, culverts, riverbanks, and overflowing streams.")

        if "abandon_vehicle" in tags:
            immediate_actions.append("Abandon your vehicle if safe to exit and move immediately to higher ground.")

        preparation.append("Assemble essential flood kit: 3L drinking water per person, dry food, torch, and power bank.")
        preparation.append("Store identity cards, land records, and deeds in a sealed waterproof pouch.")
        next_steps.append("Boil all drinking water and watch out for displaced snakes or reptiles seeking higher ground.")

    elif hazard_id == "earthquake":
        if "drop_cover_hold" in tags:
            immediate_actions.append("Practice Drop, Cover, and Hold On beneath sturdy furniture until shaking completely ceases.")
            next_steps.append("Stay away from glass windows, unanchored bookcases, mirrors, and ceiling fixtures.")

        if "highrise_evacuation" in tags:
            immediate_actions.append("NEVER use elevators or lifts after an earthquake. Evacuate only via fire-exit stairs.")

        if "gas_leak_protocol" in tags:
            immediate_actions.append("CRITICAL: Do NOT strike matches, use lighters, or operate ANY electric switches (sparks ignite gas).")
            immediate_actions.append("Turn off LPG cylinder regulator if accessible, ventilate rooms, and evacuate outside.")

        if "tsunami_evacuation" in tags:
            immediate_actions.append("URGENT TSUNAMI RISK: Move inland at least 2 km or to elevated terrain above 30 meters elevation.")

        if "trapped_rubble" in tags:
            immediate_actions.append("Cover your nose/mouth with a cloth. Tap rhythmically on pipes/walls to signal rescue teams.")

        preparation.append("Wear sturdy thick-soled shoes immediately to prevent severe lacerations from broken glass.")
        next_steps.append("Be prepared for strong aftershocks. Inspect walls for severe shear cracks before re-entering.")
        communication.append("Use SMS text messages instead of voice calls to keep cellular bandwidth open for rescue operations.")

    elif hazard_id == "landslide":
        if "perpendicular_evacuation" in tags:
            immediate_actions.append("EVACUATE IMMEDIATELY: Run sideways (PERPENDICULAR to the slide path) toward stable elevated ground.")
            immediate_actions.append("NEVER run downslope along the valley channel in the path of the mudflow.")

        if "soil_saturation" in tags:
            immediate_actions.append("Pre-emptively relocate to designated government relief camps before nightfall during heavy downpours.")

        if "ghat_road_safety" in tags:
            immediate_actions.append("Do not park under steep cut-slopes; turn around immediately if mud blocks the roadway.")

        next_steps.append("Stay completely away from the slide zone; secondary landslides occur frequently without warning.")
        preparation.append("Keep a lightweight grab-bag ready with essential medicines, torch, and dry rations.")
        communication.append("Alert District Control Room (1077) if you observe tension cracks widening on hillside slopes.")

    # Universal actions if injured or trapped
    if "call_emergency_112" in tags:
        immediate_actions.insert(0, "DIAL 112 IMMEDIATELY: State your exact location, visible landmarks, and injury status to the dispatcher.")
        communication.append("Conserve phone battery: switch to power-saver mode and use a whistle or torch to signal rescuers.")

    # Fallback guarantees if list is sparse
    if not immediate_actions:
        immediate_actions.append("Follow official NDMA / KSDMA evacuation advisories immediately if issued.")
    if not next_steps:
        next_steps.append("Monitor All India Radio, television, or district collectorate social handles for verified advisories.")

    emergency_numbers = {
        "112": "National Integrated Emergency Helpline (Police, Fire, Medical, Rescue)",
        "1070": "Kerala State Emergency Operations Centre (SEOC, 24x7)",
        "1077": "District Emergency Operations Centre (DEOC - Collectorate Control Room)",
        "108": "Ambulance & Emergency Medical Response",
        "1078": "NDMA National Disaster Control Helpline"
    }

    disclaimer = (
        "Disclaimer: This guidance is based on official National Disaster Management Authority (NDMA) "
        "and Kerala State Disaster Management Authority (KSDMA) protocols. It provides educational and "
        "first-response safety guidance and does not replace emergency rescue services or official civil defense evacuation orders. "
        "In life-threatening situations, dial 112 immediately."
    )

    return {
        "hazard_id": hazard_id,
        "risk_level": risk_level,
        "immediate_actions": immediate_actions,
        "next_steps": next_steps,
        "preparation": preparation,
        "communication": communication,
        "emergency_numbers": emergency_numbers,
        "disclaimer": disclaimer,
        "tags": list(set(tags))
    }
