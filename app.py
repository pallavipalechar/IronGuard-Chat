from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
import os
import datetime
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

HARMFUL_KEYWORDS = [
    "bomb",
    "make a bomb",
    "explosive",
    "kill",
    "murder",
    "terrorist",
    "weapon",
    "suicide",
    "poison",
    "hack",
    "illegal",
    "attack",
    "mass killing",
    "chemical weapon",
    "biological weapon",
]


def analyze_risk(text):
    lowered_text = text.lower()

    matched = [
        keyword
        for keyword in HARMFUL_KEYWORDS
        if keyword in lowered_text
    ]

    if not matched:
        return {
            "risk_level": "LOW",
            "blocked": False,
            "matched_keywords": [],
        }

    if len(matched) <= 2:
        return {
            "risk_level": "MEDIUM",
            "blocked": True,
            "matched_keywords": matched,
        }

    return {
        "risk_level": "HIGH",
        "blocked": True,
        "matched_keywords": matched,
    }


def safe_response():
    return "I cannot provide harmful, illegal, or dangerous instructions."


def log_event(user_input, risk):
    with open("security_logs.txt", "a", encoding="utf-8") as file:
        file.write("\n----------------------\n")
        file.write(f"{datetime.datetime.now().isoformat()}\n")
        file.write(f"INPUT: {user_input}\n")
        file.write(f"RISK: {risk}\n")


def generate_response(user_message):
    response = client.models.generate_content(
       model="gemini-2.5-flash",
        contents=user_message
    )
    return response.text


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "IronGuard Chat API is running"})


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "No JSON body received"}), 400

        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        risk = analyze_risk(user_message)

        if risk["blocked"]:
            log_event(user_message, risk)
            return jsonify({
                "response": safe_response(),
                "risk_analysis": risk,
            }), 200

        response = generate_response(user_message)

        return jsonify({
            "response": response,
            "risk_analysis": risk,
        }), 200

    except Exception as error:
        app.logger.exception("Chat endpoint failed")
        return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False,
        use_reloader=False,
        threaded=True,
    )