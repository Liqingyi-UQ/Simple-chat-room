import os
import socket
import threading
import sys
import datetime
import time

TIME_OF_LIVING = datetime.timedelta(seconds=100)


class Channel:
    def __init__(self, name, port, capacity):
        self.name = name
        self.port = port
        self.capacity = capacity
        self.clients = []
        self.waiting_list = []
        self.timetable = {}

    def empty(self):
        if len(self.clients) == 0:
            return
        else:
            for user in self.clients.copy():
                username = user[1]
                client_socket = self.get_socket_by_name(username)
                client_socket.send("close the socket".encode())
                client_socket.close()
                self.clients.remove(user)
                del self.timetable[username]
            if len(self.waiting_list) == 0:
                return
            else:
                for i in range(min(len(self.waiting_list), self.capacity)):
                    self.add_client()

    def update_timetable_by_mute(self, username, mute_time, mute_start_time):
        self.timetable[username]["mute_start_time"] = mute_start_time
        total_mute_time = datetime.timedelta(seconds=int(mute_time))
        self.timetable[username]["mute_end_time"] = mute_start_time + total_mute_time
        self.timetable[username]["alive_end_time"] += total_mute_time

    def update_timetable_by_message(self, username, current_time):
        if (self.timetable[username]["mute_end_time"] is not None) and current_time < self.timetable[username][
            "mute_end_time"]:
            return
        else:
            self.timetable[username]["alive_start_time"] = current_time
            self.timetable[username]["alive_end_time"] = current_time + TIME_OF_LIVING

    def disconnect_client(self, username):
        time = datetime.datetime.now().strftime('%H:%M:%S')
        client_socket = self.get_socket_by_name(username)
        if client_socket is None:
            sys.stdout.write(f"[Server message({time})] {username} is not in {self.name}.\n")
            sys.stdout.flush()
        else:
            message = f"[Server message ({time})] {username} has left the channel."
            client_socket.send("close the socket".encode())
            client_socket.close()
            self.remove_from_channel(client_socket)
            self.broadcast(message)
            sys.stdout.write(f"[Server message ({time})] Kicked {username}.\n")
            sys.stdout.flush()

    def get_socket_by_name(self, username):
        for user in self.clients:
            if user[1] == username:
                return user[0]
        return None

    def is_not_full(self):
        return len(self.clients) < self.capacity

    def add_client(self):
        time = datetime.datetime.now()
        if len(self.waiting_list) != 0:
            new_add_client_username = self.waiting_list[0][1]
            msg = f"[Server message ({time.strftime('%H:%M:%S')})] {new_add_client_username} has joined the channel."
            server_msg = f"[Server message ({time.strftime('%H:%M:%S')})] {new_add_client_username} has joined the {self.name} channel.\n"
            self.clients.append(self.waiting_list[0])
            self.timetable[new_add_client_username] = {"alive_start_time": time,
                                                       "alive_end_time": time + TIME_OF_LIVING, "mute_start_time": None,
                                                       "mute_end_time": None}
            self.waiting_list.pop(0)
            self.get_client_position()
            self.broadcast(msg)
            sys.stdout.write(server_msg)
            sys.stdout.flush()
        else:
            return

    def add_wait(self, client_socket, username):
        time = datetime.datetime.now().strftime('%H:%M:%S')
        client_socket.send(
            f"[Server message ({time})] Welcome to the {self.name} channel, {username}.\n".encode()
        )
        self.waiting_list.append([client_socket, username])
        position = len(self.waiting_list)

        if self.is_not_full():
            self.add_client()
        else:
            client_socket.send(
                f"[Server message ({time})] You are in the waiting queue and there are {position - 1} user(s) ahead of you.\n".encode())

    def has_client_in_channel(self, username):
        for user in self.clients:
            if username == user[1]:
                return True
        return False

    def has_client_in_waiting(self, username):
        if len(self.waiting_list) == 0:
            return False
        else:
            for waiter in self.waiting_list:
                if username == waiter[1]:
                    return True
            return False

    def get_client_position(self):
        time = datetime.datetime.now().strftime('%H:%M:%S')
        if len(self.waiting_list) == 0:
            return
        else:
            for location, user in enumerate(self.waiting_list):
                user[0].send(
                    f"[Server message ({time}):] You are in the waiting queue and there are {location} user(s) ahead of you.\n".encode())

    def remove_from_channel(self, client_socket):
        for user in self.clients:
            if user[0] == client_socket:
                username = user[1]
                del self.timetable[username]
                self.clients.remove(user)
                self.add_client()
                return
        return

    def remove_from_waiting(self, client_socket):
        for user in self.waiting_list:
            if user[0] == client_socket:
                self.waiting_list.remove(user)
                self.get_client_position()
                return
        return

    def broadcast(self, message):
        if len(self.clients) == 0:
            return
        else:
            for user in self.clients:
                user[0].send((message + '\n').encode())

    def tell_others(self, message, username):
        if len(self.clients) == 0:
            return
        else:
            for user in self.clients:
                if user[1] != username:
                    user[0].send((message + '\n').encode())

    def switch(self, client_socket, username, new_channel):
        time = datetime.datetime.now().strftime('%H:%M:%S')
        if new_channel.has_client_in_channel(username) or new_channel.has_client_in_waiting(username):
            return False
        else:
            msg = f"[Server message ({time})] {username} has left the channel."
            if [client_socket, username] in self.clients:
                self.remove_from_channel(client_socket)
                self.broadcast(msg)
            elif [client_socket, username] in self.waiting_list:
                self.remove_from_waiting(client_socket)
            sys.stdout.writelines(msg + '\n')
            sys.stdout.flush()
        return True

    def whisper(self, sender_socket, sender_name, message):
        time = datetime.datetime.now().strftime('%H:%M:%S')
        if sender_socket not in [user[0] for user in self.clients]:
            return
        else:
            words = message.split(" ")
            acceptor_name = words[1]
            message_index = 2
            acceptor_message = " ".join(words[message_index:])

            if self.has_client_in_channel(acceptor_name):
                for i in range(len(self.clients)):
                    if self.clients[i][1] == acceptor_name:
                        self.clients[i][0].send(
                            f"[{sender_name} whispers to you: ({time})] {acceptor_message}\n".encode())
                        break
            else:
                sender_socket.send(f"[Server message ({time})] {acceptor_name} is not here.\n".encode())

            sys.stdout.write(f"[{sender_name} whispers to {acceptor_name}: ({time})] {acceptor_message}\n")
            sys.stdout.flush()


def is_positive_integer(num):
    if num.isdigit() and int(num) > 0:
        return True
    else:
        return False


def remove_dup_space(cmd):
    return ' '.join(cmd.split())


class Server:
    def __init__(self, config_file):
        self.channels = []

    def response_list_request(self, client_socket):
        channels_information = []
        for channel in self.channels:
            channel_information = f"[Channel] {channel.name} {len(channel.clients)}/{channel.capacity}/{len(channel.waiting_list)}.\n"
            channels_information.append(channel_information)

        message = ''.join(channels_information)
        client_socket.send(message.encode())

    def get_channel_by_name(self, channel_name):
        for channel in self.channels:
            if channel_name == channel.name:
                return channel
        return None

    def get_channel_by_port(self, channel_port):
        for channel in self.channels:
            if channel_port == channel.port:
                return channel
        return None

    def load_config(self, config_file):
        count = 0
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(" ")
                    if len(parts) != 4 or parts[0] != "channel":
                        raise ValueError(f"Invalid line in config file: {line}")

                    if (not is_positive_integer(parts[2])) or (not is_positive_integer(parts[3])):
                        raise ValueError(f"Invalid line in config file: {line}")

                    name = parts[1]
                    port = int(parts[2])
                    capacity = int(parts[3])
                    if capacity < 5:
                        raise ValueError(f"Invalid config file: {line}")

                    new_channel = Channel(name, port, capacity)
                    self.channels.append(new_channel)
                    count += 1

                for i in range(len(self.channels)):
                    for j in range(i + 1, len(self.channels)):
                        if self.channels[i].name == self.channels[j].name:
                            raise ValueError(f"Invalid config file: {line}")

            if count < 3:
                raise ValueError(f"Invalid config file")

        except FileNotFoundError:
            sys.stdout.write(f"Error: Config file '{config_file}' not found")
            sys.stdout.flush()
            sys.exit(1)
        except (ValueError, TypeError):
            sys.stdout.write(f"Error: Invalid config file '{config_file}'")
            sys.stdout.flush()
            sys.exit(1)

    def handle_client(self, channel, client_socket):
        username = None
        try:
            while True:
                message = client_socket.recv(1024).decode().strip()
                current_time = datetime.datetime.now()

                if not message:
                    channel.remove_from_channel(client_socket)
                    break

                elif message.startswith("/connect ") and (len(message.split(" ")) == 2) and \
                        (client_socket not in [user[0] for user in channel.clients]) and \
                        (client_socket not in [user[0] for user in channel.waiting_list]):
                    username = message.split(" ")[1]

                    if channel.has_client_in_channel(username) or channel.has_client_in_waiting(username):
                        client_socket.send(
                            f"[Server message ({current_time.strftime('%H:%M:%S')})] Cannot connect to the {channel.name} channel.\n".encode()
                        )
                        client_socket.close()
                        break
                    else:
                        channel.add_wait(client_socket, username)

                elif message.startswith("/switch "):
                    msg = remove_dup_space(message)
                    if len(msg.split(" ")) == 2:
                        new_channel_name = msg.split(" ")[1].strip()
                        new_channel = self.get_channel_by_name(new_channel_name)
                        if new_channel is None:
                            client_socket.send(
                                f"[Server message ({current_time.strftime('%H:%M:%S')})] {new_channel_name} does not exist.\n".encode())
                            channel.update_timetable_by_message(username, current_time)
                        else:
                            if channel.switch(client_socket, username, new_channel):
                                client_socket.send(f"switch to port: {new_channel.port}".encode())
                                client_socket.close()

                                if client_socket in [user[0] for user in channel.clients]:
                                    channel.remove_from_channel(client_socket)
                                    msg = f"[Server message ({current_time.strftime('%H:%M:%S')})] {username} has left the channel."
                                    channel.broadcast(msg)

                                else:
                                    channel.remove_from_waiting(client_socket)
                                break

                            else:
                                client_socket.send(
                                    f"[Server message ({current_time.strftime('%H:%M:%S')})] Cannot switch to the {new_channel.name} channel.\n".encode())
                                channel.update_timetable_by_message(username, current_time)

                elif message.startswith("/whisper "):
                    if (channel.timetable[username]["mute_end_time"] is not None) and current_time < \
                            channel.timetable[username]["mute_end_time"]:
                        n = int((channel.timetable[username]["mute_end_time"] - current_time).total_seconds())
                        msg = f"[Server message ({current_time.strftime('%H:%M:%S')})] You are still muted for {n} seconds.\n"
                        channel.get_socket_by_name(username).send(msg.encode())
                    else:
                        channel.whisper(client_socket, username, message)

                    channel.update_timetable_by_message(username, current_time)
                    continue

                elif message.startswith("send the not existing file:"):
                    target_information = message.split(":", 1)[1]
                    target_name = target_information.split(" ", 1)[0]
                    file_path = target_information.split(" ", 1)[1]

                    if not channel.has_client_in_channel(target_name):
                        client_socket.send(
                            f"[Server message ({current_time.strftime('%H:%M:%S')})] {target_name} is not here.\n".encode())

                    client_socket.send(
                        f"[Server message ({current_time.strftime('%H:%M:%S')})] {file_path} does not exist.\n".encode())
                    channel.update_timetable_by_message(username, current_time)

                elif message.startswith("/send "):
                    channel.update_timetable_by_message(username, current_time)
                    target = message.split(" ", 2)[1]
                    file_path = message.split(" ", 2)[2]
                    if not channel.has_client_in_channel(target):
                        client_socket.send(
                            f"[Server message ({current_time.strftime('%H:%M:%S')})] {target} is not here.\n".encode())
                    else:
                        client_socket.send(
                            f"[Server message ({current_time.strftime('%H:%M:%S')})] You sent {file_path} to {target}.\n".encode())

                        header = client_socket.recv(1024).decode().strip()
                        file_name = header.split(" ", 2)[2]
                        file_size = int(header.split(" ", 2)[1])
                        target_client = channel.get_socket_by_name(target)
                        target_client.send(f"/FileCome {file_size} {file_name}".encode())
                        file_send = 0
                        while file_send < file_size:
                            piece = client_socket.recv(1024)
                            target_client.send(piece)
                            file_send += len(piece)

                        sys.stdout.write(
                            f"[Server message {current_time.strftime('%H:%M:%S')})] {username} sent {file_path} to {target}.\n")
                        sys.stdout.flush()

                elif message == "/list":
                    self.response_list_request(client_socket)
                    if channel.has_client_in_channel(username):
                        channel.update_timetable_by_message(username, current_time)

                    continue

                elif message == "/quit":
                    if [client_socket, username] in channel.clients:
                        msg = f"[Server message ({current_time.strftime('%H:%M:%S')})] {username} has left the channel."
                        channel.remove_from_channel(client_socket)
                        sys.stdout.write(msg + "\n")
                        sys.stdout.flush()
                        channel.broadcast(msg)
                        client_socket.close()
                        break
                    else:
                        msg = f"[Server message ({current_time.strftime('%H:%M:%S')})] {username} has left the channel."
                        channel.remove_from_waiting(client_socket)
                        sys.stdout.write(msg + "\n")
                        sys.stdout.flush()
                        client_socket.close()
                        break

                else:
                    if (channel.timetable[username]["mute_end_time"] is not None) and current_time < \
                            channel.timetable[username]["mute_end_time"]:
                        n = int((channel.timetable[username]["mute_end_time"] - current_time).total_seconds())
                        if n > 0:
                            msg = f"[Server message ({current_time.strftime('%H:%M:%S')})] You are still muted for {n} seconds.\n"
                            channel.get_socket_by_name(username).send(msg.encode())
                    else:
                        if [client_socket, username] in channel.clients:
                            msg = f"[{username} ({current_time.strftime('%H:%M:%S')})] {message}"
                            channel.broadcast(msg)
                            channel.update_timetable_by_message(username, current_time)
                            sys.stdout.write(msg + "\n")
                            sys.stdout.flush()
                        else:
                            pass

                    continue

        except socket.error:
            return

    def check_is_alive(self, channel):
        msg = ''
        while True:
            clients_to_delete = []
            timetable_copy = channel.timetable.copy()

            for username in timetable_copy:
                nowtime = datetime.datetime.now()
                if timetable_copy[username]['alive_end_time'] <= nowtime and channel.has_client_in_channel(username):
                    client_socket = channel.get_socket_by_name(username)
                    client_socket.close()

                    clients_to_delete.append(username)
                    msg = f"[Server message ({nowtime.strftime('%H:%M:%S')})] {username} went AFK."
                    sys.stdout.write(msg + '\n')
                    sys.stdout.flush()

            for username in clients_to_delete:
                client_socket = channel.get_socket_by_name(username)
                channel.remove_from_channel(client_socket)

            if len(clients_to_delete) != 0:
                channel.broadcast(msg)

            time.sleep(0.01)

    def accept_clients(self, server_socket, channel):
        check_alive = threading.Thread(target=self.check_is_alive, args=(channel,))
        check_alive.daemon = True
        check_alive.start()
        while True:
            client_socket, addr = server_socket.accept()
            handle_clients = threading.Thread(target=self.handle_client, args=(channel, client_socket))
            handle_clients.daemon = True
            handle_clients.start()

    def start(self, configfile):
        self.load_config(configfile)
        for channel in self.channels:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            server_socket.bind(('', channel.port))
            server_socket.listen(5)
            acception = threading.Thread(target=self.accept_clients, args=(server_socket, channel))
            acception.daemon = True
            acception.start()

        while True:
            cmd = sys.stdin.readline().strip()
            if cmd == "/shutdown":
                sys.exit(1)

            elif cmd.startswith("/kick "):
                newcmd = remove_dup_space(cmd)
                if len(newcmd.split(" ")) == 2:
                    targe = newcmd.split(" ", 1)[1]
                    channel_name = targe.split(":", 1)[0]
                    username = targe.split(":", 1)[1]
                    time = datetime.datetime.now().strftime('%H:%M:%S')
                    channel = self.get_channel_by_name(channel_name)
                    if channel is None:
                        sys.stdout.write(f"[Server message({time})] {channel_name} does not exist.\n")
                        sys.stdout.flush()
                    else:
                        channel.disconnect_client(username)
                continue

            elif cmd.startswith("/mute "):
                newcmd = remove_dup_space(cmd)
                if len(newcmd.split(" ")) == 3:
                    time = datetime.datetime.now()
                    _, channel_and_target, mute_time = newcmd.split(" ")
                    channel_name, username = channel_and_target.split(":")
                    channel = self.get_channel_by_name(channel_name)
                    if channel is None:
                        sys.stdout.write(f"[Server message ({time.strftime('%H:%M:%S')})] {username} is not here.\n")
                        sys.stdout.flush()
                    else:
                        if not channel.has_client_in_channel(username):
                            sys.stdout.write(
                                f"[Server message ({time.strftime('%H:%M:%S')})] {username} is not here.\n")
                            sys.stdout.flush()
                        else:
                            if not mute_time.isdigit():
                                sys.stdout.write(f"[Server message ({time.strftime('%H:%M:%S')})] Invalid mute time.\n")
                                sys.stdout.flush()
                            else:
                                if int(mute_time) == 0:
                                    sys.stdout.write(
                                        f"[Server message ({time.strftime('%H:%M:%S')})] Invalid mute time.\n")
                                    sys.stdout.flush()
                                else:
                                    sys.stdout.write(
                                        f"[Server message ({time.strftime('%H:%M:%S')})] Muted {username} for {mute_time} seconds.\n")
                                    sys.stdout.flush()
                                    msg1 = f"[Server message ({time.strftime('%H:%M:%S')})] You have been muted for {mute_time} seconds.\n"
                                    channel.get_socket_by_name(username).send(msg1.encode())
                                    msg2 = f"[Server message ({time.strftime('%H:%M:%S')})] {username} has been muted for {mute_time} seconds."
                                    channel.tell_others(msg2, username)
                                    channel.update_timetable_by_mute(username, mute_time, time)
                continue

            elif cmd.startswith("/empty "):
                newcmd = remove_dup_space(cmd)
                if len(newcmd.split(" ")) == 2:
                    time = datetime.datetime.now()
                    channel_name = cmd.split(" ", 1)[1]
                    channel = self.get_channel_by_name(channel_name)
                    if channel is None:
                        sys.stdout.write(
                            f"[Server message ({time.strftime('%H:%M:%S')})] {channel_name} does not exist.\n")
                        sys.stdout.flush()
                    else:
                        channel.empty()
                        sys.stdout.write(
                            f"[Server message ({time.strftime('%H:%M:%S')})] {channel_name} has been emptied.\n")
                        sys.stdout.flush()
                continue


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)

    configfile = sys.argv[1]
    try:
        server = Server(configfile)
        server.start(configfile)
    except Exception as e:
        sys.exit(1)
