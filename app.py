from flask import Flask, render_template, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

CHAT_FILE = "chat_history.json"
PROMPT_FILE = "prompt.json"

# Home route
@app.route("/")
def home():
    return render_template("index.html")

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    # Load existing chat history
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    # Build conversation context (last 5 exchanges)
    history_text = ""
    for turn in history[-5:]:
        history_text += f"User: {turn['user']}\nBot: {turn['bot']}\n"
    history_text += f"User: {user_message}\nBot:"

    # Save latest prompt separately
    with open(PROMPT_FILE, "w") as f:
        json.dump({"prompt": history_text}, f, indent=2)

    # Send to Ollama
    payload = {
        "model": "deepseek-r1:7b",
        "prompt": history_text
    }

    bot_response = ""
    try:
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

    # Save chat history
    history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "bot": bot_response
    })

    with open(CHAT_FILE, "w") as f:
        json.dump(history, f, indent=2)

    return jsonify({"response": bot_response})


if __name__ == "__main__":
    app.run(debug=True)
