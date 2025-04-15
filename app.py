import os
import json
import openai
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"
hubspot_form_url = "https://api.hsforms.com/submissions/v3/integration/submit/45853776/8f77cd97-b1a7-416f-9701-bf6de899e020"

app = Flask(__name__)
CORS(app)

conversations = {}

@app.route("/pbj", methods=["POST"])
def chat_with_pbj():
    try:
        user_input = request.json.get("message", "").strip()
        user_id = request.remote_addr

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Initialize thread if not exists
        if user_id not in conversations:
            thread = openai.beta.threads.create()
            conversations[user_id] = {"thread_id": thread.id}
        else:
            thread = openai.beta.threads.retrieve(conversations[user_id]["thread_id"])

        # Append message
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Run assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Polling for completion
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return jsonify({"error": "Assistant failed to complete the task"}), 500

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        assistant_reply = messages.data[0].content[0].text.value

        # Extract contact info from user input
        info = extract_contact_info(user_input)
        if info.get("email") and info.get("phone") and info.get("firstname") and info.get("lastname"):
            send_to_hubspot(info)

        return jsonify({"response": assistant_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def extract_contact_info(text):
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    phone_match = re.search(r"\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b", text)
    name_match = re.search(r"(?:my name is|I'm|I am)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)", text)
    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "firstname": name_match.group(1) if name_match else None,
        "lastname": name_match.group(2) if name_match else None,
        "notes": text
    }

def send_to_hubspot(data):
    payload = {
        "fields": [
            {"name": "email", "value": data["email"]},
            {"name": "firstname", "value": data["firstname"]},
            {"name": "lastname", "value": data["lastname"]},
            {"name": "phone", "value": data["phone"]},
            {"name": "notes", "value": data["notes"]}
        ]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(hubspot_form_url, json=payload, headers=headers)
    print("[HubSpot] Lead submitted:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(debug=True)
