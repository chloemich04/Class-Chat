import socket
import json

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

    while True:
        # Send a message
        recipient = input("Who would you like to message: ")  # who are you texting
            
        text = input("What do you want to say -> ") # get input

        if text.lower().strip() == 'bye': # if the client types 'bye' they will be disconnected from the server
            break
    
        text_info = {
            "sender": username,
            "receiver": recipient,
            "message": text
        }
    
        json_info = json.dumps(text_info)
        client_socket.sendall(json_info.encode())
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

    client_socket.close() # close the connection


if __name__ == '__main__':
    client()