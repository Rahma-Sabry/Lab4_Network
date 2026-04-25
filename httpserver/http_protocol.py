def build_get(path):
    return f"GET {path} HTTP/1.0\r\nHost: localhost\r\n\r\n"


def build_post(path, body):
    return (
        f"POST {path} HTTP/1.0\r\n"
        f"Host: localhost\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Content-Type: text/plain\r\n"
        f"\r\n"
        f"{body}"
    )


def parse_request(req):
    header_part, _, body = req.partition("\r\n\r\n")
    lines = header_part.split("\r\n")
    method, path, version = lines[0].split()

    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()

    return method, path, version, headers, body


def build_response(status, body, content_type="text/plain"):
    return (
        f"HTTP/1.0 {status}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
        f"{body}"
    )