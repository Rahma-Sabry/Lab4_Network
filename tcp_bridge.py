
import socket
import threading
import sys
import os

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 7000          
UDP_SERVER_HOST = "127.0.0.1"
UDP_SERVER_PORT = 8080      

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transport.reliable_udp import ReliableUDP


def handle_client(tcp_conn, client_addr):

    print(f"\n[Bridge] New connection from {client_addr}")

    try:
        tcp_conn.settimeout(5)
        raw = b""
        while True:
            try:
                chunk = tcp_conn.recv(4096)
                if not chunk:
                    break
                raw += chunk
                # Stop once we have a complete HTTP request
                # (headers end at \r\n\r\n; for POST we also wait for body)
                if b"\r\n\r\n" in raw:
                    header_part, _, body_so_far = raw.partition(b"\r\n\r\n")
                    headers_text = header_part.decode(errors="replace")

                    # Check Content-Length to know if we need to read a body
                    content_length = 0
                    for line in headers_text.split("\r\n")[1:]:
                        if line.lower().startswith("content-length:"):
                            content_length = int(line.split(":", 1)[1].strip())
                            break

                    if len(body_so_far) >= content_length:
                        break   # we have the whole request

            except socket.timeout:
                break   # stop waiting, send what we have

        if not raw:
            print("[Bridge] Empty request, closing.")
            tcp_conn.close()
            return

        http_request = raw.decode(errors="replace")
        print(f"[Bridge] Received HTTP request:\n{http_request[:300]}")

        udp_client = ReliableUDP(UDP_SERVER_HOST, UDP_SERVER_PORT)
        udp_client.handshake_client()
        udp_client.send(http_request)
        http_response = udp_client.receive()
        udp_client.close_client()

        print(f"[Bridge] Got UDP response:\n{http_response[:300]}")

        tcp_conn.sendall(http_response.encode())
        print("[Bridge] Response sent to Postman.")

    except Exception as e:
        print(f"[Bridge] Error: {e}")
        error_resp = (
            "HTTP/1.0 500 Internal Server Error\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 21\r\n"
            "\r\n"
            "Bridge error occurred."
        )
        try:
            tcp_conn.sendall(error_resp.encode())
        except Exception:
            pass

    finally:
        tcp_conn.close()


def run_bridge():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((BRIDGE_HOST, BRIDGE_PORT))
    server_sock.listen(5)

    print("=" * 55)
    print(f"  TCP-to-UDP Bridge running")
    print(f"  Postman  →  http://{BRIDGE_HOST}:{BRIDGE_PORT}/")
    print(f"  Bridge   →  UDP server at {UDP_SERVER_HOST}:{UDP_SERVER_PORT}")
    print("=" * 55)
    print("Waiting for connections...\n")

    while True:
        try:
            conn, addr = server_sock.accept()
            # Handle each Postman request in its own thread
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
        except KeyboardInterrupt:
            print("\n[Bridge] Shutting down.")
            break

    server_sock.close()


if __name__ == "__main__":
    run_bridge()
