"""
Script to generate high-fidelity UI preview screenshots for SafeKerala.
Produces crisp PNG graphics for desktop and mobile views in docs/screenshots/.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False):
    try:
        # Try Windows standard fonts
        font_name = "segoeuib.ttf" if bold else "segoeui.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            font_name = "arialbd.ttf" if bold else "arial.ttf"
            return ImageFont.truetype(font_name, size)
        except Exception:
            return ImageFont.load_default()

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def generate_desktop_chat(out_path: str):
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), "#0f172a") # Dark navy background
    draw = ImageDraw.Draw(img)

    # 1. Top emergency bar
    draw.rectangle([(0, 0), (w, 38)], fill="#dc2626")
    font_sm_b = get_font(13, bold=True)
    draw.text((30, 11), "EMERGENCY HELPLINES: National 112 | Kerala SEOC 1070 | District Control 1077 | Ambulance 108", fill="#ffffff", font=font_sm_b)
    draw.text((w - 220, 11), "OFFLINE READY (PWA)", fill="#fef08a", font=font_sm_b)

    # 2. Main Navigation
    draw.rectangle([(0, 38), (w, 98)], fill="#1e293b")
    font_logo = get_font(22, bold=True)
    draw.text((30, 52), "SafeKerala / DisasterSafe", fill="#38bdf8", font=font_logo)
    
    font_nav = get_font(14, bold=False)
    nav_items = ["Emergency Chat", "Interactive Tree", "Disaster Kit", "Quiz", "Official Sources"]
    nx = 380
    for i, item in enumerate(nav_items):
        active = (i == 0)
        col = "#ffffff" if active else "#94a3b8"
        draw.text((nx, 58), item, fill=col, font=font_nav)
        if active:
            draw.line([(nx, 80), (nx + 100, 80)], fill="#38bdf8", width=3)
        nx += 140

    # Language toggle & theme
    draw_rounded_rect(draw, [(w - 180, 52), (w - 30, 84)], 6, fill="#334155")
    draw.text((w - 165, 59), "English | മലയാളം | हिंदी", fill="#cbd5e1", font=get_font(12, bold=True))

    # 3. Main Chat Container (Card Layout)
    draw_rounded_rect(draw, [(180, 118), (1100, 760)], 12, fill="#1e293b", outline="#334155", width=1)
    
    # Chat card header
    draw_rounded_rect(draw, [(180, 118), (1100, 178)], 12, fill="#0f172a")
    draw.text((210, 134), "FLOOD SAFETY GUIDANCE ASSISTANT", fill="#38bdf8", font=get_font(16, bold=True))
    draw_rounded_rect(draw, [(950, 132), (1070, 162)], 6, fill="#166534")
    draw.text((965, 139), "ACTIVE SESSION", fill="#bbf7d0", font=get_font(11, bold=True))

    # Chat message 1: Bot welcome
    draw_rounded_rect(draw, [(210, 198), (920, 268)], 8, fill="#334155")
    draw.text((230, 210), "FloodSafe Emergency Assistant", fill="#38bdf8", font=get_font(12, bold=True))
    draw.text((230, 232), "Welcome to FloodSafe. I will guide you through safety actions based on your situation.", fill="#f8fafc", font=get_font(14))

    # Chat message 2: User answer
    draw_rounded_rect(draw, [(680, 280), (1070, 330)], 8, fill="#0284c7")
    draw.text((700, 294), "Location: Indoors (at home/building)", fill="#ffffff", font=get_font(14, bold=True))

    # Chat message 3: Bot advice & Question
    draw_rounded_rect(draw, [(210, 345), (1000, 485)], 8, fill="#334155")
    draw_rounded_rect(draw, [(230, 358), (340, 380)], 4, fill="#b91c1c")
    draw.text((242, 362), "CRITICAL ACTION", fill="#ffffff", font=get_font(10, bold=True))
    draw.text((230, 390), "Move immediately to higher floors or safe elevated ground.", fill="#f8fafc", font=get_font(14, bold=True))
    draw.text((230, 415), "- Do NOT touch electrical switches, breakers, or appliances if water is nearby.", fill="#e2e8f0", font=get_font(13))
    draw.text((230, 435), "- Avoid ground floor and basements entirely. Keep emergency supplies at hand.", fill="#e2e8f0", font=get_font(13))
    draw.text((230, 460), "Source: NDMA Flood Guidelines Sec 4.2 | KSDMA Orange Book", fill="#94a3b8", font=get_font(11))

    # Chat message 4: Question with options
    draw_rounded_rect(draw, [(210, 500), (900, 560)], 8, fill="#334155")
    draw.text((230, 515), "Question: Is floodwater entering your house?", fill="#f8fafc", font=get_font(15, bold=True))

    # Interactive Option Buttons
    draw_rounded_rect(draw, [(230, 575), (420, 625)], 8, fill="#dc2626") # Yes
    draw.text((290, 590), "Yes (Water Entering)", fill="#ffffff", font=get_font(13, bold=True))

    draw_rounded_rect(draw, [(440, 575), (630, 625)], 8, fill="#475569") # No
    draw.text((505, 590), "No (Dry Inside)", fill="#ffffff", font=get_font(13, bold=True))

    # Chat Footer Action Controls
    draw.line([(180, 690), (1100, 690)], fill="#334155", width=1)
    draw_rounded_rect(draw, [(210, 705), (320, 745)], 6, fill="#475569")
    draw.text((235, 718), "Back (Undo)", fill="#f8fafc", font=get_font(13, bold=True))

    draw_rounded_rect(draw, [(335, 705), (445, 745)], 6, fill="#475569")
    draw.text((360, 718), "Restart Chat", fill="#f8fafc", font=get_font(13, bold=True))

    draw_rounded_rect(draw, [(460, 705), (610, 745)], 6, fill="#0369a1")
    draw.text((480, 718), "Download Checklist", fill="#f8fafc", font=get_font(13, bold=True))

    draw_rounded_rect(draw, [(920, 705), (1070, 745)], 6, fill="#dc2626")
    draw.text((945, 718), "Call 112 SOS", fill="#ffffff", font=get_font(14, bold=True))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"Generated: {out_path}")


def generate_mobile_chat(out_path: str):
    w, h = 390, 844
    img = Image.new("RGB", (w, h), "#0f172a")
    draw = ImageDraw.Draw(img)

    # 1. Mobile status & emergency bar
    draw.rectangle([(0, 0), (w, 44)], fill="#dc2626")
    draw.text((15, 14), "EMERGENCY: 112 | 1070 | 1077", fill="#ffffff", font=get_font(11, bold=True))
    draw_rounded_rect(draw, [(w - 75, 8), (w - 12, 36)], 4, fill="#b91c1c")
    draw.text((w - 65, 14), "CALL 112", fill="#ffffff", font=get_font(11, bold=True))

    # 2. Header
    draw.rectangle([(0, 44), (w, 100)], fill="#1e293b")
    draw.text((15, 58), "SafeKerala", fill="#38bdf8", font=get_font(18, bold=True))
    draw.text((15, 80), "Flood Safety Guidance", fill="#94a3b8", font=get_font(11))
    draw_rounded_rect(draw, [(w - 70, 56), (w - 15, 86)], 6, fill="#334155")
    draw.text((w - 58, 64), "മലയാളം", fill="#cbd5e1", font=get_font(11, bold=True))

    # 3. Chat stream
    # Bot message
    draw_rounded_rect(draw, [(15, 115), (w - 30, 200)], 8, fill="#1e293b", outline="#334155")
    draw.text((25, 125), "FloodSafe Bot", fill="#38bdf8", font=get_font(11, bold=True))
    draw.text((25, 145), "Where are you currently located?", fill="#ffffff", font=get_font(14, bold=True))
    draw.text((25, 170), "Select your current physical situation:", fill="#94a3b8", font=get_font(11))

    # User answer
    draw_rounded_rect(draw, [(w - 240, 215), (w - 15, 260)], 8, fill="#0284c7")
    draw.text((w - 225, 228), "Indoors (at home/building)", fill="#ffffff", font=get_font(12, bold=True))

    # Bot advice
    draw_rounded_rect(draw, [(15, 275), (w - 15, 420)], 8, fill="#1e293b", outline="#ef4444")
    draw_rounded_rect(draw, [(25, 285), (120, 305)], 4, fill="#b91c1c")
    draw.text((32, 289), "SAFETY ACTION", fill="#ffffff", font=get_font(9, bold=True))
    draw.text((25, 315), "Move to higher floors immediately.", fill="#ffffff", font=get_font(13, bold=True))
    draw.text((25, 340), "Switch off power ONLY if dry.\nNever walk through moving water.", fill="#e2e8f0", font=get_font(11))
    draw.text((25, 385), "Source: NDMA Flood Manual 4.2", fill="#94a3b8", font=get_font(9))

    # Bot question
    draw_rounded_rect(draw, [(15, 435), (w - 15, 510)], 8, fill="#1e293b", outline="#334155")
    draw.text((25, 450), "Is floodwater entering your home?", fill="#ffffff", font=get_font(13, bold=True))
    draw.text((25, 478), "Please choose one:", fill="#94a3b8", font=get_font(11))

    # Options buttons (Full width mobile pills)
    draw_rounded_rect(draw, [(15, 525), (w - 15, 575)], 8, fill="#dc2626")
    draw.text((120, 542), "Yes - Water Entering", fill="#ffffff", font=get_font(13, bold=True))

    draw_rounded_rect(draw, [(15, 585), (w - 15, 635)], 8, fill="#334155")
    draw.text((135, 602), "No - Interior Dry", fill="#ffffff", font=get_font(13, bold=True))

    # Quick action bar
    draw_rounded_rect(draw, [(15, 650), (w - 15, 700)], 8, fill="#0369a1")
    draw.text((100, 667), "View Current Summary", fill="#ffffff", font=get_font(12, bold=True))

    # Mobile bottom bar
    draw.rectangle([(0, 770), (w, 844)], fill="#1e293b")
    draw.line([(0, 770), (w, 770)], fill="#334155", width=1)
    draw.text((30, 795), "Chat", fill="#38bdf8", font=get_font(11, bold=True))
    draw.text((120, 795), "Flowchart", fill="#94a3b8", font=get_font(11))
    draw.text((215, 795), "Kit 72h", fill="#94a3b8", font=get_font(11))
    draw.text((310, 795), "Quiz", fill="#94a3b8", font=get_font(11))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"Generated: {out_path}")


def generate_desktop_home(out_path: str):
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), "#0f172a")
    draw = ImageDraw.Draw(img)

    # Top emergency bar
    draw.rectangle([(0, 0), (w, 38)], fill="#dc2626")
    draw.text((30, 11), "EMERGENCY HELPLINES: 112 (National) | 1070 (SEOC) | 1077 (District) | 108 (Ambulance)", fill="#ffffff", font=get_font(13, bold=True))
    draw.text((w - 220, 11), "OFFLINE READY (PWA)", fill="#fef08a", font=get_font(13, bold=True))

    # Main Navigation
    draw.rectangle([(0, 38), (w, 98)], fill="#1e293b")
    draw.text((30, 52), "SafeKerala / DisasterSafe", fill="#38bdf8", font=get_font(22, bold=True))

    # Hero section
    draw.text((30, 130), "Disaster Safety Guidance & Preparedness Portal", fill="#ffffff", font=get_font(26, bold=True))
    draw.text((30, 170), "Evidence-based decision-tree guidance validated by NDMA and KSDMA official protocols.", fill="#94a3b8", font=get_font(14))

    # 3 Hazard Cards
    # Card 1: Flood
    draw_rounded_rect(draw, [(30, 215), (420, 470)], 12, fill="#1e293b", outline="#38bdf8", width=2)
    draw_rounded_rect(draw, [(50, 235), (130, 260)], 4, fill="#0284c7")
    draw.text((58, 240), "PRIMARY", fill="#ffffff", font=get_font(11, bold=True))
    draw.text((50, 275), "Flood Safety (വെള്ളപ്പൊക്കം)", fill="#ffffff", font=get_font(18, bold=True))
    draw.text((50, 310), "Step-by-step guidance for indoor inundation,\noutdoors, vehicle safety, electrical hazards, and\ntrapped emergency rescue protocols.", fill="#cbd5e1", font=get_font(13))
    draw_rounded_rect(draw, [(50, 400), (400, 445)], 8, fill="#0284c7")
    draw.text((150, 415), "Start Flood Guidance ->", fill="#ffffff", font=get_font(13, bold=True))

    # Card 2: Earthquake
    draw_rounded_rect(draw, [(455, 215), (845, 470)], 12, fill="#1e293b", outline="#334155", width=1)
    draw_rounded_rect(draw, [(475, 235), (555, 260)], 4, fill="#ca8a04")
    draw.text((485, 240), "HAZARD", fill="#ffffff", font=get_font(11, bold=True))
    draw.text((475, 275), "Earthquake (ഭൂകമ്പം)", fill="#ffffff", font=get_font(18, bold=True))
    draw.text((475, 310), "Drop-Cover-Hold On protocol, high-rise building\nrules, gas leak detection, coastal tsunami alert,\nand structural aftershock safety.", fill="#cbd5e1", font=get_font(13))
    draw_rounded_rect(draw, [(475, 400), (825, 445)], 8, fill="#334155")
    draw.text((580, 415), "Start Earthquake ->", fill="#ffffff", font=get_font(13, bold=True))

    # Card 3: Landslide
    draw_rounded_rect(draw, [(880, 215), (1250, 470)], 12, fill="#1e293b", outline="#334155", width=1)
    draw_rounded_rect(draw, [(900, 235), (980, 260)], 4, fill="#16a34a")
    draw.text((910, 240), "HAZARD", fill="#ffffff", font=get_font(11, bold=True))
    draw.text((900, 275), "Landslide (ഉരുൾപൊട്ടൽ)", fill="#ffffff", font=get_font(18, bold=True))
    draw.text((900, 310), "Western Ghats early warning signs, slope crack\ndetection, muddy spring discharge, ghat road\ntravel rules, and night evacuation.", fill="#cbd5e1", font=get_font(13))
    draw_rounded_rect(draw, [(900, 400), (1230, 445)], 8, fill="#334155")
    draw.text((1000, 415), "Start Landslide ->", fill="#ffffff", font=get_font(13, bold=True))

    # Quick Emergency Dialers Section
    draw_rounded_rect(draw, [(30, 500), (1250, 750)], 12, fill="#1e293b", outline="#334155", width=1)
    draw.text((55, 520), "KERALA STATE & NATIONAL EMERGENCY CONTACTS (VERIFIED)", fill="#38bdf8", font=get_font(15, bold=True))

    contacts = [
        ("112", "National Emergency Response (All Hazards, Police, Fire, Medical)"),
        ("1070", "Kerala State Emergency Operations Centre (SEOC)"),
        ("1077", "District Disaster Management Authority (DDMA / DEOC)"),
        ("108", "Kerala Free Ambulance Service (KIVIS / GVK-EMRI)"),
        ("1078", "National Disaster Management Authority (NDMA) Control Room"),
    ]
    cy = 555
    for num, desc in contacts:
        draw_rounded_rect(draw, [(55, cy), (125, cy + 30)], 6, fill="#b91c1c")
        draw.text((70, cy + 7), num, fill="#ffffff", font=get_font(12, bold=True))
        draw.text((140, cy + 7), desc, fill="#f1f5f9", font=get_font(13))
        cy += 38

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"Generated: {out_path}")


def generate_desktop_flowchart(out_path: str):
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), "#0f172a")
    draw = ImageDraw.Draw(img)

    # Top header
    draw.rectangle([(0, 0), (w, 38)], fill="#dc2626")
    draw.text((30, 11), "DECISION-TREE LOGIC VISUALIZER: Guaranteed 100% Code-Flowchart Parity", fill="#ffffff", font=get_font(13, bold=True))

    # Main Navigation
    draw.rectangle([(0, 38), (w, 98)], fill="#1e293b")
    draw.text((30, 52), "SafeKerala / Decision Tree Explorer", fill="#38bdf8", font=get_font(22, bold=True))

    # Canvas Card
    draw_rounded_rect(draw, [(30, 118), (1250, 760)], 12, fill="#1e293b", outline="#334155", width=1)
    draw.text((55, 135), "FLOOD SAFETY DECISION-TREE (AUTOMATICALLY GENERATED FROM DATA/TREES/FLOOD.JSON)", fill="#ffffff", font=get_font(14, bold=True))

    # Start Node
    draw_rounded_rect(draw, [(540, 175), (740, 215)], 20, fill="#0284c7")
    draw.text((585, 187), "[START] User Enters", fill="#ffffff", font=get_font(12, bold=True))

    # Down arrow
    draw.line([(640, 215), (640, 250)], fill="#94a3b8", width=2)

    # Decision Node 1: Location
    draw_rounded_rect(draw, [(500, 250), (780, 305)], 8, fill="#475569", outline="#38bdf8", width=2)
    draw.text((525, 268), "{?} Where are you located?", fill="#f8fafc", font=get_font(13, bold=True))

    # 3 Branches
    # Indoors
    draw.line([(550, 305), (280, 350)], fill="#94a3b8", width=2)
    draw.text((360, 315), "Indoors", fill="#38bdf8", font=get_font(11, bold=True))

    # Outdoors
    draw.line([(640, 305), (640, 350)], fill="#94a3b8", width=2)
    draw.text((648, 320), "Outdoors", fill="#38bdf8", font=get_font(11, bold=True))

    # Vehicle
    draw.line([(730, 305), (1000, 350)], fill="#94a3b8", width=2)
    draw.text((880, 315), "In Vehicle", fill="#38bdf8", font=get_font(11, bold=True))

    # Level 2 Nodes
    draw_rounded_rect(draw, [(160, 350), (400, 410)], 8, fill="#334155")
    draw.text((180, 370), "{?} Low-lying area check", fill="#ffffff", font=get_font(12, bold=True))

    draw_rounded_rect(draw, [(520, 350), (760, 410)], 8, fill="#334155")
    draw.text((545, 370), "{?} Floodwater blocking path?", fill="#ffffff", font=get_font(12, bold=True))

    draw_rounded_rect(draw, [(880, 350), (1120, 410)], 8, fill="#334155")
    draw.text((905, 370), "{?} Surrounded by floodwater?", fill="#ffffff", font=get_font(12, bold=True))

    # Level 3: Advice Nodes (Critical Warnings)
    draw_rounded_rect(draw, [(160, 460), (400, 530)], 8, fill="#991b1b")
    draw.text((180, 475), "[!] Move to Higher Floor", fill="#ffffff", font=get_font(12, bold=True))
    draw.text((180, 498), "Never touch wet electricals", fill="#fecaca", font=get_font(11))

    draw_rounded_rect(draw, [(520, 460), (760, 530)], 8, fill="#991b1b")
    draw.text((545, 475), "[!] Turn Around, Don't Drown", fill="#ffffff", font=get_font(12, bold=True))
    draw.text((545, 498), "Seek elevated solid ground", fill="#fecaca", font=get_font(11))

    draw_rounded_rect(draw, [(880, 460), (1120, 530)], 8, fill="#991b1b")
    draw.text((905, 475), "[!] Abandon Vehicle Quickly", fill="#ffffff", font=get_font(12, bold=True))
    draw.text((905, 498), "Climb to roof if surrounded", fill="#fecaca", font=get_font(11))

    # Level 4: Summary Target
    draw_rounded_rect(draw, [(440, 600), (840, 680)], 12, fill="#166534", outline="#22c55e", width=2)
    draw.text((520, 620), "[SUMMARY] Personalized Safety Action Plan", fill="#ffffff", font=get_font(13, bold=True))
    draw.text((470, 645), "Severity Tier + Immediate Checklist + Verified Emergency Contacts", fill="#bbf7d0", font=get_font(11))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    generate_desktop_chat("docs/screenshots/desktop_chat.png")
    generate_mobile_chat("docs/screenshots/mobile_chat.png")
    generate_desktop_home("docs/screenshots/desktop_home.png")
    generate_desktop_flowchart("docs/screenshots/desktop_flowchart.png")

