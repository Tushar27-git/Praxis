import http.client
import json
import threading
import unittest

from coc_advisor.server import MAX_REQUEST, create_server
from test_planner import session


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result

    def test_serves_app_assets_with_correct_types(self):
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Scouting Lab", body)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        status, headers, _ = self.request("GET", "/app.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", headers["Content-Type"])

    def test_only_explicit_assets_are_accessible(self):
        for path in ["/research/FINAL_RESEARCH.md", "/../HANDOVER.md", "/%2e%2e/HANDOVER.md", "/favicon.ico"]:
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[0], 404)

    def test_real_planning_request(self):
        status, _, raw = self.request("POST", "/api/plan", json.dumps(session()), {"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["candidates"][0]["zone_id"], "west")

    def test_bad_json_and_schema_return_readable_errors(self):
        for payload in [b"{", b"\xff", b'{"x": NaN}', b"[]", json.dumps({"schema_version": 9}).encode()]:
            with self.subTest(payload=payload):
                status, _, raw = self.request("POST", "/api/plan", payload, {"Content-Type": "application/json"})
                self.assertEqual(status, 400)
                self.assertTrue(json.loads(raw)["error"])

    def test_rejects_cross_origin_and_wrong_host(self):
        status, _, _ = self.request("POST", "/api/plan", "{}", {"Origin": "https://example.com", "Content-Type": "application/json"})
        self.assertEqual(status, 403)
        self.assertEqual(self.request("GET", "/", headers={"Host": "example.com"})[0], 403)

    def test_rejects_non_json_and_oversized_payloads(self):
        self.assertEqual(self.request("POST", "/api/plan", "{}", {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/plan", b"", {"Content-Type": "application/json", "Content-Length": str(MAX_REQUEST + 1)})[0], 413)

    def test_huge_integer_returns_validation_error_instead_of_dropping_connection(self):
        data = session()
        data["annotations"][0]["x"] = 10**1000
        status, _, raw = self.request("POST", "/api/plan", json.dumps(data), {"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(raw))


if __name__ == "__main__":
    unittest.main()
