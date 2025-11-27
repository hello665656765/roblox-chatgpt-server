from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

conversations = {}

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        user_message = data.get("message", "").strip()
        user_id = str(data.get("userId", "unknown"))

        if not user_message:
            return jsonify({"reply": "Say something!"})

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

        response = requests.post(f"{URL}?key={GEMINI_API_KEY}", json=payload, timeout=30)
        
        if response.status_code != 200:
            return jsonify({"reply": f"Gemini error {response.status_code}"}), 500

        full_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Force Roblox 190-char limit + never cut mid-sentence
        MAX = 190
        if len(full_reply) <= MAX:
            final_reply = full_reply
        else:
            cut = MAX
            while cut > 100 and full_reply[cut] not in " .,!?\n":
                cut -= 1
            if cut <= 100:
                cut = MAX
            final_reply = full_reply[:cut].rstrip(" .,?!") + "…"

        # Save full reply for memory, send short one to Roblox
        history.append({"role": "model", "parts": [{"text": full_reply}]})
        conversations[user_id] = history

        return jsonify({"reply": final_reply})

    except Exception as e:
        return jsonify({"reply": "Backend error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
