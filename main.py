from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Store conversation history per player (Roblox UserId as key)
conversations = {}

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        user_id = data.get("userId", "unknown")
        if not user_message:
            return jsonify({"reply": "Say something!"})

        # Load or create history
        history = conversations.get(user_id, [])
        history.append({"role": "user", "parts": [{"text": user_message}]})
        if len(history) > 20:
            history = history[-20:]

        payload = {
            "contents": history,
            "safetySettings": [
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
            ]
        }

        response = requests.post(
            f"{URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({"reply": f"API error: {response.status_code}"}), 500

        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        # ────── FORCE ROBLOX 190-CHAR LIMIT + NEVER CUT MID-SENTENCE ──────
        MAX_CHARS = 190
        if len(reply) <= MAX_CHARS:
            final_reply = reply
        else:
            cut = MAX_CHARS
            while cut > 100 and reply[cut] not in " .,!?\n":
                cut -= 1
            if cut <= 100:
                cut = MAX_CHARS
            final_reply = reply[:cut].rstrip(" .,?!") + "…"

        # Save FULL reply to memory (Gemini remembers everything)
        history.append({"role": "model", "parts": [{"text": reply}]})
        conversations[user_id] = history

        return jsonify({"reply": final_reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
