import socket

def client():
    host = '127.0.0.1' # address for local testing
    port = 5000 # server's socket port number

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4 TCP socket
    client_socket.connect((host, port)) # connect to the server

    message = input(" -> ") # get input

    while message.lower().strip() != 'bye':
        # Send a message
        client_socket.sendall(message.encode())
        raw_message = client_socket.recv(1024)

        if not raw_message:
            break
        try:
            data = raw_message.decode('utf-8')
        except UnicodeDecodeError:
            print("Received non-UTF-8 data from the server, skipping...")
            continue

        # Show output in the terminal
        print('Received from server: ' + data)

        message = input(" -> ") # get input again

    client_socket.close() # close the connection


if __name__ == '__main__':
    client()