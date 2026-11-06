"""
SafeKerala / DisasterSafe – Multi-Hazard Safety Guidance System
Flask Application Factory, REST API & Web Routes

Author: DisasterSafe Team
Complies with NDMA (Government of India) & KSDMA Protocols.
"""

import os
import json
from typing import Dict, Any
from flask import (
    Flask, render_template, request, jsonify, make_response, send_from_directory
)
from engine.tree_engine import tree_engine
from engine.session import session_manager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def create_app(test_config: Dict[str, Any] = None) -> Flask:
    """Application factory for DisasterSafe Flask backend."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "disastersafe-kerala-2026-prod-secret"),
        SEND_FILE_MAX_AGE_DEFAULT=31536000
    )

    if test_config:
        app.config.update(test_config)

    # -------------------------------------------------------------------------
    # SECURITY & COMPLIANCE HEADERS
    # -------------------------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), microphone=(self)"
        return response

    # -------------------------------------------------------------------------
    # STATIC HELPER & PWA SERVICE WORKER ROUTES
    # -------------------------------------------------------------------------
    @app.route("/manifest.json")
    def manifest():
        return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")

    @app.route("/sw.js")
    def service_worker():
        response = make_response(send_from_directory("static", "sw.js", mimetype="application/javascript"))
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    # -------------------------------------------------------------------------
    # HTML WEB VIEWS
    # -------------------------------------------------------------------------
    @app.route("/")
    def index_view():
        """Landing Page with Hero, Hazard Cards, Emergency Strip, and Triage."""
        return render_template("index.html")

    @app.route("/chat")
    def chat_view():
        """Interactive Chatbot Interface."""
        hazard = request.args.get("hazard", "flood")
        lang = request.args.get("lang", "en")
        return render_template("chat.html", active_hazard=hazard, active_lang=lang)

    @app.route("/flowchart")
    def flowchart_view():
        """Decision Tree / Flowchart View."""
        hazard = request.args.get("hazard", "flood")
        return render_template("flowchart.html", active_hazard=hazard)

    @app.route("/kit")
    def kit_view():
        """Disaster Emergency Kit Checklist."""
        kits_path = os.path.join(DATA_DIR, "kits.json")
        kits_data = {}
        if os.path.exists(kits_path):
            with open(kits_path, "r", encoding="utf-8") as f:
                kits_data = json.load(f)
        return render_template("kit.html", kits=kits_data)

    @app.route("/plan")
    def plan_view():
        """Family Emergency Plan Builder."""
        return render_template("plan.html")

    @app.route("/quiz")
    def quiz_view():
        """Preparedness Quiz Mode."""
        quiz_path = os.path.join(DATA_DIR, "quizzes.json")
        quiz_data = {}
        if os.path.exists(quiz_path):
            with open(quiz_path, "r", encoding="utf-8") as f:
                quiz_data = json.load(f)
        return render_template("quiz.html", quizzes=quiz_data.get("quizzes", {}))

    @app.route("/insights")
    def insights_view():
        """Privacy-friendly Anonymous Analytics Dashboard."""
        analytics = session_manager.get_analytics()
        return render_template("insights.html", analytics=analytics)

    @app.route("/about")
    def about_view():
        """Sources, Official Protocols, and Verified Contacts."""
        sources_path = os.path.join(DATA_DIR, "sources.json")
        contacts_path = os.path.join(DATA_DIR, "contacts.json")
        myths_path = os.path.join(DATA_DIR, "myths.json")

        sources_data, contacts_data, myths_data = {}, {}, {}
        if os.path.exists(sources_path):
            with open(sources_path, "r", encoding="utf-8") as f:
                sources_data = json.load(f)
        if os.path.exists(contacts_path):
            with open(contacts_path, "r", encoding="utf-8") as f:
                contacts_data = json.load(f)
        if os.path.exists(myths_path):
            with open(myths_path, "r", encoding="utf-8") as f:
                myths_data = json.load(f)

        return render_template(
            "about.html",
            sources=sources_data.get("sources", []),
            contacts=contacts_data,
            myths=myths_data.get("hazards", {})
        )

    # -------------------------------------------------------------------------
    # REST API BLUEPRINT ENDPOINTS
    # -------------------------------------------------------------------------
    @app.route("/api/hazards", methods=["GET"])
    def api_hazards():
        """Returns list of supported disaster hazards."""
        lang = request.args.get("lang", "en")
        return jsonify({
            "status": "success",
            "hazards": tree_engine.get_hazard_list(lang=lang)
        })

    @app.route("/api/start", methods=["POST"])
    def api_start():
        """Initializes a new assessment session."""
        data = request.get_json(force=True, silent=True) or {}
        hazard_id = data.get("hazard_id", "flood")
        lang = data.get("lang", "en")
        try:
            result = tree_engine.start_conversation(hazard_id, lang=lang)
            resp = make_response(jsonify(result))
            resp.set_cookie("ds_session_id", result["session_id"], max_age=86400, httponly=True, samesite="Lax")
            return resp
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/api/answer", methods=["POST"])
    def api_answer():
        """Processes a choice or free-text input through the decision tree."""
        data = request.get_json(force=True, silent=True) or {}
        session_id = data.get("session_id") or request.cookies.get("ds_session_id")
        choice = data.get("choice") or data.get("text") or ""

        if not session_id:
            return jsonify({
                "status": "error",
                "code": "MISSING_SESSION",
                "message": "Missing session identifier. Please start a new session."
            }), 400

        if not choice:
            return jsonify({
                "status": "error",
                "code": "INVALID_INPUT",
                "message": "No answer or selection provided."
            }), 400

        result = tree_engine.process_answer(session_id, choice)
        return jsonify(result)

    @app.route("/api/back", methods=["POST"])
    def api_back():
        """Reverts the last answered question (Undo)."""
        data = request.get_json(force=True, silent=True) or {}
        session_id = data.get("session_id") or request.cookies.get("ds_session_id")

        if not session_id:
            return jsonify({"status": "error", "message": "No active session to undo."}), 400

        result = tree_engine.go_back(session_id)
        return jsonify(result)

    @app.route("/api/restart", methods=["POST"])
    def api_restart():
        """Restarts the active conversation from the beginning."""
        data = request.get_json(force=True, silent=True) or {}
        session_id = data.get("session_id") or request.cookies.get("ds_session_id")

        result = tree_engine.restart_conversation(session_id)
        return jsonify(result)

    @app.route("/api/summary", methods=["GET"])
    def api_summary():
        """Fetches the final personalized summary for a session."""
        session_id = request.args.get("session_id") or request.cookies.get("ds_session_id")
        session = session_manager.get_session(session_id)
        if not session or not session.summary:
            return jsonify({"status": "error", "message": "Summary not yet available for session."}), 404
        return jsonify({"status": "success", "summary": session.summary})

    @app.route("/api/tree/<hazard_id>", methods=["GET"])
    def api_tree_raw(hazard_id: str):
        """Returns the raw JSON tree structure for a hazard."""
        tree = tree_engine.get_tree(hazard_id)
        if not tree:
            return jsonify({"status": "error", "message": "Hazard not found."}), 404
        return jsonify({"status": "success", "tree": tree})

    @app.route("/api/flowchart-data", methods=["GET"])
    def api_flowchart_data():
        """Returns the Mermaid diagram source for the requested hazard."""
        hazard = request.args.get("hazard", "flood")
        mmd_path = os.path.join(BASE_DIR, "docs", "flowcharts", f"{hazard}.mmd")
        if not os.path.exists(mmd_path):
            mmd_path = os.path.join(BASE_DIR, "flowchart.mmd")

        try:
            with open(mmd_path, "r", encoding="utf-8") as f:
                content = f.read()
            return jsonify({"status": "success", "hazard": hazard, "mermaid": content})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/export/<fmt>", methods=["GET"])
    def api_export_summary(fmt: str):
        """Exports the safety plan in plain text or JSON."""
        session_id = request.args.get("session_id") or request.cookies.get("ds_session_id")
        session = session_manager.get_session(session_id)
        if not session or not session.summary:
            return jsonify({"status": "error", "message": "No completed assessment to export."}), 404

        summary = session.summary
        if fmt == "json":
            return jsonify(summary)

        # Plain text format
        lines = [
            "============================================================",
            f"DISASTERSAFE / SAFEKERALA - PERSONALIZED SAFETY PLAN",
            f"HAZARD    : {summary.get('hazard_id', '').upper()}",
            f"RISK LEVEL: {summary.get('risk_level')}",
            "============================================================",
            "",
            "⚡ IMMEDIATE PRIORITY ACTIONS:"
        ]
        for act in summary.get("immediate_actions", []):
            lines.append(f"  • {act}")
        lines.append("")
        lines.append("✓ NEXT STEPS & MITIGATION:")
        for st in summary.get("next_steps", []):
            lines.append(f"  • {st}")
        lines.append("")
        lines.append("🎒 PREPARATION & PACKING:")
        for it in summary.get("preparation", []):
            lines.append(f"  • {it}")
        lines.append("")
        lines.append("📞 EMERGENCY RESCUE HELPLINES:")
        for num, desc in summary.get("emergency_numbers", {}).items():
            lines.append(f"  • {num}: {desc}")
        lines.append("")
        lines.append(f"DISCLAIMER: {summary.get('disclaimer')}")

        text_content = "\n".join(lines)
        response = make_response(text_content)
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename="disastersafe_{summary.get("hazard_id")}_plan.txt"'
        return response

    @app.route("/api/triage", methods=["POST"])
    def api_triage():
        """Quick 2-question triage to route citizen to the right hazard assistant."""
        data = request.get_json(force=True, silent=True) or {}
        phenomenon = data.get("phenomenon", "").lower()
        terrain = data.get("terrain", "").lower()

        if "water" in phenomenon or "rain" in phenomenon or "flood" in phenomenon or "drain" in phenomenon:
            return jsonify({"status": "success", "hazard": "flood"})
        elif "shak" in phenomenon or "tremor" in phenomenon or "vibrat" in phenomenon:
            return jsonify({"status": "success", "hazard": "earthquake"})
        elif "mud" in phenomenon or "slide" in phenomenon or "crack" in phenomenon or "hill" in terrain:
            return jsonify({"status": "success", "hazard": "landslide"})
        else:
            return jsonify({"status": "success", "hazard": "flood"})

    @app.route("/api/feedback", methods=["POST"])
    def api_feedback():
        """Saves anonymous feedback."""
        data = request.get_json(force=True, silent=True) or {}
        feedback_file = os.path.join(DATA_DIR, "feedback.json")
        feedback_entry = {
            "hazard_id": data.get("hazard_id", "unknown"),
            "rating": data.get("rating", "up"),
            "comment": data.get("comment", "").strip()[:500]
        }
        try:
            entries = []
            if os.path.exists(feedback_file):
                with open(feedback_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            entries.append(feedback_entry)
            with open(feedback_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
            return jsonify({"status": "success", "message": "Feedback recorded."})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/health", methods=["GET"])
    def api_health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "DisasterSafe Multi-Hazard Guidance Engine",
            "hazards_loaded": list(tree_engine.trees.keys())
        })

    # Error Handlers
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "code": 404, "message": "Resource not found"}), 404
        return render_template("base.html", error_title="Page Not Found", error_message="The requested disaster advisory page does not exist."), 404

    @app.errorhandler(500)
    def handle_500(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "code": 500, "message": "Internal server error"}), 500
        return render_template("base.html", error_title="Internal System Error", error_message="Our safety protocols remain operational. Please try restarting the page."), 500

    return app


# Default app instance for WSGI / CLI / Direct run
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
