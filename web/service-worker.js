"use strict";

importScripts("/static/cipher.js");

const MAX_RANGE_SIZE = 256 * 1024;
const RETRIES = 2;
let catalogPromise;

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

function catalog() {
  if (!catalogPromise) {
    catalogPromise = fetch("/api/videos")
      .then((response) => {
        if (!response.ok) throw new Error(`Video catalog failed: HTTP ${response.status}`);
        return response.json();
      })
      .then(({ videos }) => new Map(videos.map((video) => [video.id, video])));
  }
  return catalogPromise;
}

async function fetchEncrypted(url) {
  let lastError;
  for (let attempt = 0; attempt <= RETRIES; attempt += 1) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Encrypted range failed: HTTP ${response.status}`);
      return new Uint8Array(await response.arrayBuffer());
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

function requestedRange(request, size) {
  const range = request.headers.get("Range");
  if (!range) return { start: 0, length: size };
  const match = /^bytes=(\d*)-(\d*)$/.exec(range);
  if (!match || (!match[1] && !match[2])) return null;
  if (!match[1]) {
    const suffixLength = Math.min(Number(match[2]), size);
    return { start: size - suffixLength, length: suffixLength };
  }
  const start = Number(match[1]);
  const requestedLength = match[2] ? Number(match[2]) - start + 1 : size - start;
  return { start, length: Math.min(requestedLength, size - start) };
}

function decryptedStream(video, start, length) {
  let offset = start;
  const end = start + length;
  return new ReadableStream({
    async pull(controller) {
      if (offset >= end) {
        controller.close();
        return;
      }
      const chunkLength = Math.min(MAX_RANGE_SIZE, end - offset);
      try {
        const encrypted = await fetchEncrypted(
          `/api/videos/${encodeURIComponent(video.id)}/chunk?offset=${offset}&length=${chunkLength}`,
        );
        controller.enqueue(LfsrCipher.xorBytes(encrypted, video.seed, offset));
        offset += chunkLength;
      } catch (error) {
        controller.error(error);
      }
    },
    cancel() {
      offset = end;
    },
  });
}

async function decryptedRange(request, videoId) {
  const video = (await catalog()).get(videoId);
  if (!video) return new Response("Video not found", { status: 404 });
  const range = requestedRange(request, video.size);
  if (!range || !Number.isSafeInteger(range.start) || !Number.isSafeInteger(range.length)
      || range.start < 0 || range.start >= video.size || range.length <= 0) {
    return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${video.size}` } });
  }
  const { start, length } = range;
  return new Response(decryptedStream(video, start, length), {
    status: 206,
    headers: {
      "Accept-Ranges": "bytes",
      "Content-Length": String(length),
      "Content-Range": `bytes ${start}-${start + length - 1}/${video.size}`,
      "Content-Type": video.mime_type,
      "Cache-Control": "no-store",
    },
  });
}

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || !url.pathname.startsWith("/decrypted/")) return;
  const videoId = decodeURIComponent(url.pathname.slice("/decrypted/".length));
  event.respondWith(decryptedRange(event.request, videoId));
});
