from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import sys

app = Flask(__name__)

# =============================================
# CONFIGURATION - VERY IMPORTANT
# =============================================
# 1. Go to https://aistudio.google.com/app/apikey
# 2. Create/get your API key (free tier is enough for this)
# 3. In Render dashboard → your service → Environment tab
#    Add: Name = GEMINI_API_KEY   Value = your-key-here
# =============================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable is not set!", file=sys.stderr)
    GEMINI_API_KEY = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API key loaded successfully", file=sys.stderr)

# Recommended model for Jan 2026 – fast, free tier compatible, great for chat
MODEL_NAME = "gemini-2.5-flash"  # Change to "gemini-2.5-pro" if you want smarter replies

model = None
if GEMINI_API_KEY:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        print(f"Model {MODEL_NAME} initialized successfully", file=sys.stderr)
    except Exception as e:
        print(f"Failed to initialize model '{MODEL_NAME}': {e}", file=sys.stderr)

@app.route('/chat', methods=['POST'])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({"error": "Server not configured - missing GEMINI_API_KEY"}), 500
    if model is None:
        return jsonify({"error": "Failed to load Gemini model"}), 500

    try:
        data = request.get_json(force=True)
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field in JSON"}), 400

        user_message = data['message']
        print(f"Received message: {user_message[:100]}...", file=sys.stderr)

        # Generate response with safety filters DISABLED to avoid empty replies
        response = model.generate_content(
    [
        # ← This system prompt is the key
        {"role": "model", "parts": [{
            "text": 
                "You are a helpful, friendly AI named Gemini. "
                "Always reply in clear, natural, complete English sentences. "
                "Finish every thought properly — never cut sentences short. "
                "Use proper grammar and punctuation. "
                "Be concise but thorough, aim for 1-4 full sentences per reply unless asked for more."
        }]},
        
        # The actual user message (player name + their chat)
        {"role": "user", "parts": [{"text": user_message}]}
    ],
    
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,           # keep or lower to 0.6–0.8 for more consistent style
        max_output_tokens=400,     # ↑ this helps a lot – was probably too low before
    ),
    safety_settings={
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    }
)

        # More robust reply extraction
        reply_text = ""
        if response.text:
            reply_text = response.text.strip()
        elif response.candidates and response.candidates[0].content.parts:
            # Fallback if text is in parts
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    reply_text += part.text
            reply_text = reply_text.strip()

        if not reply_text:
            reply_text = "Sorry, Gemini couldn't generate a response this time. Try again!"
            print("Empty response from Gemini – possible safety/choice block", file=sys.stderr)

        return jsonify({"reply": reply_text})

    except Exception as e:
        error_msg = str(e)
        print(f"Error processing request: {error_msg}", file=sys.stderr)
        return jsonify({"error": error_msg}), 500

@app.route('/', methods=['GET'])
def health_check():
    """Health check – visit in browser to confirm server is alive"""
    status = {
        "status": "online",
        "model": MODEL_NAME if model else "not loaded",
        "api_key_set": bool(GEMINI_API_KEY)
    }
    return jsonify(status)

if __name__ == '__main__':
    # For local testing (Render ignores this)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
