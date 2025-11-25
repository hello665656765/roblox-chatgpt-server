from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "No message"}), 400

        payload = {
            "contents": [{"parts": [{"text": user_message}]}]
        }

        response = requests.post(
            f"{URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({"reply": f"Gemini error {response.status_code}"}), 500

        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"reply": reply.strip()})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
