def frame_message(message):
    fixed = message + "\n"
    return fixed.encode('utf-8')


def extract_messages(buffer):
    messages = []

    while b'\n' in buffer:
        message, buffer = buffer.split(b'\n',1)
        messages.append(message)

    return messages, buffer

if __name__ == '__main__':
    print(frame_message("Hello Alice!"))
    print(extract_messages(b'Hello\n'))
    print(extract_messages(b'Hello\nBye\n'))
    print(extract_messages(b'Hello\nGood'))
    print(extract_messages(b'Hel'))
    print(extract_messages(b''))