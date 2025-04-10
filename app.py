import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables (like your OpenAI API key)
load_dotenv()

# Initialize Flask app and OpenAI client
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def index():
    return "PBJ Server is Live!"

@app.route("/pbj", methods=["POST"])
def pbj_handler():
    data = request.get_json()
    user_input = data.get("message", "")

    system_prompt = (
        "You are Project BlueJay, a brilliant strategist powered by the 48 Laws of Power, "
        "psychological leverage, and modern business intelligence. You respond with clarity, "
        "tactical direction, and high-level insight. Your tone is calm, persuasive, and strategic. "
        "You always aim to increase power, influence, or perception."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
