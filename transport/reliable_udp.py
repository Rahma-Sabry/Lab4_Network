import socket
import random
import json
from transport.packet import create_packet, parse_packet, is_valid

LOSS_RATE = 0.0
CORRUPT_RATE = 0.0
TIMEOUT = 2
BUFFER_SIZE = 65535


def ack_match(packet, expected):
    return packet["ack"] == expected


class ReliableUDP:
    def __init__(self, ip, port, is_server=False):
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(TIMEOUT)

        self.seq = 0
        self.expected_seq = 0
        self.is_server = is_server
        self.client_addr = None

        if is_server:
            self.sock.bind(self.addr)

    # -------------------------
    # Simulation helpers
    # -------------------------
    def _simulate_loss(self):
        return random.random() < LOSS_RATE

    def _maybe_corrupt_bytes(self, packet_bytes):
        if random.random() < CORRUPT_RATE:
            packet = parse_packet(packet_bytes)
            packet["checksum"] = (packet["checksum"] + 1) % 256
            print("Simulating packet corruption")
            return json.dumps(packet).encode()
        return packet_bytes

    def _send_raw(self, packet_bytes, destination, simulate=True):
        packet = parse_packet(packet_bytes)

        should_simulate = simulate and ("DATA" in packet["flags"])

        if should_simulate and self._simulate_loss():
            print("Simulating packet loss")
            return

        if should_simulate:
            packet_bytes = self._maybe_corrupt_bytes(packet_bytes)

        self.sock.sendto(packet_bytes, destination)

    def _peer_addr(self):
        return self.client_addr if self.is_server else self.addr

    # -------------------------
    # Handshake
    # -------------------------
    def handshake_client(self):
        syn = create_packet(self.seq, 0, ["SYN"], "")
        print("Client: Sending SYN")

        while True:
            self._send_raw(syn, self.addr, simulate=False)
            try:
                data, _ = self.sock.recvfrom(BUFFER_SIZE)
                packet = parse_packet(data)

                if not is_valid(packet):
                    print("Client: Corrupted SYN-ACK dropped")
                    continue

                if "SYN-ACK" in packet["flags"]:
                    print("Client: Received SYN-ACK")
                    ack = create_packet(self.seq, packet["seq"], ["ACK"], "")
                    self._send_raw(ack, self.addr, simulate=False)
                    print("Client: Connection established")
                    return
            except socket.timeout:
                print("Client: Timeout waiting for SYN-ACK, resending SYN")

    def handshake_server(self):
        print("Server: Waiting for SYN")

        while True:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue

            packet = parse_packet(data)

            if not is_valid(packet):
                print("Server: Corrupted SYN dropped")
                continue

            if "SYN" in packet["flags"]:
                print("Server: Received SYN")
                self.client_addr = addr
                syn_ack = create_packet(0, packet["seq"], ["SYN-ACK"], "")
                self._send_raw(syn_ack, addr, simulate=False)

                while True:
                    try:
                        data, addr2 = self.sock.recvfrom(BUFFER_SIZE)
                        ack = parse_packet(data)

                        if not is_valid(ack):
                            print("Server: Corrupted ACK dropped")
                            continue

                        if addr2 == addr and "ACK" in ack["flags"]:
                            print("Server: Connection established")
                            return
                    except socket.timeout:
                        print("Server: Timeout waiting for ACK, resending SYN-ACK")
                        self._send_raw(syn_ack, addr, simulate=False)

    # -------------------------
    # Reliable send (Stop-and-Wait)
    # -------------------------
    def send(self, data):
        packet = create_packet(self.seq, 0, ["DATA"], data)
        destination = self._peer_addr()

        while True:
            self._send_raw(packet, destination)
            print(f"Sent DATA seq={self.seq}")

            try:
                resp, _ = self.sock.recvfrom(BUFFER_SIZE)
                ack = parse_packet(resp)

                if not is_valid(ack):
                    print("Corrupted ACK dropped")
                    continue

                if "ACK" in ack["flags"] and ack["ack"] == self.seq:
                    print(f"ACK received for seq={self.seq}")
                    self.seq += 1
                    return
            except socket.timeout:
                print(f"Timeout waiting for ACK of seq={self.seq}, resending")

    # -------------------------
    # Reliable receive
    # -------------------------
    def receive(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                print("Receive timeout, still waiting...")
                continue

            packet = parse_packet(data)

            if not is_valid(packet):
                print("Corrupted packet dropped")
                continue

            if "DATA" in packet["flags"]:
                if packet["seq"] == self.expected_seq:
                    print(f"Received expected DATA seq={packet['seq']}")
                    ack = create_packet(0, packet["seq"], ["ACK"], "")
                    self._send_raw(ack, addr)
                    self.expected_seq += 1
                    return packet["data"]

                elif packet["seq"] < self.expected_seq:
                    print(f"Duplicate DATA seq={packet['seq']} received, re-sending ACK")
                    ack = create_packet(0, packet["seq"], ["ACK"], "")
                    self._send_raw(ack, addr)

                else:
                    print(f"Out-of-order packet seq={packet['seq']} dropped")

    # -------------------------
    # Connection teardown
    # -------------------------
    def close_client(self):
        fin = create_packet(self.seq, 0, ["FIN"], "")
        destination = self._peer_addr()

        while True:
            self._send_raw(fin, destination, simulate=False)
            print("Client: Sent FIN")
            try:
                data, _ = self.sock.recvfrom(BUFFER_SIZE)
                packet = parse_packet(data)

                if not is_valid(packet):
                    continue

                if "ACK" in packet["flags"] and ack_match(packet, self.seq):
                    print("Client: FIN acknowledged")
                    self.sock.close()
                    return
            except socket.timeout:
                print("Client: Timeout waiting for FIN-ACK, resending FIN")

    def close_server(self):
        while True:
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            packet = parse_packet(data)

            if not is_valid(packet):
                continue

            if "FIN" in packet["flags"]:
                print("Server: Received FIN")
                ack = create_packet(0, packet["seq"], ["ACK"], "")
                self._send_raw(ack, addr, simulate=False)
                self.sock.close()
                print("Server: Connection closed")
                return