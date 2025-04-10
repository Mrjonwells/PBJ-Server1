import os
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_ID = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"  # Your Custom GPT ID

@app.route("/", methods=["GET"])
def index():
    return "PBJ (Custom GPT) is Live!"

@app.route("/pbj", methods=["POST"])
def pbj_handler():
    data = request.get_json()
    user_input = data.get("message", "")

    try:
        # Step 1: Create a thread
        thread = client.beta.threads.create()

        # Step 2: Add message to thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Step 3: Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Step 4: Wait for the run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return jsonify({"error": "Assistant run failed."}), 500
            time.sleep(1)

        # Step 5: Get the assistant’s reply
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value.strip()

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
