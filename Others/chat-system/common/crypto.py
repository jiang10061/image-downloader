from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json

class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, plaintext):
        try:
            cipher = AES.new(self.key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
            return json.dumps({
                'nonce': base64.b64encode(cipher.nonce).decode(),
                'ciphertext': base64.b64encode(ciphertext).decode(),
                'tag': base64.b64encode(tag).decode()
            })
        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")

    def decrypt(self, ciphertext):
        try:
            data = json.loads(ciphertext)
            nonce = base64.b64decode(data['nonce'])
            ciphertext = base64.b64decode(data['ciphertext'])
            tag = base64.b64decode(data['tag'])
            
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ciphertext, tag)
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")