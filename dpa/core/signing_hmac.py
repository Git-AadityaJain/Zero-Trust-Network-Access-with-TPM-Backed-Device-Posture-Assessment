import hmac
import hashlib

class HMACSigner:
    def __init__(self, key=None):
        self.key = key or b'default_hmac_key_for_signing'

    def sign(self, message: str):
        mac = hmac.new(self.key, message.encode('utf-8'), hashlib.sha256)
        return mac.hexdigest()
