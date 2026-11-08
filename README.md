# DisasterSafe (SafeKerala) – Multi-Hazard Disaster Safety Assistant

A rule-based, multilingual disaster safety assistant that guides people through floods, earthquakes and landslides using interactive decision trees and safety instructions based on NDMA and KSDMA guidance.

## Project Overview

DisasterSafe asks a user a few simple questions about their situation (for example, "Are you indoors or outdoors?") and gives different safety instructions depending on the answers. The advice comes from a deterministic decision-tree engine, with no AI model and no paid API, so the same answers always give the same guidance.

The content follows guidance from the National Disaster Management Authority (NDMA) and the Kerala State Disaster Management Authority (KSDMA). Flood is the primary hazard. Earthquake and Landslide are included as additional hazards.

## Key Features

- **Multi-Hazard Support:** Flood, Earthquake and Landslide guidance.
- **Interactive Chatbot:** Step-by-step questions with clickable options, Back and Restart buttons, and a personalized safety checklist at the end.
- **Multilingual Chatbot:** English, Malayalam and Hindi.
- **Decision Tree Visualization:** Flowcharts generated from the same JSON files the chatbot uses.
- **Emergency Kit Checklist:** Checkable list of essential supplies.
- **Safety Quiz:** Preparedness questions with explanations.
- **Rainfall Estimate:** Current rainfall for the user's location from Open-Meteo (an estimate, not an official warning).
- **Emergency Helplines:** Quick access to emergency numbers on every page.
- **Accessibility:** Adjustable font size, high-contrast mode and light/dark theme.
- **Installable Web App (PWA):** Offline caching for the chatbot and static assets.

## Technical Highlights

- Data-driven decision-tree engine: each hazard is a JSON file.
- Validator that checks for dead ends, unreachable nodes, cycles and missing sources before the app starts.
- Rule-based free-text matching using Levenshtein distance and synonyms (no external NLP).
- In-memory session management with Back/Undo.
- Flowcharts and sample transcripts generated from the real engine, so they match the code.
- Automated tests for decision paths and safety rules (for example, never advising anyone to walk, swim or drive through floodwater).

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python, Flask |
| Data Storage | JSON files (no database) |
| Testing | Pytest |
| Visualization | Mermaid.js |
| Packaging | Docker, Docker Compose, PWA |

## Project Statistics

| Metric | Result |
|---|---:|
| Supported Hazards | 3 |
| Decision Nodes | 50 |
| Verified Decision Paths | 90 |
| Supported Languages | 3 |
| Automated Tests | 33 |

## Project Structure

```text
disaster-chatbot/
├── app.py                  # Flask web app
├── cli_chatbot.py          # Terminal version of the chatbot
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── data/
│   └── trees/              # flood.json, earthquake.json, landslide.json
├── engine/                 # Decision-tree engine, validator, matcher, sessions
├── static/                 # CSS, JavaScript, icons, service worker
├── templates/              # HTML pages
├── tests/                  # Automated tests
├── tools/                  # Flowchart and transcript generators
├── docs/                   # Flowcharts, transcripts, architecture notes
├── flowchart.mmd           # Primary (flood) flowchart source
├── sample_transcript.txt   # Sample conversation (flood)
└── LICENSE
```

## Installation and Execution

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd YOUR_REPOSITORY_FOLDER
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the web app

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

### 5. Or run the terminal version

```bash
python cli_chatbot.py
```

## Run Tests

```bash
python -m pip install pytest
python -m pytest -v tests/
```

## How the Decision Tree Works

Each hazard is stored as a JSON tree of nodes (questions, advice and summaries). Every option points to the next node. The engine follows the user's answers through the tree, collects tags along the way, and builds a final checklist with the most urgent actions first.

Flood example: Where are you? → Indoors / Outdoors / Inside a vehicle → follow-up questions for that branch → "Are you injured or trapped?" → personalized safety summary with emergency numbers.

Run `python tools/generate_flowchart.py` to regenerate the flowcharts from the JSON, and `python tools/generate_transcript.py` to regenerate the sample transcripts from the real engine.

## Limitations

- Malayalam and Hindi are available in the chatbot (questions, advice and summary). Other pages are English only. Translations are machine-generated and should be reviewed by a native speaker before real-world use.
- Offline caching covers the chatbot and static assets. The flowchart page may need internet if Mermaid loads from a CDN.
- The rainfall card shows an estimate from Open-Meteo, not an official warning. Check IMD and KSDMA for official alerts.
- The project is rule-based, so it can only respond to situations covered by its decision trees.
- Emergency numbers should be verified on official sources before real-world use.

## Official References

- [National Disaster Management Authority (NDMA)](https://ndma.gov.in/)
- [Kerala State Disaster Management Authority (KSDMA)](https://sdma.kerala.gov.in/)
- [Emergency Response Support System – 112](https://112.gov.in/)
- [India Meteorological Department (IMD)](https://mausam.imd.gov.in/)

The full list of sources with access dates is in `data/sources.json` and on the Sources & Protocols page of the app.

## Disclaimer

This project is developed for academic and educational purposes. It provides disaster safety guidance but does not replace emergency services, official instructions, professional rescue services or directions from local authorities. In an emergency, call 112.

## License

MIT License. See the `LICENSE` file.