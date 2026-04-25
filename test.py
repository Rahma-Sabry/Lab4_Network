import unittest
from transport.packet import create_packet, parse_packet, is_valid
from httpserver.http_protocol import build_get, build_post, parse_request, build_response


class TestPacket(unittest.TestCase):
    def test_packet_valid(self):
        raw = create_packet(1, 0, ["DATA"], "hello")
        packet = parse_packet(raw)
        self.assertTrue(is_valid(packet))

    def test_packet_invalid_checksum(self):
        raw = create_packet(1, 0, ["DATA"], "hello")
        packet = parse_packet(raw)
        packet["checksum"] += 1
        self.assertFalse(is_valid(packet))


class TestHTTPProtocol(unittest.TestCase):
    def test_build_get(self):
        req = build_get("/index.html")
        self.assertIn("GET /index.html HTTP/1.0", req)

    def test_build_post(self):
        req = build_post("/submit", "hello")
        self.assertIn("POST /submit HTTP/1.0", req)
        self.assertIn("Content-Length: 5", req)
        self.assertTrue(req.endswith("hello"))

    def test_parse_get_request(self):
        req = "GET /index.html HTTP/1.0\r\nHost: localhost\r\n\r\n"
        method, path, version, headers, body = parse_request(req)
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/index.html")
        self.assertEqual(version, "HTTP/1.0")
        self.assertEqual(headers["Host"], "localhost")
        self.assertEqual(body, "")

    def test_parse_post_request(self):
        req = "POST /submit HTTP/1.0\r\nContent-Length: 5\r\n\r\nhello"
        method, path, version, headers, body = parse_request(req)
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/submit")
        self.assertEqual(body, "hello")

    def test_build_response(self):
        resp = build_response("200 OK", "hello")
        self.assertIn("HTTP/1.0 200 OK", resp)
        self.assertIn("Content-Length: 5", resp)
        self.assertTrue(resp.endswith("hello"))


if __name__ == "__main__":
    unittest.main()