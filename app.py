from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import requests
import re

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")
hubspot_url = "https://api.hsforms.com/submissions/v3/integration/submit/45853776/8f77cd97-b1a7-416f-9701-bf6de899e020"

# Store conversations per user IP (simplified session)
session_store = {}

def extract_fields(text):
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text)
    name_match = re.search(r"(?:I'm|I am|This is|Name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
    
    name_parts = name_match.group(1).split() if name_match else []
    firstname = name_parts[0] if name_parts else ""
    lastname = name_parts[1] if len(name_parts) > 1 else ""

    return {
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
        "firstname": firstname,
        "lastname": lastname,
        "notes": text
    }

def send_to_hubspot(fields):
    payload = {
        "fields": [
            {"name": "email", "value": fields["email"]},
            {"name": "phone", "value": fields["phone"]},
            {"name": "firstname", "value": fields["firstname"]},
            {"name": "lastname", "value": fields["lastname"]},
            {"name": "notes", "value": fields["notes"]},
        ]
    }
    response = requests.post(hubspot_url, json=payload)
    print("[HubSpot] Lead submitted:", response.status_code)
    return response.status_code

@app.route("/pbj", methods=["POST"])
def pbj():
    data = request.get_json()
    user_input = data.get("message", "")
    user_ip = request.remote_addr or "default"

    # Store the user input in session
    if user_ip not in session_store:
        session_store[user_ip] = []

    session_store[user_ip].append(user_input)

    # Trigger final submission
    if user_input.lower().strip() in ["done", "submit", "that's all", "go ahead", "looks good"]:
        combined_input = " ".join(session_store[user_ip])
        fields = extract_fields(combined_input)
        print("[HubSpot] Fields extracted:", fields)
        send_to_hubspot(fields)
        session_store.pop(user_ip)  # clear the session
        return jsonify({"response": "Awesome! I’ve submitted your info to our team. Expect a follow-up soon!"})

    # Regular chat flow
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_input}]
    )

    reply = response.choices[0].message["content"]
    return jsonify({"response": reply})
