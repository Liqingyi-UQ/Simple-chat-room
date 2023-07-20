# Simple-chat-room
Written in Python. A chat room for online multiplayer. There is no UI design. Use Python's threading. This is my first personal project on COMS 3200 Computer Network 1 at UQ


## Statement:
This personal project was written as part C of the A1 assignment in UQ's Computer Network 1 (COMS 3200) in the first semester of 2023. Uploaded to Github after the author graduated. Do not copy or reprint without permission

## Introduction

This project is part C of computer network A1, and it mainly realizes the application design of multi-person online chat. There are multiple channels on the server side, and users can enter different channels to chat online. More specifically, it also includes private chat, file transfers, and so on. The main transport layer protocol implemented by the project is TCP, and the programming language is Python.

## Installation
1. Just download the chatserver.py and chatclient.py files in the compressed file. Self-configured configuration files must satisfy the requirement that each line follows the following format:
channel <channel_name> <channel_port> <channel_capacity>
The configuration file and the two py files must be in the same directory.
2. It can be run with python3.6.8, or it can be started with various shell scripts in the Linux system.

## List Of Functions
For chatclient.py:
1. Initialization: The client has a Client class, and the Client class has attributes such as host, port, and username. At the same time, run indicates whether the client is running, file_path stores the legal path of the file to be sent, and target stores the target object for sending the file.
2. connect: Request connection, send your user name to the server and request connection
3.send_message: Send the command or message you input
4. want_send: Before calling, judge whether the command is in the format of sending a file, and then judge whether the file exists. If it exists, send it to tell the server to send the file, and who is the target. If it does not match, tell the server to send an error message "send the not existing file:{path}" If the file exists, no matter whether it can be sent or not, otherwise, the transfer object and purpose have been determined, and the value of self has been changed
5. check_can_sent: check whether the server is allowed to send files, the message that is allowed by the server is: "[Server message ({time})] You sent {file_path} to {target}.\n" returns true. If not allowed, returns false
6. send_file: Before calling, you have obtained the permission of the server, and the client can send the file. (check_can_sent passed), send a header first: /File {file_size} {file_name} Tell the server to send the target and file information, and then send the file.
7. receive_file: Receive a file, and check whether the server intends to transfer the file before calling
8. receive_message: Receive the message transmitted from the server, and do different processing according to different messages. If it is other client information, it will be displayed. If it is some command, execute it, such as "switch to port", close your existing connection, and reconnect to the new port.
9. send_message: Send the command or message from the client to the server.
10. start: Start the client and use send_message as a daemon thread.
11. main: Determine whether the command to start the client meets the requirements, if it meets the requirement to start the client

For chatserver.py:
For the server side:
1. TIME_OF_LIVING: Constant, the default standby time. 100 seconds. The channel is raised when the user does not send any messages or commands for more than 100 seconds.

### Channel class
1. Init: Initialize the channel. Channel class has a name, port, capacity, etc. Clients store all existing users of the channel, the storage method is a list, and each list element is [client_socket, username]. The waiting_list stores the waiting users, first in first out, and the list is implemented. The elements of each list are [client_socket, username]. timetable stores the timetable (dictionary) of each user of the channel, and the elements in the dictionary are "username": {alive_start_time: alive_end_time, mute_start_time, mute_end_time}.
2. empty: The channel clears the current users in the channel, and then waits for the queued users to join
3. update_timetable_by_mute(self, username, mute_time, mute_start_time): Timetable update: The server mute command is updated where mute_time is a positive integer string mute_start_time is the start time of the mute command.
4. update_timetable_by_message(self, username, current_time): Timetable update: the timetable is updated when the message is sent. 
5. disconnect_client(self, username): The channel cuts off the connection with a certain user. Before cutting off, judge whether it is in the channel
6. get_socket_by_name(self, username): find socket by username
7. is_not_full: Check whether the channel is full, if not, return false; otherwise return true
8.add_client: add a user to channel
9. add_wait: Add a user to the waiting queue. No matter what, the user will be added to the waiting queue first. Note that add wait here actually joins the channel immediately if the queue is not full
10. has_client_in_channel(self, username): Determine whether there is a user whose username already exists in the channel, and if so, return true
11.has_client_in_waiting(self, username): Determine whether there is a user whose username already exists in the waiting queue of the channel, and return true if it exists.
12. get_client_position: As long as there are people on the waiting list leaving, it will send a message to each waiting person about how many people are in front of him
13. remove_from_channel(self, client_socket): remove the user from the channel, and then return a true to tell the server to find the user from the waiting list to enter the channel
14. remove_from_waiting(self, client_socket): Remove the specified user from the waiting queue
15. broadcast(self, message): Send group announcements or group chats (to everyone in the channel)
16. tell_others(self, message, username): send to other people in the channel
17. switch(self, client_socket, username, new_channel): The user tries to switch to a new channel, if the switch cannot be returned to False, if the switch can be returned to True, if it is True, the server sends the port number and then disconnects from the user
18. whisper(self, sender_socket, sender_name, message): It is used to process private chat information, sender_socket is the information of the private chat person, and the message is the information from the private chat. If the private chat fails, it will return to tell the sender that the private chat person is not here

### Public Functions
1.is_positive_integer(num): Determine whether it is a positive integer
2.remove_dup_space(cmd): Used to remove extra spaces in the string, cmd is a string type

###Server class
Used to manage different channels.
1. Initialization: channels are a list used to store instance objects of the channel class.
2. response_list_request(self, client_socket): Find the information of the current channel in the channel: [Channel] <channel_name > <current >/<capacity >/<queue_length >
3. get_channel_by_name(self, channel_name): Find the information list of the channel according to the name of the channel, if it exists, return the corresponding channel, if it does not exist, return None
4. get_channel_by_port(self, channel_port): Find the information list of the channel according to the port number of the channel, if it exists, return the information list, if it does not exist, return False
5. load_config(self, config_file): Load the configuration file and get the channel instance object
6. handle_client(self, channel, client_socket): handle the commands and information sent by the client received by the channel and the channel.
7. check_is_alive(self, channel): Check once per second whether there is a user in the channel that has timed out, if not, it will be normal, if there is a timeout, it will be kicked out
8.accept_clients(self, server_socket, channel): The channel receives the client requesting connection
9. start(self, config file): read the configuration file, instantiate the channel class and server class, and create the socket corresponding to each channel (each channel has its socket). And receive server-side commands, and perform different operations according to different commands. For example, "/shutdown" is to close the server.
10. main: If the command to start the server is legal and the configuration file is legal, start the server. else exit(1)

## The Test
1. Observation: Run the program with pycharm, and then enter the corresponding command in the terminal command according to the assignment requirements to check whether the output value is correct. For example, enter in the client: python3 chatclient.py 7777 lqy (the port number is correct), and check whether the client output is:
[Server message (16:19:02)] Welcome to the channel1 channel, lqy.
[Server message (16:19:02)] lqy has joined the channel.
2. Use a Linux virtual machine (Fedora) to run the test file on Blackboard locally.
3. Upload to MOSS and run the test file on Blackboard.

## References:
[1] Python Software Foundation, "16.1. threading — Thread-based parallelism," Python 3.6.8 documentation. [Online]. Available: https://docs.python.org/3.6/library/threading.html. [Accessed: 25-Apr-2023].
[2] Python Software Foundation, "19.6. socket — Low-level networking interface," Python 3.6.8 documentation. [Online]. Available: https://docs.python.org/3.6/library/socket.html. [Accessed: 25-Apr-2023].
[3] Sentdex, "Socket Chatroom server - Creating chat application with sockets in Python," YouTube, 3-Apr-2019. [Online]. Available: https://www.youtube.com/watch?v=Lbfe3-v7yE0. [Accessed: 25-Apr-2023].
