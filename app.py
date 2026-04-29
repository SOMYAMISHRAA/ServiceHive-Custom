from flask import Flask, render_template, request, jsonify
import uuid
import os
from agent import process_message

app = Flask(__name__)

# Basic storage of session IDs to maintain conversational threads
# (For a product app you'd use browser cookies/sessions, but we just want an ephemeral web test interface)
threads = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    session_id = data.get("session_id")
    
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
        return jsonify({"status": "error", "reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY is missing! Agent will fail unless you provide one.")
    app.run(debug=True, port=5000)
