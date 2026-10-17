import tempfile
import unittest
from pathlib import Path

from stream_cipher import xor_bytes
from stream_server import create_app


class VideoApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        (root / "first.webm").write_bytes(bytes(range(256)) * 5)
        (root / "second.webm").write_bytes(b"second-video" * 89)
        (root / "ignored.txt").write_text("not media")
        self.app = create_app(root).test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lists_only_supported_videos(self):
        response = self.app.get("/api/videos")
        self.assertEqual(response.status_code, 200)
        videos = response.get_json()["videos"]
        self.assertEqual([video["id"] for video in videos], ["first", "second"])
        self.assertTrue(all(video["mime_type"] == "video/webm" for video in videos))

    def test_every_listed_video_round_trips_in_chunks(self):
        for video in self.app.get("/api/videos").get_json()["videos"]:
            encrypted = bytearray()
            for offset in range(0, video["size"], 113):
                length = min(113, video["size"] - offset)
                response = self.app.get(
                    f"/api/videos/{video['id']}/chunk?offset={offset}&length={length}"
                )
                self.assertEqual(response.status_code, 200)
                encrypted.extend(response.data)
            plaintext = xor_bytes(bytes(encrypted), video["seed"])
            source = Path(self.temp_dir.name, f"{video['id']}.webm").read_bytes()
            self.assertEqual(plaintext, source)

    def test_rejects_unknown_video_and_invalid_ranges(self):
        cases = [
            ("/api/videos/missing/chunk?offset=0&length=1", 404, "VIDEO_NOT_FOUND"),
            ("/api/videos/first/chunk?offset=nope&length=1", 400, "INVALID_RANGE"),
            ("/api/videos/first/chunk?offset=-1&length=1", 400, "INVALID_RANGE"),
            ("/api/videos/first/chunk?offset=0&length=0", 400, "INVALID_RANGE"),
            ("/api/videos/first/chunk?offset=0&length=9999999", 400, "INVALID_RANGE"),
        ]
        for url, status, code in cases:
            with self.subTest(url=url):
                response = self.app.get(url)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.get_json()["error"]["code"], code)

    def test_static_responses_include_security_headers(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Content-Security-Policy"], "default-src 'self'")
        response.close()

        worker = self.app.get("/service-worker.js")
        self.assertEqual(worker.status_code, 200)
        self.assertEqual(worker.headers["Service-Worker-Allowed"], "/")
        worker.close()


if __name__ == "__main__":
    unittest.main()
