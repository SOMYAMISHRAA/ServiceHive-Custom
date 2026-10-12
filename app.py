
from flask import Flask, render_template, request, jsonify
import uuid
import os
import traceback

from agent import process_message

app = Flask(__name__)

# Store session IDs for conversational threads.
# Conversation state is managed by the agent's LangGraph memory.
threads = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    user_message = data.get("message")
    session_id = data.get("session_id")

    # Validate the incoming request.
    if not user_message or not isinstance(user_message, str):
        return jsonify({
            "status": "error",
            "reply": "Please enter a valid message."
        }), 400

    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        response_data = process_message(session_id, user_message)

        return jsonify({
            "status": "success",
            "reply": response_data["reply"],
            "session_id": session_id,
            "state": response_data["state"]
        })

    except Exception as e:
        # Print the complete error and traceback in the terminal.
        print("\n========== CHATBOT ERROR ==========")
        traceback.print_exc()
        print("===================================\n")

        # Return the exception message to the browser for debugging.
        return jsonify({
            "status": "error",
            "reply": f"Error: {str(e)}"
        }), 500


if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        print(
            "WARNING: GOOGLE_API_KEY is missing! "
            "Check that your .env file is configured correctly."
        )

    app.run(debug=True, port=5000)
