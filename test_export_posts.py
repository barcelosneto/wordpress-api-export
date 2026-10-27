import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from export_posts import export_posts, fetch_json


def item(identifier, title="Olá &amp; <b>WordPress</b>"):
    return {"id": identifier, "title": {"rendered": title}, "link": "https://example.org/post/", "date_gmt": "2026-10-27T12:00:00"}


class ExportTests(unittest.TestCase):
    def test_pagination_and_title(self):
        calls = []
        def fetch(url):
            calls.append(url)
            return [item(len(calls))], {"X-WP-TotalPages": "2"}
        result = export_posts("https://example.org", per_page=1, fetch=fetch)
        self.assertEqual(result["total_posts_read"], 2)
        self.assertEqual(result["posts"][0]["title"], "Olá & WordPress")
        self.assertIn("page=2", calls[1])
        self.assertFalse(result["truncated"])

    def test_page_cap_marks_truncation(self):
        result = export_posts("https://example.org", max_pages=1, per_page=1,
                              fetch=lambda _: ([item(1)], {"x-wp-totalpages": "9"}))
        self.assertTrue(result["truncated"])

    def test_missing_pagination_header(self):
        result = export_posts("https://example.org", fetch=lambda _: ([item(1)], {}))
        self.assertEqual(result["pages_read"], 1)
        self.assertFalse(result["truncated"])

    def test_bad_contract_and_duplicate(self):
        for payload in ({"code": "error"}, [{"id": True}], [item(1), item(1)]):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                export_posts("https://example.org", fetch=lambda _: (payload, {}))

    def test_input_validation(self):
        for site in ("http://example.org", "https://user:password@example.org", "https://example.org?key=secret"):
            with self.subTest(site=site), self.assertRaises(ValueError):
                export_posts(site)
        with self.assertRaises(ValueError):
            export_posts("https://example.org", max_pages=0)

    def test_transport_failure_propagates_without_partial_result(self):
        def fetch(url):
            raise TimeoutError("timeout demonstrativo")
        with self.assertRaises(TimeoutError):
            export_posts("https://example.org", fetch=fetch)

    def test_http_transport_uses_get_and_reads_json(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                data = json.dumps([item(1)]).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-WP-TotalPages", "1")
                self.end_headers()
                self.wfile.write(data)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            payload, headers = fetch_json(f"http://127.0.0.1:{server.server_port}/posts")
            self.assertEqual(payload[0]["id"], 1)
            self.assertEqual(headers["X-WP-TotalPages"], "1")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
