from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# Put your OpenAI key here (we'll replace it in 1 second)
client = OpenAI(api_key="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")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_message}]
    )
    
    ai_reply = response.choices[0].message.content
    return jsonify({"reply": ai_reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
