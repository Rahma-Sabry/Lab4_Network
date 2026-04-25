from transport.reliable_udp import ReliableUDP
from .http_protocol import build_get, build_post


def run_client():
    client = ReliableUDP("127.0.0.1", 5000)
    client.handshake_client()

    choice = input("Enter method (GET/POST): ").strip().upper()

    if choice == "POST":
        path = input("Enter path: ").strip()
        body = input("Enter body: ")
        request = build_post(path, body)
    else:
        path = input("Enter path: ").strip()
        request = build_get(path)

    client.send(request)
    response = client.receive()
    print("\nHTTP Response:\n")
    print(response)

    client.close_client()