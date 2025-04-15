from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import time
import requests

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"

HUBSPOT_FORM_URL = "https://forms.hubspot.com/uploads/form/v2/45853776/8f77cd97-b1a7-416f-9701-bf6de899e020"
submitted_threads = {}

STANDARD_FIELDS = ["firstname", "lastname", "email", "phone"]

def extract_fields(text):
    structured = {}
    extras = []
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            clean_key = key.strip().lower().replace(" ", "_")
            clean_value = value.strip()
            if clean_key in STANDARD_FIELDS:
                structured[clean_key] = clean_value
            else:
                extras.append(f"{key.strip()}: {clean_value}")
    if extras:
        structured["notes"] = "\n".join(extras)
    return structured

def send_to_hubspot(data):
    payload = {field: data.get(field, "") for field in STANDARD_FIELDS}
    payload["notes"] = data.get("notes", "")
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(HUBSPOT_FORM_URL, data=payload, headers=headers).status_code

@app.route('/pbj', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    incoming_thread_id = data.get("thread_id")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    thread_id = incoming_thread_id or client.beta.threads.create().id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    for _ in range(40):
        status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if status.status == "completed":
            break
        elif status.status == "failed":
            return jsonify({"error": "Assistant run failed"}), 500
        time.sleep(0.3)
    else:
        return jsonify({"error": "Timeout waiting for assistant response"}), 504

    messages = client.beta.threads.messages.list(thread_id=thread_id).data
    latest = messages[0].content[0].text.value

    fields = extract_fields(user_message)
    print(f"[HubSpot] Fields extracted from user input: {fields}")

    if "email" in fields and "firstname" in fields and thread_id not in submitted_threads:
        try:
            status = send_to_hubspot(fields)
            submitted_threads[thread_id] = True
            print(f"[HubSpot] Lead submitted: Status {status}")
        except Exception as e:
            print(f"[HubSpot] Submission failed: {str(e)}")
    else:
        print("[HubSpot] Skipping submission: Missing required fields or already submitted.")

    return jsonify({
        "response": latest,
        "thread_id": thread_id
    })

@app.route('/')
def home():
    return "BlueJay backend v1.4 — Standard HubSpot fields with bundled notes active."
