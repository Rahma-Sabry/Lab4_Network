from transport.reliable_udp import ReliableUDP
from http_protocol import parse_request, build_response


def run_server():
    server = ReliableUDP("127.0.0.1", 5000, is_server=True)

    server.handshake_server()

    while True:
        request = server.receive()
        print("HTTP Request:\n", request)

        method, path, body = parse_request(request)

        if method == "GET":
            try:
                with open("." + path) as f:
                    content = f.read()
                response = build_response("200 OK", content)
            except:
                response = build_response("404 NOT FOUND", "")

        elif method == "POST":
            response = build_response("200 OK", "POST received")

        server.send(response)