from flask import Flask, request, jsonify, render_template
import json
import requests
from datetime import datetime

app = Flask(__name__)
CHAT_FILE = "chat_history.json"

# Load chat history
def load_chat():
    with open(CHAT_FILE, "r") as f:
        return json.load(f)

# Save chat history
def save_chat(chat):
    with open(CHAT_FILE, "w") as f:
        json.dump(chat, f, indent=4)

# Function to call Ollama
def ask_ollama(prompt):
    url = "http://localhost:11434/v1/llm"
    payload = {
        "model": "deepseek-r1:7b",  # your local model
        "prompt": prompt
    }
    response = requests.post(url, json=payload)
    return response.json().get("response", "No response from Ollama")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    chat_history = load_chat()

    # Include last 5 messages as context for continuity
    context = "\n".join([f"User: {c['user']}\nBot: {c['bot']}" for c in chat_history[-5:]])
    full_prompt = context + f"\nUser: {user_input}\nBot:"

    bot_response = ask_ollama(full_prompt)

    # Append new conversation to JSON
    chat_history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_input,
        "bot": bot_response
    })

    save_chat(chat_history)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
