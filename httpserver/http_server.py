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
    print("=" * 45)
    print("  ReliableUDP HTTP Server starting...")
    print("  Listening on 127.0.0.1:8080")
    print("=" * 45)

    while True:
        # Create a fresh ReliableUDP instance for each connection
        # (each Postman request from the bridge = one full handshake cycle)
        server = ReliableUDP("127.0.0.1", 8080, is_server=True)

        print("\n[Server] Waiting for new connection...")
        server.handshake_server()
        server.sock.settimeout(10)

        try:
            request = server.receive()
            print("\n[Server] HTTP Request received:\n")
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

            # Wait for client FIN to close cleanly
            server.sock.settimeout(5)
            server.close_server()

        except Exception as e:
            print(f"[Server] Error handling request: {e}")
            try:
                server.sock.close()
            except Exception:
                pass

        print("[Server] Connection closed. Ready for next request.\n")