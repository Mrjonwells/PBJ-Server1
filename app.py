from flask import Flask, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
CORS(app)
app.secret_key = 'something-secret'  # Needed for session

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/pbj', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

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

        reply = response.choices[0].message.content.strip()

        # Save assistant's reply to history
        session['history'].append({"role": "assistant", "content": reply})

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('history', None)
    return jsonify({"message": "Conversation reset."})

@app.route('/')
def home():
    return "PBJ Server is running!"

if __name__ == '__main__':
    app.run(debug=True)
