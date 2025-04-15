import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import requests
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

assistant_id = os.getenv("ASSISTANT_ID")

@app.route("/pbj", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    print(f"[User Input] {user_input}")

    if not user_input:
        return jsonify({"error": "No message received"}), 400

    try:
        # Step 1: Create a thread
        thread = client.beta.threads.create()

        # Step 2: Add message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Step 3: Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Step 4: Poll until complete
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return jsonify({"error": "Assistant run failed"}), 500

        # Step 5: Get the messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value

        return jsonify({"response": response_text})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
