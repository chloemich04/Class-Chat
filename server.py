import socket
import threading
import json
from protocol import frame_message, extract_messages

client_list = {}
client_locks = {}
lock = threading.Lock()  # separate threads during the connection

"""_summary_
This function will allow the server to have multiple clients in one connection
and talk to each other.
"""

def handle_clients(conn, addr):
    new_client = None
    buffer = b''
    
    try:
        registered = False

        print(f"Connection from: {addr}")

        # keeping adding incoming data to the buffer to be framed
        while b'\n' not in buffer:
            data = conn.recv(1024)

            if not data:
                return
            buffer += data

        # manually get the username from the data
        username_bytes, buffer = buffer.split(b'\n', 1)
        new_client = username_bytes.decode('utf-8')


        with lock:
            if new_client in client_list:
                # tell the client that this username is taken
                registered = False
            else:
                # the client is new; allow them in the server
                send_lock = threading.Lock()
                client_locks[new_client] = send_lock
                send_lock.acquire()
                client_list[new_client] = conn
                registered = True
                #print(client_list)

        # tell the client if the server accepted them or not
        if registered:
            try:
                conn.sendall(frame_message("REGISTERED"))
            finally:
                send_lock.release()
        else:
            conn.sendall(frame_message("USERNAME_TAKEN"))
            return

    
        # the client is connected; they can communicate
        while True:
            if b'\n' not in buffer:
                data = conn.recv(1024)

                if not data: # the client's connection is closed
                    break

                buffer += data

            # get full messages and send them to the correct recipient
            messages, buffer = extract_messages(buffer)

            for message in messages:
                try:
                    message_info = json.loads(message.decode('utf-8'))  # get the client's message
                except (json.JSONDecodeError, UnicodeDecodeError):
                    with send_lock:
                        conn.sendall(frame_message("Invalid message format."))
                        continue
                
                # check to make sure the requested message from the client is an acceptable request
                if not isinstance(message_info, dict):
                    with send_lock:
                        conn.sendall(frame_message("Message must be a JSON object."))
                        continue

                if "receiver" not in message_info or "message" not in message_info:
                    with send_lock:
                        conn.sendall(frame_message("Receiver and message fields are required."))
                        continue

                if not isinstance(message_info["receiver"], str):   
                    with send_lock:
                        conn.sendall(frame_message("Receiver must be a string."))
                        continue

                if not isinstance(message_info["message"], str):
                    with send_lock:
                        conn.sendall(frame_message("Message must be a string."))
                        continue

                if not message_info["receiver"].strip():
                    with send_lock:
                        conn.sendall(frame_message("Must provide a recipient."))
                    continue

                if not message_info["message"].strip():
                    with send_lock:
                        conn.sendall(frame_message("Must type a message."))
                    continue


                # client message request passed; send the message to the recipient
                receiver = message_info["receiver"]
                text = message_info["message"]

                message_info["sender"] = new_client


                print(f"**{new_client}** sent --{receiver}-- a message of: '{text}'")

                forward_message = frame_message(json.dumps(message_info))

                # get the client that's getting the message
                with lock:
                    receiver_socket = client_list.get(receiver)
                    receiver_lock = client_locks.get(receiver)

                if receiver_socket is not None and receiver_lock is not None:
                    try:
                        with receiver_lock:
                            receiver_socket.sendall(forward_message) # sending the client's message to their recipient

                    except OSError as e:
                        print(f"Delivery failed: {e}")
                        with send_lock:
                            conn.sendall(
                                frame_message(f"Failed to deliver message to '{receiver}'.")
                            )
                else:
                    with send_lock:
                        conn.sendall(frame_message(f"User '{receiver}' is not connected to the server."))

    except ConnectionResetError:
        print("Client disconnected unexpectedly")

    except BrokenPipeError:
        print("Send failed: client has closed the connection")

    except socket.timeout:
        print("Connection timed out")

    except OSError as e:
        print(f"Unexpected socket error: {e}")

    except UnicodeDecodeError:
        print("Invalid UTF-8 data received during registration.")

    finally:
        with lock: # only take out the necessary client
            if client_list.get(new_client) is conn:
                client_list.pop(new_client, None)
                client_locks.pop(new_client, None)
        conn.close()



def server():
    host = '127.0.0.1' # address for local testing
    port = 5000 # creating a port

    # IPv4 TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    # Allow port reuse immediately after server shutdown
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    # Bind host address and port together
    server_socket.bind((host, port))

    # The socket is listening for connections
    server_socket.listen(5)

    server_socket.settimeout(1.0)

    print(f"Server listening on {host}:{port}")

    try:
        while True:
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue

            # Let the server allow multiple clients
            thread = threading.Thread(
                target=handle_clients,
                args=(conn, addr),
                daemon=True
            )

            thread.start()
            print(f"Active connections: {threading.active_count() - 1}")
            
    except KeyboardInterrupt:
        print("Server shutting down")
    finally:
        server_socket.close() # close the listening socket


if __name__ == '__main__':
    server()
