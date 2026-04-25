from transport.reliable_udp import ReliableUDP
from .http_protocol import build_get


def run_client():
    client = ReliableUDP("127.0.0.1", 5000)

    client.handshake_client()

    request = build_get("/index.html")

    client.send(request)

    response = client.receive()
    print("HTTP Response:\n", response)