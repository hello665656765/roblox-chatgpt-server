from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "")
        if not user_message:
            return jsonify({"reply": "Say something!"})

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",  # super fast & free
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7,
            "max_tokens": 500
        }

        response = requests.post(URL, json=data, headers=headers)
        reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
