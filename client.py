import socket
import json
import select
import threading
import queue

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
        receive_messages(client_socket, out_going, read_socket, stop_event)
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
        out_going.put(json_info.encode('utf-8'))

        try:
        # tell the main thread to get the message from the queue
            write_socket.sendall(b'M')
        # if it doesn't get sent, stop the operation
        except OSError as e:
            print(f"Notification failed: {e}")
            stop_event.set()
            break 


def receive_messages(client_socket,out_going, read_socket, stop_event):
    while not stop_event.is_set():
        readable, writable, exceptional = select.select(
            [client_socket,read_socket], [], [], 1
        )

        # incoming data; process it
        if client_socket in readable:
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