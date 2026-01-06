from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import sys

app = Flask(__name__)

# =============================================
#          CONFIGURATION - VERY IMPORTANT
# =============================================
# 1. Go to https://aistudio.google.com/app/apikey
# 2. Create new API key (free tier gives you plenty for testing)
# 3. In Render dashboard → your service → Environment tab
#    Add new environment variable:
#    Name: GEMINI_API_KEY
#    Value: your-key-here
# =============================================

try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API key loaded successfully", file=sys.stderr)
except KeyError:
    print("ERROR: GEMINI_API_KEY environment variable is not set!", file=sys.stderr)
    GEMINI_API_KEY = None

# Use latest stable model (as of Jan 2026)
MODEL_NAME = "gemini-2.5-flash"      # Recommended: fast, cheap, current stable equivalent
# or
MODEL_NAME = "gemini-2.5-flash-latest"   # Auto-updates to newest flash variant
# or (higher quality, bit slower):
# MODEL_NAME = "gemini-2.5-pro"
# or (newest frontier, preview as of Jan 2026):
# MODEL_NAME = "gemini-3-flash-preview"

model = None
if GEMINI_API_KEY:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        print(f"Model {MODEL_NAME} initialized", file=sys.stderr)
    except Exception as e:
        print(f"Failed to initialize model: {e}", file=sys.stderr)


@app.route('/chat', methods=['POST'])
def chat():
    if GEMINI_API_KEY is None:
        return jsonify({"error": "Server not configured - missing GEMINI_API_KEY"}), 500

    if model is None:
        return jsonify({"error": "Failed to load Gemini model"}), 500

    try:
        data = request.get_json(force=True)
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field in JSON"}), 400

        user_message = data['message']
        print(f"Received message: {user_message[:100]}...", file=sys.stderr)

        # Optional: add safety settings or generation config
        response = model.generate_content(
            user_message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=300,
            )
        )

        reply_text = response.text.strip() if response.text else "Sorry, I couldn't generate a response."

        return jsonify({"reply": reply_text})

    except Exception as e:
        error_msg = str(e)
        print(f"Error processing request: {error_msg}", file=sys.stderr)
        return jsonify({"error": error_msg}), 500


@app.route('/', methods=['GET'])
def health_check():
    """Simple health check so base URL doesn't 404"""
    status = {
        "status": "online",
        "model": MODEL_NAME if model else "not loaded",
        "api_key_set": bool(GEMINI_API_KEY)
    }
    return jsonify(status)


if __name__ == '__main__':
    # For local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
