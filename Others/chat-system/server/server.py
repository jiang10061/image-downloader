import socket
import threading
import json
import logging
from datetime import datetime
from common.config_loader import ConfigLoader
from common.crypto import AESCipher

class ChatServer:
    def __init__(self):
        self.config = ConfigLoader.load_config('server')
        self.clients = {}
        self.logger = self.setup_logger()
        self.encryption_key = bytes.fromhex(self.config['server']['encryption_key'])
        self.cipher = AESCipher(self.encryption_key)

    def setup_logger(self):
        logger = logging.getLogger('chat_server')
        logger.setLevel(self.config['logging']['level'])
        handler = logging.FileHandler(self.config['logging']['file'])
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def encrypt(self, data):
        return self.cipher.encrypt(data)

    def decrypt(self, data):
        return self.cipher.decrypt(data)

    def handle_client(self, conn, addr):
        username = None
        try:
            with conn:
                username = conn.recv(1024).decode()
                self.clients[username] = conn
                self.logger.info(f"{username} connected from {addr}")
                self.broadcast(f"{username} joined the chat!")

                while True:
                    data = conn.recv(4096)
                    if not data: break
                    
                    decrypted = self.decrypt(data.decode())
                    msg = json.loads(decrypted)
                    
                    if msg['type'] == 'heartbeat':
                        continue
                    else:
                        self.broadcast(f"{username}: {msg['content']}")

        except Exception as e:
            self.logger.error(f"Client error: {str(e)}")
        finally:
            if username and username in self.clients:
                del self.clients[username]
                self.broadcast(f"{username} left the chat")
                self.logger.info(f"{username} disconnected")

    def broadcast(self, message):
        encrypted_msg = self.encrypt(message)
        for client in list(self.clients.values()):
            try:
                client.sendall(encrypted_msg.encode())
            except:
                self.remove_client(client)

    def remove_client(self, conn):
        for username, client in list(self.clients.items()):
            if client == conn:
                del self.clients[username]
                self.logger.info(f"Removed {username}")
                break

    def heartbeat_checker(self):
        while True:
            now = datetime.now()
            for username, conn in list(self.clients.items()):
                try:
                    conn.sendall(b'PING')
                    conn.recv(4)
                except:
                    self.remove_client(conn)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.config['server']['bind_address'], self.config['server']['port']))
            s.listen()
            self.logger.info(f"Server started on {self.config['server']['bind_address']}:{self.config['server']['port']}")
            
            threading.Thread(target=self.heartbeat_checker, daemon=True).start()
            
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()