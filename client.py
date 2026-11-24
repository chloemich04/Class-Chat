import socket
import json
import select
import threading

def client():

    host = '127.0.0.1' # address for local testing
    port = 5000 # server's socket port number

    username = input("Enter a username: ")  # the client will name itself

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4 TCP socket
    client_socket.connect((host, port)) # connect to the server

    client_socket.sendall(username.encode('utf-8'))  # tell the server who the client is

    response = client_socket.recv(1024).decode('utf-8') # the server will tell if the client is registered or not

    if response == "REGISTERED":
        print(f"Welcome to Class Chat: {username}!") # the client is accepted 
    else:
        print("Username already taken.") # the client is rejected; stop the client
        client_socket.close()
        return

    # The client can now communicate through the server

    stop_event = threading.Event()

    # let the clients send messages to their recipient
    thread = threading.Thread(
        target=send_messages,
        args=(client_socket, username, stop_event),
        daemon=True
    )

    thread.start()

    try:
        receive_messages(client_socket, stop_event)
    finally:
        stop_event.set()
        client_socket.close()


def send_messages(client_socket, username, stop_event):
    while not stop_event.is_set():
        # Send a message
        recipient = input("Who would you like to message: ")  # who are you texting
            
        text = input("What do you want to say -> ") # get input

        if stop_event.is_set(): # if the client is disconnected, don't let the message go through
            break

        if text.lower().strip() == 'bye': # if the client types 'bye' they will be disconnected from the server
            stop_event.set()
            break
    
        text_info = {
            "sender": username,
            "receiver": recipient,
            "message": text
        }
    
        json_info = json.dumps(text_info)

        # send the message but if it doesn't get sent (server disconnected), stop the operation
        try:
            client_socket.sendall(json_info.encode('utf-8'))
        except OSError as e:
            print(f"Send failed: {e}")
            stop_event.set()
            break

def receive_messages(client_socket,stop_event):
    while not stop_event.is_set():
        readable, writable, exceptional = select.select(
            [client_socket],[],[], 1
        )

        # no incoming data; check again
        if client_socket not in readable:
            continue
        
        raw_message = client_socket.recv(1024)

        if not raw_message: # see if the server disconnection
            stop_event.set()
            break
        try:
            data = raw_message.decode('utf-8')
        except UnicodeDecodeError:
            print("Received non-UTF-8 data from the server, skipping...")
            continue

        # show the recipient the message the client sent
        # if the server sends something to the client, the name will be 'Server
        try:
            message_info = json.loads(data)
            print(f"<{message_info["sender"]}>: {message_info["message"]}")
        except json.JSONDecodeError:
            print(f"<Server>: {data}")

if __name__ == '__main__':
    client()