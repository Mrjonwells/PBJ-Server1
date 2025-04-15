from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import time
import requests
import re

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"

HUBSPOT_FORM_URL = "https://forms.hubspot.com/uploads/form/v2/45853776/8f77cd97-b1a7-416f-9701-bf6de899e020"
submitted_threads = {}

def extract_fields(text):
    data = {}

    # Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        data["email"] = email_match.group(0)

    # Phone (US)
    phone_match = re.search(r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})", text)
    if phone_match:
        data["phone"] = phone_match.group(0)

    # Name detection (improved for multiple intro styles)
    name_patterns = [
        r"(?:my name is|this is|i am|i’m|it's|it is|hey[, ]*this is|hey[, ]*i'?m)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",  # "My name is Jordan Lee"
        r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+(from|at)\b"  # "Jordan Lee from Mint Mocha"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["firstname"] = match.group(1)
            data["lastname"] = match.group(2)
            break

    data["notes"] = text.strip()
    return data

def send_to_hubspot(data):
    payload = {
        "firstname": data.get("firstname", ""),
        "lastname": data.get("lastname", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "notes": data.get("notes", "")
    }
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
    print(f"[HubSpot] Fields extracted from natural input: {fields}")

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
    return "BlueJay backend v1.6 — Enhanced natural language extraction + HubSpot sync"
