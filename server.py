import socket
import threading
import json

client_list = {}
lock = threading.Lock()  # separate threads during the connection

"""_summary_
This function will allow the server to have multiple clients in one connection
and talk to each other.
"""

def handle_clients(conn, addr):
    new_client = None
    
    try:
        registered = False

        print(f"Connection from: {addr}")

        new_client = conn.recv(1024).decode('utf-8')

        
        with lock:
            if new_client in client_list:
                # tell the client that this username is taken
                registered = False
            else:
                # the client is new; allow them in the server
                client_list[new_client] = conn
                registered = True
                print(client_list)

        # tell the client what the server decided
        if registered:
            conn.sendall("REGISTERED".encode('utf-8'))
        else:
            conn.sendall("USERNAME_TAKEN".encode('utf-8'))
            conn.close()
            return

    
        # the client is connected; they can communicate
        while True:
            data = conn.recv(1024)
            if not data: # the client's connection is closed
                break

            message_info = json.loads(data.decode('utf-8'))  # get the client's message

            receiver = message_info["receiver"]
            text = message_info["message"]

            message_info["sender"] = new_client


            print(f"**{new_client}** sent --{receiver}-- a message of: '{text}'")

            forward_message = json.dumps(message_info).encode('utf-8')

            # get the client that's getting the message
            with lock:
                receiver_socket = client_list.get(receiver)

            if receiver_socket is not None:
                try:
                    receiver_socket.sendall(forward_message) # sending the client's message to their recipient

                except OSError as e:
                    print(f"Delivery failed: {e}")
                    conn.sendall(
                        f"Failed to deliver message to '{receiver}'.".encode('utf-8')
                    )
            else:
                conn.sendall(f"User '{receiver}' is not connected to the server.".encode('utf-8'))

    except ConnectionResetError:
        print("Client disconnected unexpectedly")

    except BrokenPipeError:
        print("Send failed: client has closed the connection")

    except socket.timeout:
        print("Connection timed out")

    finally:
        with lock: # only take out the necessary client
            if client_list.get(new_client) is conn:
                client_list.pop(new_client, None)
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

    print(f"Server listening on {host}:{port}")

    try:
        while True:
            conn, addr = server_socket.accept()
            # Let the server allow multiple clients
            thread = threading.Thread(target=handle_clients, args=(conn, addr), daemon=True)
            thread.start()
            print(f"Active connections: {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("Server shutting down")
    finally:
        server_socket.close() # close the listening socket


if __name__ == '__main__':
    server()
