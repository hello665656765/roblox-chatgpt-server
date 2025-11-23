from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# This automatically uses the secret key you set in Render (100% safe)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"reply": "Please type something!"}), 200
            
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message}],
            max_tokens=500
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
        
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

# This keeps Render happy
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
