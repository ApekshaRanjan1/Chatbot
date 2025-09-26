from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

PROMPT_FILE = "prompt.json"
CHAT_FILE = "chat_history.json"
RESPONSE_FILE = "response.json"

MODEL = "gemma3:4b"  # Change model here if needed

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": ""})

    # Save user input to prompt.json
    with open(PROMPT_FILE, "w") as f:
        json.dump({"prompt": user_input}, f, indent=2)

    # Load chat history
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            try:
                chat_history = json.load(f)
            except json.JSONDecodeError:
                chat_history = []
    else:
        chat_history = []

    # Load prompt.json
    with open(PROMPT_FILE, "r") as f:
        prompt_data = json.load(f)
    prompt_text = prompt_data.get("prompt", "")

    # Build payload for Ollama
    payload = {
        "model": MODEL,
        "prompt": prompt_text
    }

    bot_response = ""
    try:
        # Stream response from Ollama
        with requests.post("http://127.0.0.1:11434/api/generate",
                           json=payload, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        bot_response += data["response"]
    except Exception as e:
        bot_response = f"[Error connecting to Ollama: {e}]"

    # Update response.json
    with open(RESPONSE_FILE, "w") as f:
        json.dump({"response": bot_response}, f, indent=2)

    # Update chat_history.json
    chat_history.append({"prompt": prompt_text, "response": bot_response})
    with open(CHAT_FILE, "w") as f:
        json.dump(chat_history, f, indent=2)

    # Clear prompt.json
    with open(PROMPT_FILE, "w") as f:
        json.dump({"prompt": ""}, f, indent=2)

    return jsonify({"response": bot_response})


if __name__ == "__main__":
    app.run(debug=True)
