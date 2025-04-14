from flask import Flask, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
import os
import time
import requests

app = Flask(__name__)
CORS(app)
app.secret_key = 'super-secret-key'

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = "asst_7OU1YPsc8cRuhWRaJwxsaHx5"

# Your HubSpot form endpoint
HUBSPOT_FORM_URL = "https://forms.hubspot.com/uploads/form/v2/45853776/8f77cd97-b1a7-416f-9701-bf6de899e020"

# Fields to extract and map from conversation memory
REQUIRED_FIELDS = [
    "firstname", "lastname", "email", "phone", "address", "city", "state",
    "company", "business_type", "how_would_you_like_to_be_contacted_", "notes"
]

def extract_field(text, field_name):
    # Very basic pattern-based logic (placeholder: improve with NLP if needed)
    lower = text.lower()
    if "email" in field_name:
        for word in lower.split():
            if "@" in word and "." in word:
                return word
    elif "phone" in field_name:
        for word in lower.split():
            digits = ''.join(filter(str.isdigit, word))
            if len(digits) >= 10:
                return digits
    return None

def try_parse_fields(messages):
    data = {}
    full_text = "\n".join([m["content"] for m in messages if m["role"] == "user" or m["role"] == "assistant"])
    for field in REQUIRED_FIELDS:
        val = extract_field(full_text, field)
        if val:
            data[field] = val
    return data

def submit_to_hubspot(data):
    headers = { "Content-Type": "application/x-www-form-urlencoded" }
    return requests.post(HUBSPOT_FORM_URL, data=data, headers=headers)

@app.route('/pbj', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    if 'thread_id' not in session:
        thread = client.beta.threads.create()
        session['thread_id'] = thread.id

    thread_id = session['thread_id']

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
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            return jsonify({"error": "Assistant run failed"}), 500
        time.sleep(0.3)
    else:
        return jsonify({"error": "Timeout waiting for assistant response"}), 504

    messages = client.beta.threads.messages.list(thread_id=thread_id).data
    latest = messages[0].content[0].text.value

    # Try to extract data and submit to HubSpot
    fields = try_parse_fields([{"role": m.role, "content": m.content[0].text.value} for m in messages])
    if all(field in fields for field in REQUIRED_FIELDS):
        try:
            submit_to_hubspot(fields)
        except Exception as e:
            print("HubSpot submission error:", e)

    return jsonify({"response": latest})

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('thread_id', None)
    return jsonify({"message": "Conversation reset."})

@app.route('/')
def home():
    return "PBJ server with Assistants API + HubSpot is running!"
