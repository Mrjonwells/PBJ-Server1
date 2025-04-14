from flask import Flask, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
import os
import time

app = Flask(__name__)
CORS(app)
app.secret_key = 'super-secret-key'  # Required for session handling

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"

@app.route('/pbj', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Initialize a new thread if one doesn't exist for this session
    if 'thread_id' not in session:
        thread = client.beta.threads.create()
        session['thread_id'] = thread.id

    thread_id = session['thread_id']

    # Add user message to thread
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

    # Poll the run until completion (with faster polling)
    for _ in range(40):  # max wait: 40 * 0.3s = 12 seconds
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            return jsonify({"error": "Assistant run failed"}), 500
        time.sleep(0.3)
    else:
        return jsonify({"error": "Timeout waiting for assistant response"}), 504

    # Retrieve and return the assistant's reply
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    latest = messages.data[0].content[0].text.value

    return jsonify({"response": latest})

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('thread_id', None)
    return jsonify({"message": "Conversation reset."})

@app.route('/')
def home():
    return "PBJ (Assistants API) server is running!"
