import json


def compute_checksum(seq, ack, flags, data):
    content = f"{seq}|{ack}|{'-'.join(flags)}|{data}"
    return sum(content.encode()) % 256


def create_packet(seq, ack, flags, data):
    packet = {
        "seq": seq,
        "ack": ack,
        "flags": flags,
        "data": data,
    }
    packet["checksum"] = compute_checksum(seq, ack, flags, data)
    return json.dumps(packet).encode()


def parse_packet(raw_data):
    return json.loads(raw_data.decode())


def is_valid(packet):
    expected = compute_checksum(
        packet["seq"],
        packet["ack"],
        packet["flags"],
        packet["data"],
    )
    return packet["checksum"] == expected