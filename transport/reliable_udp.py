import socket
import json
import random
import time
from transport.packet import create_packet, parse_packet, is_valid

LOSS_RATE = 0.0
CORRUPT_RATE = 0.0
TIMEOUT = 2


class ReliableUDP:
    def __init__(self, ip, port, is_server=False):
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(TIMEOUT)

        self.seq = 0
        self.expected_seq = 0
        self.is_server = is_server

        if is_server:
            self.sock.bind(self.addr)

    # ========================
    # Simulation
    # ========================
    def _simulate_loss(self):
        return random.random() < LOSS_RATE

    def _simulate_corruption(self, packet):
        if random.random() < CORRUPT_RATE:
            packet["checksum"] = 999
        return packet

    # ========================
    # Handshake
    # ========================
    def handshake_client(self):
        print("Client: Sending SYN")
        packet = create_packet(self.seq, 0, ["SYN"], "")

        while True:
            self.sock.sendto(packet, self.addr)

            try:
                data, _ = self.sock.recvfrom(1024)
                p = parse_packet(data)

                if "SYN-ACK" in p["flags"]:
                    print("Client: Received SYN-ACK")
                    ack = create_packet(self.seq, p["seq"], ["ACK"], "")
                    self.sock.sendto(ack, self.addr)
                    print("Client: Connection established")
                    return

            except socket.timeout:
                print("Client: Timeout, resend SYN")

    def handshake_server(self):
        print("Server: Waiting for SYN")

        while True:
            data, addr = self.sock.recvfrom(1024)
            p = parse_packet(data)

            if "SYN" in p["flags"]:
                print("Server: Received SYN")
                syn_ack = create_packet(0, p["seq"], ["SYN-ACK"], "")
                self.sock.sendto(syn_ack, addr)

                data, _ = self.sock.recvfrom(1024)
                ack = parse_packet(data)

                if "ACK" in ack["flags"]:
                    print("Server: Connection established")
                    self.client_addr = addr
                    return

    # ========================
    # Send
    # ========================
    def send(self, data):
        packet = create_packet(self.seq, 0, ["DATA"], data)

        while True:
            if not self._simulate_loss():
                self.sock.sendto(packet, self.addr if not self.is_server else self.client_addr)
                print(f"Sent seq {self.seq}")

            try:
                resp, _ = self.sock.recvfrom(1024)
                ack = parse_packet(resp)

                if ack["ack"] == self.seq:
                    print("ACK received")
                    self.seq += 1
                    return

            except socket.timeout:
                print("Timeout → Resending")

    # ========================
    # Receive
    # ========================
    def receive(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            packet = parse_packet(data)

            if not is_valid(packet):
                print("Corrupted packet dropped")
                continue

            if packet["seq"] == self.expected_seq:
                print(f"Received seq {packet['seq']}")
                self.expected_seq += 1

                ack = create_packet(0, packet["seq"], ["ACK"], "")
                self.sock.sendto(ack, addr)

                return packet["data"]
            else:
                print("Duplicate packet ignored")