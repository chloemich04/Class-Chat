import socket
import json
import select
import threading
import queue
from protocol import frame_message, extract_messages

def client():

    host = '127.0.0.1' # address for local testing
    port = 5000 # server's socket port number

    username = input("Enter a username: ")  # the client will name itself

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4 TCP socket
    client_socket.connect((host, port)) # connect to the server

    buffer = b''

    client_socket.sendall(frame_message(username))  # tell the server who the client is

    while b'\n' not in buffer:
        data = client_socket.recv(1024) # the server will tell if the client is registered or not

        if not data:
            print("Server disconnected during registration.")
            client_socket.close()
            return
        
        buffer += data

    # get the server's decision from the buffer
    response_bytes, buffer = buffer.split(b'\n', 1)
    response = response_bytes.decode('utf-8')

    if response == "REGISTERED":
        print(f"Welcome to Class Chat: {username}!") # the client is accepted 
    else:
        print("Username already taken.") # the client is rejected; stop the client
        client_socket.close()
        return

    # The client can now communicate through the server (hooray:))

    stop_event = threading.Event()

    out_going = queue.Queue()

    read_socket, write_socket = socket.socketpair()

    # let the clients send messages to their recipient
    thread = threading.Thread(
        target=send_messages,
        args=(username, out_going, write_socket, stop_event),
        daemon=True
    )

    thread.start()

    try:
        receive_messages(client_socket, out_going, read_socket, stop_event, buffer)
    finally:
        stop_event.set()
        read_socket.close()
        write_socket.close()
        client_socket.close()


def send_messages(username, out_going, write_socket, stop_event):
    while not stop_event.is_set():
        # Send a message
        recipient = input("Who would you like to message: ")  # who are you texting
            
        text = input("What do you want to say -> ") # get input

        if stop_event.is_set(): # if the client is disconnected, don't let the message go through
            break

        # if the client types 'bye' they will be disconnected from 
        # the server; make sure the server is aware of it
        if text.lower().strip() == 'bye': 
            try:
                write_socket.sendall(b'Q')
            except OSError:
                stop_event.set()
            
            break
    
        text_info = {
            "sender": username,
            "receiver": recipient,
            "message": text
        }
    
        json_info = json.dumps(text_info)

        # send the message to the queue
        out_going.put(frame_message(json_info))

        try:
        # tell the main thread to get the message from the queue
            write_socket.sendall(b'M')
        # if it doesn't get sent, stop the operation
        except OSError as e:
            print(f"Notification failed: {e}")
            stop_event.set()
            break 


def receive_messages(client_socket,out_going, read_socket, stop_event, buffer):
    while not stop_event.is_set():
        timeout = 0 if b'\n' in buffer else 1
        readable, writable, exceptional = select.select(
            [client_socket,read_socket], [], [], timeout
        )

        # incoming data; process it
        if client_socket in readable:
            data = client_socket.recv(1024) # the server will tell if the client is registered or not

            if not data:
                print("Server disconnected.")
                return
            
            buffer += data

        messages, buffer = extract_messages(buffer)

        for message in messages:
            try:
                info = message.decode('utf-8')
            except UnicodeDecodeError:
                print("Received non-UTF-8 data from the server, skipping...")
                continue

            # show the recipient the message the client sent
            # if the server sends something to the client, the name will be 'Server
            try:
                message_info = json.loads(info)
                print(f"<{message_info["sender"]}>: {message_info["message"]}")
            except json.JSONDecodeError:
                print(f"<Server>: {info}")

        # incoming notification; process it
        if read_socket in readable:
            signals = read_socket.recv(1024)

            for signal in signals:
                if signal == ord('M'):
                    # Retrieve and send outgoing message
                    try:
                        message = out_going.get_nowait()
                        client_socket.sendall(message)
                    except queue.Empty:
                        continue
                    except OSError as e:
                        print(f"Send failed: {e}")
                        stop_event.set()
                        break
                elif signal == ord('Q'):
                    # Stop the communication
                    stop_event.set()
                    break

if __name__ == '__main__':
    client()