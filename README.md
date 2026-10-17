# LFSR Encrypted Video Lab

This classroom project demonstrates the mechanics—and limitations—of a synchronous stream cipher. A Flask server reads one of the bundled videos, XORs each requested range with bytes from a 16-bit LFSR, and sends only ciphertext. A browser service worker decrypts ranges on demand, so playback can begin while later parts remain encrypted and unfetched.

## Run

Python 3.11 or newer is required.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m stream_server --port 8000
```

Open <http://127.0.0.1:8000>, select a video, and press play when the first range is ready. Later ranges are decrypted during playback and seeking.