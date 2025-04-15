from flask import Flask, request, jsonify, stream_with_context, Response
from flask_cors import CORS
from openai import OpenAI
import os
import time
import json
import requests

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"

HUBSPOT_FORM_URL = "https://forms.hubspot.com/uploads/form/v2/45853776/8f77cd97-b1a7-416f-9701-bf6de899e020"

# Temporary per-session tracking (you can replace this with a DB later)
thread_leads = {}

# Fields we want to match against BlueJay’s response
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
    found = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            clean_key = key.strip().lower().replace(" ", "_")
            if clean_key in HUBSPOT_FIELDS:
                found[clean_key] = value.strip()
    return found

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
        assistant_id=assistant_id,
        stream=True
    )

    def stream():
        full_response = ""
        for chunk in run:
            if hasattr(chunk, "delta") and hasattr(chunk.delta, "content"):
                token = chunk.delta.content or ""
                full_response += token
                yield f"data: {token}\n\n"
        yield f"data: <END>|{thread_id}\n\n"

        # Extract fields and send to HubSpot
        collected = extract_fields(full_response)
        if "email" in collected and "firstname" in collected:
            if thread_id not in thread_leads:
                status = send_to_hubspot(collected)
                thread_leads[thread_id] = True
                print(f"HubSpot lead sent (status {status})")

    return Response(stream_with_context(stream()), mimetype="text/event-stream")

@app.route('/')
def home():
    return "BlueJay backend is running!"
