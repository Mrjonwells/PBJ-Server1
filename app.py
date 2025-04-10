import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai

load_dotenv()

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def index():
    return "PBJ Server is Live!"

@app.route("/pbj", methods=["POST"])
def pbj_handler():
    data = request.get_json()
    user_input = data.get("message", "")
    
    # Project BlueJay style system prompt
    system_prompt = (
        "You are Project BlueJay, a strategic consigliere combining the 48 Laws of Power, "
        "business acumen, and emotional intelligence. You respond with short, powerful insights, "
        "strategic guidance, and decision-making clarity. You speak like a human strategist, "
        "not an assistant."
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response['choices'][0]['message']['content'].strip()
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
