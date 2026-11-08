# SafeKerala – Multi-Hazard Disaster Safety Assistant

A rule-based, multilingual disaster safety assistant that guides people during floods, earthquakes and landslides through interactive decision trees and verified safety instructions.

## Project Overview

SafeKerala helps people understand what actions to take before, during and after natural disasters. It uses a deterministic decision-tree engine to provide situation-specific safety guidance based on user responses.

The system follows safety protocols and references from the National Disaster Management Authority (NDMA) and Kerala State Disaster Management Authority (KSDMA).

## Key Features

- **Multi-Hazard Support:** Flood, Earthquake and Landslide guidance.
- **Interactive Chatbot:** Step-by-step questions with situation-specific safety instructions.
- **Multilingual Support:** English, Malayalam and Hindi.
- **Decision Tree Visualization:** Interactive flowcharts generated from JSON decision trees.
- **Emergency Kit Builder:** Checklist for preparing essential emergency supplies.
- **Family Emergency Plan:** Helps families prepare emergency contacts and meeting locations.
- **Safety Quiz:** Disaster preparedness questions with explanations.
- **Live Insights:** Anonymous chatbot usage statistics.
- **Progressive Web App:** Installable website with offline caching for core chatbot features.
- **Emergency Helplines:** Quick access to important emergency numbers.

## Technical Highlights

- Data-driven decision-tree engine using JSON.
- Rule-based text matching with Levenshtein distance and synonyms.
- Advice chaining for delivering urgent instructions without unnecessary steps.
- Graph validation to detect unreachable nodes, cycles and dead ends.
- In-memory session management with back/undo functionality.
- Automated testing of decision paths and safety rules.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python, Flask |
| Data Storage | JSON |
| Testing | Pytest |
| Visualization | Mermaid.js |
| Deployment | Docker, Docker Compose, PWA |

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
SafeKerala/
├── app.py
├── cli_chatbot.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── data/
│   └── trees/
├── engine/
├── static/
├── templates/
├── tests/
├── tools/
├── docs/
├── flowchart.mmd
├── README.md
└── LICENSE
```

## Installation and Execution

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd SafeKerala
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

Open your browser at:

`http://127.0.0.1:5000`

## Run Tests

```bash
pytest -v tests/
```

## Official References

- [National Disaster Management Authority (NDMA)](https://ndma.gov.in/)
- [Kerala State Disaster Management Authority (KSDMA)](https://sdma.kerala.gov.in/)
- [Emergency Response Support System – 112](https://112.gov.in/)

## Disclaimer

This project is developed for academic and educational purposes. It provides disaster safety guidance but does not replace official emergency instructions, professional rescue services or directions from local authorities.

