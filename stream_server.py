"""Flask server for the educational encrypted-video exercise."""

from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from stream_cipher import xor_bytes

ROOT = Path(__file__).resolve().parent
DEFAULT_VIDEOS = ROOT / "videos"
WEB_ROOT = ROOT / "web"
SEED = 0xACE1
MAX_CHUNK_SIZE = 256 * 1024
SUPPORTED_SUFFIXES = {".mp4", ".webm"}


def _video_catalog(video_dir: Path) -> dict[str, Path]:
    return {
        path.stem: path
        for path in sorted(video_dir.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    }


def _error(code: str, message: str, status: int):
    return jsonify(error={"code": code, "message": message}), status


def create_app(video_dir: Path | str = DEFAULT_VIDEOS) -> Flask:
    app = Flask(__name__, static_folder=None)
    catalog = _video_catalog(Path(video_dir).resolve())

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

    @app.get("/")
    def index():
        return send_from_directory(WEB_ROOT, "index.html")

    @app.get("/static/<path:name>")
    def static_file(name: str):
        if name not in {"app.js", "cipher.js", "styles.css"}:
            return _error("NOT_FOUND", "Static resource not found", 404)
        return send_from_directory(WEB_ROOT, name)

    @app.get("/api/videos")
    def videos():
        return jsonify(
            videos=[
                {
                    "id": video_id,
                    "name": path.stem.replace("_", " ").title(),
                    "size": path.stat().st_size,
                    "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                    "seed": SEED,
                }
                for video_id, path in catalog.items()
            ]
        )

    @app.get("/api/videos/<video_id>/chunk")
    def video_chunk(video_id: str):
        path = catalog.get(video_id)
        if path is None:
            return _error("VIDEO_NOT_FOUND", "Video not found", 404)
        try:
            offset = int(request.args["offset"])
            length = int(request.args["length"])
        except (KeyError, TypeError, ValueError):
            return _error("INVALID_RANGE", "offset and length must be integers", 400)

        size = path.stat().st_size
        if offset < 0 or length <= 0 or length > MAX_CHUNK_SIZE or offset + length > size:
            return _error("INVALID_RANGE", "Requested byte range is invalid", 400)

        with path.open("rb") as video:
            video.seek(offset)
            encrypted = xor_bytes(video.read(length), SEED, offset)
        return encrypted, 200, {
            "Content-Type": "application/octet-stream",
            "X-Chunk-Offset": str(offset),
            "X-Chunk-Length": str(length),
            "X-Video-Size": str(size),
            "X-Cipher-Seed": str(SEED),
        }

    @app.get("/service-worker.js")
    def service_worker():
        response = send_from_directory(WEB_ROOT, "service-worker.js")
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--videos", type=Path, default=DEFAULT_VIDEOS)
    args = parser.parse_args()
    create_app(args.videos).run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
