from transport.reliable_udp import ReliableUDP
from .http_protocol import parse_request, build_response
import os


def get_content_type(path):
    if path.endswith(".html"):
        return "text/html"
    if path.endswith(".txt"):
        return "text/plain"
    if path.endswith(".json"):
        return "application/json"
    return "text/plain"


def run_server():
    server = ReliableUDP("127.0.0.1", 5000, is_server=True)
    server.handshake_server()
    server.sock.settimeout(None)

    while True:
        request = server.receive()
        print("\nHTTP Request:\n")
        print(request)

        method, path, version, headers, body = parse_request(request)

        if method == "GET":
            file_path = "." + path
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                response = build_response("200 OK", content, get_content_type(file_path))
            else:
                response = build_response("404 NOT FOUND", "File not found")

        elif method == "POST":
            response = build_response("200 OK", f"POST received:\n{body}")

        else:
            response = build_response("400 BAD REQUEST", "Unsupported method")

        server.send(response)
        server.close_server()
        break