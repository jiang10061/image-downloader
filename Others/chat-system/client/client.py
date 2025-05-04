import socket
import threading
import json
import time
from common.config_loader import ConfigLoader
from common.crypto import AESCipher

class ChatClient:
    def __init__(self):
        self.config = ConfigLoader.load_config('client')
        self.running = True
        self.username = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cipher = AESCipher(bytes.fromhex(self.config['client']['encryption_key']))

    def connect(self):
        while self.running:
            try:
                self.sock.connect((self.config['client']['server_address'], 
                                 self.config['client']['server_port']))
                return True
            except Exception as e:
                print(f"Connection failed: {str(e)}. Retrying...")
                time.sleep(self.config['client']['network_retry_attempts'])

    def encrypt(self, data):
        return self.cipher.encrypt(data)

    def decrypt(self, data):
        return self.cipher.decrypt(data)

    def message_handler(self):
        while self.running:
            try:
                data = self.sock.recv(4096).decode()
                if not data: break
                decrypted = self.decrypt(data)
                msg = json.loads(decrypted)
                print(f"\n{msg['sender']}: {msg['content']}")
            except Exception as e:
                print(f"\nConnection error: {str(e)}")
                break

    def run(self):
        if not self.connect():
            return

        self.username = input("Enter username: ")
        self.sock.sendall(self.username.encode())

        threading.Thread(target=self.message_handler, daemon=True).start()
        threading.Thread(target=self.send_heartbeat, daemon=True).start()

        while self.running:
            try:
                msg = input()
                encrypted = self.encrypt(json.dumps({
                    'sender': self.username,
                    'content': msg,
                    'type': 'message'
                }))
                self.sock.sendall(encrypted.encode())
            except KeyboardInterrupt:
                self.running = False
                self.sock.close()
                print("\nClient terminated.")

    def send_heartbeat(self):
        while self.running:
            self.sock.sendall(b'HEARTBEAT')
            time.sleep(self.config['client']['network_heartbeat_interval'])

if __name__ == "__main__":
    client = ChatClient()
    try:
        client.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
