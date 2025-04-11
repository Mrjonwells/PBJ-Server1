from flask import Flask, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
CORS(app)
app.secret_key = 'super-secret-key'  # Needed for sessions

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/pbj', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Initialize chat history if not present
    if 'history' not in session:
        session['history'] = []

    # Add the user's message
    session['history'].append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=session['history'],
            temperature=0.7
        )

        assistant_reply = response.choices[0].message.content.strip()

        # Save assistant's reply to history
        session['history'].append({"role": "assistant", "content": assistant_reply})

        return jsonify({"response": assistant_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('history', None)
    return jsonify({"message": "Conversation history reset."})

@app.route('/')
def home():
    return "PBJ server with memory is running!"
