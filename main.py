from flask import Flask, request, jsonify
import os
import requests
from urllib.parse import quote_plus

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"  # We'll use a free proxy for search

# Free Google Custom Search (use a free proxy like SerpAPI free tier or direct)
# Note: For true free, we'll use a simple DuckDuckGo proxy (no key needed)
def search_google(query):
    try:
        # Free DuckDuckGo API proxy (no key, 1000s of searches/day free)
        search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(search_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("Abstract"):
                return data["Abstract"] + " (Source: DuckDuckGo)"
            elif data.get("RelatedTopics"):
                return data["RelatedTopics"][0].get("Text", "No results found") + " (Source: DuckDuckGo)"
        return "No search results available."
    except:
        return "Search failed — using internal knowledge."

# Memory per player
conversations = {}

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        user_id = data.get("userId", "unknown")

        if not user_message:
            return jsonify({"reply": "Say something!"})

        # Load history
        history = conversations.get(user_id, [])
        history.append({"role": "user", "content": user_message})
        if len(history) > 20:
            history = history[-20:]

        # Check if message needs search (keywords like "search", "current", "what is", "who is")
        needs_search = any(word in user_message.lower() for word in ["search", "current", "today", "weather", "news", "who is", "what is"])
        search_results = ""
        if needs_search:
            search_results = search_google(user_message)
            # Feed search to Gemini as system prompt
            system_prompt = f"Use this search info: {search_results}\n\nRespond based on this and your knowledge."
            history.insert(0, {"role": "system", "content": system_prompt})

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
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({"reply": f"API error: {response.status_code}"}), 500

        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Add AI reply to history
        history.append({"role": "model", "content": reply})
        conversations[user_id] = history

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
