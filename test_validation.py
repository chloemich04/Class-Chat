import socket
from protocol import frame_message

host = "127.0.0.1"
port = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
    test_socket.settimeout(5)
    test_socket.connect((host, port))

    # Register the test client
    test_socket.sendall(frame_message("TestClient"))

    with test_socket.makefile("rb") as responses:
        response = responses.readline().decode("utf-8").strip()
        print("Registration:", response)

        if response != "REGISTERED":
            raise RuntimeError("Registration failed.")

        # Invalid inputs
        test_message = [
            "This is not JSON",
            '["Bob", "Hello"]',
            '{"message": "Hello"}',
            '{"receiver": "Bob"}',
            '{"receiver": 123, "message": "Hello"}',
            '{"receiver": "Bob", "message": 123}'
        ]

        for message in test_message:
            print(f"\nSending: {message}")

            test_socket.sendall(frame_message(message))

            response = responses.readline().decode("utf-8").strip()
            print(f"Server response: {response}")

        # Verify continued communication
        test_socket.sendall(frame_message(
            '{"receiver": "Bob", "message": "Validation tests completed!"}'
        ))