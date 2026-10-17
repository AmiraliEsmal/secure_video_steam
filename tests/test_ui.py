import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrowserContractTests(unittest.TestCase):
    def test_page_has_accessible_player_and_status(self):
        html = (ROOT / "web/index.html").read_text()
        self.assertIn('id="video-list"', html)
        self.assertIn('id="player"', html)
        self.assertIn('id="status" role="status"', html)
        self.assertIn("Teaching cipher only", html)

    def test_javascript_matches_python_known_vector_and_offsets(self):
        script = """
const lab = require('./web/cipher.js');
const whole = lab.keystream(24, 0xace1);
const part = lab.keystream(7, 0xace1, 9);
const periodic = lab.keystream(24, 0xace1, 65535);
process.stdout.write(JSON.stringify({vector: Buffer.from(whole.slice(0, 4)).toString('hex'), part: [...part], expected: [...whole.slice(9, 16)], periodic: [...periodic], whole: [...whole]}));
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
        )
        values = json.loads(result.stdout)
        self.assertEqual(values["vector"], "873544e2")
        self.assertEqual(values["part"], values["expected"])
        self.assertEqual(values["periodic"], values["whole"])

    def test_networking_and_ordering_are_completed(self):
        javascript = (ROOT / "web/app.js").read_text()
        worker = (ROOT / "web/service-worker.js").read_text()
        self.assertIn("navigator.serviceWorker.register", javascript)
        self.assertIn('updateViaCache: "none"', javascript)
        self.assertIn("player.muted = false", javascript)
        self.assertIn("/decrypted/", javascript)
        self.assertIn('request.headers.get("Range")', worker)
        self.assertIn("Content-Range", worker)
        self.assertIn("new ReadableStream", worker)
        self.assertIn("LfsrCipher.xorBytes", worker)
        self.assertNotIn("TODO(student)", worker)

    def test_service_worker_streams_the_complete_requested_range(self):
        script = """
const fs = require('fs');
const vm = require('vm');
const context = {
  self: { addEventListener() {}, skipWaiting() {}, clients: { claim() {} }, location: { origin: 'http://local' } },
  importScripts() {}, fetch() {}, LfsrCipher: {}, ReadableStream, Response, URL, Map, Promise,
  Number, Error, Uint8Array,
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('./web/service-worker.js', 'utf8'), context);
const request = (value) => ({ headers: { get: () => value } });
process.stdout.write(JSON.stringify({
  open: context.requestedRange(request('bytes=0-'), 1000),
  explicit: context.requestedRange(request('bytes=100-399'), 1000),
  suffix: context.requestedRange(request('bytes=-50'), 1000),
}));
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
        )
        ranges = json.loads(result.stdout)
        self.assertEqual(ranges["open"], {"start": 0, "length": 1000})
        self.assertEqual(ranges["explicit"], {"start": 100, "length": 300})
        self.assertEqual(ranges["suffix"], {"start": 950, "length": 50})


if __name__ == "__main__":
    unittest.main()
