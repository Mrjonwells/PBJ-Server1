from flask import Flask, request, jsonify, stream_with_context, Response
from flask_cors import CORS
from openai import OpenAI
import os
import time
import json

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

    # Use existing thread or create new
    if incoming_thread_id:
        thread_id = incoming_thread_id
    else:
        thread = client.beta.threads.create()
        thread_id = thread.id

    # Add user message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    # Start the run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        stream=True  # Turn on streaming
    )

    def stream():
        full_response = ""
        for chunk in run:
            if hasattr(chunk, "delta") and hasattr(chunk.delta, "content"):
                token = chunk.delta.content or ""
                full_response += token
                yield f"data: {token}\n\n"
        yield f"data: <END>|{thread_id}\n\n"

    return Response(stream_with_context(stream()), mimetype="text/event-stream")
