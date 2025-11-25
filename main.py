from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Updated Nov 25, 2025: Free preview model (stable for v1beta)
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "Say something!"})

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_message}
                    ]
                }
            ]
        }

        response = requests.post(
            f"{URL}?key={GEMINI_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({"reply": f"API error: {response.status_code} - {response.text[:200]}..."}), 500

        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
