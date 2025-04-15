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

HUBSPOT_FIELDS = [
    "firstname",
    "lastname",
    "email",
    "phone",
    "business_name",
    "business_type",
    "how_would_you_like_to_be_contacted_",
    "notes",
    "website",
    "monthly_card_sales",
    "average_ticket_size"
]

def extract_fields(text):
    data = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            clean_key = key.strip().lower().replace(" ", "_")
            if clean_key in HUBSPOT_FIELDS:
                data[clean_key] = value.strip()
    return data

def send_to_hubspot(data):
    payload = {field: data.get(field, "") for field in HUBSPOT_FIELDS}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    res = requests.post(HUBSPOT_FORM_URL, data=payload, headers=headers)
    return res.status_code

@app.route('/pbj', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    incoming_thread_id = data.get("thread_id")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    if incoming_thread_id:
        thread_id = incoming_thread_id
    else:
        thread = client.beta.threads.create()
        thread_id = thread.id

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

    # HubSpot integration
    fields = extract_fields(latest)
    if "email" in fields and "firstname" in fields and thread_id not in submitted_threads:
        try:
            status = send_to_hubspot(fields)
            submitted_threads[thread_id] = True
            print(f"[HubSpot] Lead submitted: Status {status}")
        except Exception as e:
            print("[HubSpot] Submission failed:", str(e))

    return jsonify({
        "response": latest,
        "thread_id": thread_id
    })

@app.route('/')
def home():
    return "BlueJay backend with HubSpot integration is live!"
