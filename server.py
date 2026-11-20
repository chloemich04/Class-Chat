import socket
import threading

client_list = []
lock = threading.Lock()  # separate threads during the connection

"""_summary_
This function will allow the server to have multiple clients in one connection
and talk to each other.
"""

def handle_clients(conn, addr):
    with lock:  # will release the lock when an exception occurs
        client_list.append(addr)

    print(f"Connection from: {addr}")

    try:
        while True:
            data = conn.recv(1024)
            if not data:  # the client's connection is closed
                break
            conn.sendall(data) # client's data is received
    except ConnectionResetError:
        print("Client disconnected unexpectedly")
    except BrokenPipeError:
        print("Send failed: client has closed the connection")
    except socket.timeout:
        print("Connection timed out")
    finally:
        with lock:
            client_list.remove(addr)
        conn.close()


    """_summary_
    The baseline server that allows clients to communicate
    """
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
