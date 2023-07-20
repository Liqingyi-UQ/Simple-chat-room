import os
import socket
import threading
import sys
import datetime

class Client:
    def __init__(self, host, port, username):
        self.run = True
        self.host = host
        self.port = port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_path = None
        self.target = None
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((self.host, self.port))
        message = f"/connect {self.username}"
        self.send_message(message)

    def send_message(self, message):
        self.socket.send(message.encode())

    def want_send(self, message):
        path = message.split(" ", 2)[2]
        self.target = message.split(" ", 2)[1]
        if os.path.isfile(path):
            self.file_path = path
            self.send_message(message)
        else:
            error_msg = f"send the not existing file:{self.target} {path}"
            self.send_message(error_msg)

    def check_can_sent(self, message):
        if message.startswith("[Server message ") and message.split("]")[1].startswith(" You sent "):
            sys.stdout.write(message)
            sys.stdout.flush()
            return True
        else:
            return False

    def send_file(self):
        file_name = os.path.basename(self.file_path)
        file_size = os.path.getsize(self.file_path)
        header = f"/File {file_size} {file_name}"
        self.send_message(header)
        with open(self.file_path, "rb") as f:
            while True:
                piece = f.read(1024)
                if not piece:
                    break
                self.socket.send(piece)
        f.close()

    def receive_file(self, message):
        file_size = int(message.split(" ", 2)[1])
        file_name = message.split(" ", 2)[2]
        with open(file_name, 'wb') as f:
            file_received = 0
            while file_received < file_size:
                piece = self.socket.recv(1024)
                f.write(piece)
                file_received += len(piece)
        f.close()

    def receive_messages(self):
        while self.run:
            try:
                message = self.socket.recv(1024).decode()

                if not message:
                    self.socket.close()
                    self.run = False
                    sys.stdin.close()
                    sys.exit()

                elif message == "close the socket":
                    self.socket.close()
                    sys.stdin.close()
                    break

                elif message.startswith("switch to port:"):
                    new_port = int(message.split(":")[-1])

                    self.socket.close()
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.port = new_port
                    self.connect()

                elif message.startswith("[Server message ") and message.split(" ")[3] == "Cannot" and \
                        message.split(" ")[4] == "connect":
                    self.run = False
                    sys.exit()

                elif self.check_can_sent(message):
                    self.send_file()

                elif message.startswith("/FileCome "):
                    self.receive_file(message)

                else:
                    sys.stdout.write(message)
                    sys.stdout.flush()

            except ConnectionResetError:
                break

            except Exception as e:
                break

    def send_messages(self):
        while True:
            try:
                msg = sys.stdin.readline().strip()
                if msg == "/quit":
                    self.send_message(msg)
                    self.run = False
                    break

                elif msg.startswith("/send "):
                    self.want_send(msg)
                else:
                    self.send_message(msg)
            except Exception as e:
                break

    def start(self):
        self.connect()
        send = threading.Thread(target=self.send_messages)

        send.daemon = True
        send.start()
        self.receive_messages()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit(1)

    port_str = sys.argv[1]
    username = sys.argv[2]

    port = int(port_str)

    client = Client("localhost", port, username)
    client.start()
