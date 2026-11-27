import socket
import json
import time
from protocol import frame_message

host = "127.0.0.1"
port = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
    test_socket.settimeout(5)
    test_socket.connect((host, port))

    test_socket.sendall(frame_message("FramingClient"))

    with test_socket.makefile("rb") as responses:
        response = responses.readline().decode("utf-8").strip()
        print("Registration:", response)

        if response != "REGISTERED":
            raise RuntimeError("Registration failed.")

        # Test A: Fragmented message
        message = frame_message(json.dumps({
            "receiver": "Bob",
            "message": "Fragmented message test!"
        }))

        midpoint = len(message) // 2

        print("Sending first fragment...")
        test_socket.sendall(message[:midpoint])

        time.sleep(3)

        print("Sending second fragment...")
        test_socket.sendall(message[midpoint:])

        time.sleep(1)

        # Test B: Combined messages
        message1 = frame_message(json.dumps({
            "receiver": "Bob",
            "message": "Combined message 1"
        }))

        message2 = frame_message(json.dumps({
            "receiver": "Bob",
            "message": "Combined message 2"
        }))

        print("Sending two message together...")
        test_socket.sendall(message1 + message2)

        print("Framing tests completed.")