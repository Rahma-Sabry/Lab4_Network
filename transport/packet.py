import json

def checksum(data):
    return sum(bytearray(data.encode())) % 256


def create_packet(seq, ack, flags, data):
    packet = {
        "seq": seq,
        "ack": ack,
        "flags": flags,
        "data": data,
    }
    packet["checksum"] = checksum(data)
    return json.dumps(packet).encode()


def parse_packet(data):
    return json.loads(data.decode())


def is_valid(packet):
    return packet["checksum"] == checksum(packet["data"])