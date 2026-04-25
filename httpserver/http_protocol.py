def build_get(path):
    return f"GET {path} HTTP/1.0\r\n\r\n"


def build_post(path, body):
    return f"POST {path} HTTP/1.0\r\nContent-Length: {len(body)}\r\n\r\n{body}"


def parse_request(req):
    lines = req.split("\r\n")
    method, path, _ = lines[0].split()
    body = lines[-1] if method == "POST" else ""
    return method, path, body


def build_response(status, body):
    return f"HTTP/1.0 {status}\r\nContent-Length: {len(body)}\r\n\r\n{body}"