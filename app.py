from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import time

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"

@app.route('/pbj', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    incoming_thread_id = data.get("thread_id")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Use existing thread or create a new one
    if incoming_thread_id:
        thread_id = incoming_thread_id
    else:
        thread = client.beta.threads.create()
        thread_id = thread.id

    # Send message to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Wait for the run to complete
    for _ in range(40):
        status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if status.status == "completed":
            break
        elif status.status == "failed":
            return jsonify({"error": "Assistant run failed"}), 500
        time.sleep(0.3)
    else:
        return jsonify({"error": "Timeout waiting for assistant response"}), 504

    # Get the latest message
    messages = client.beta.threads.messages.list(thread_id=thread_id).data
    latest = messages[0].content[0].text.value

    return jsonify({
        "response": latest,
        "thread_id": thread_id
    })

@app.route('/')
def home():
    return "BlueJay backend is live!"
