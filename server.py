import socket

def server():
    host = '127.0.0.1' # address for local testing
    port = 5000 # creating a port

    # IPv4 TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    # Allow port reuse immediately after server shutdown
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    # Bind host address and port together
    server_socket.bind((host, port))

    # Up to 5 connection requests
    server_socket.listen(5)

    conn, address = server_socket.accept() # accept new connections
    print("Connection from: " + str(address))

    while True:
        raw_data = conn.recv(1024)

        if not raw_data:
            break
        try:
            data = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            print(f"Received non-UTF-8 data from {address}, skipping...")
            continue

        print("from connected user: " + str(data))
        data = input(' -> ')

        conn.sendall(data.encode()) # send data to the client

    conn.close() # close the server connection
    server_socket.close() # close the listening socket