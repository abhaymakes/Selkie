"""
Implementation of a C2 Server using Python.
"""

from flask import Flask, request

import secrets
import uuid
import base64

app = Flask(__name__)

def generate_new_challenge():
    challenge_id = uuid.uuid4()
    challenge = secrets.token_bytes(32)
    challenge_base64 = base64.b64encode(challenge).decode("utf-8")

    return {
        "challenge_id": challenge_id,
        "challenge": challenge_base64
    }

@app.route("/api/register/start", methods=["POST"])
def register_agent():
    "Receive the initial request from the beacon and send a challenge for verification."
    challenge_generated = generate_new_challenge()

    return challenge_generated
    

if __name__ == "__main__":
    app.run(debug=True, port=4999)