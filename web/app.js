"use strict";

let currentVideo = null;

async function ensureServiceWorker() {
  if (!("serviceWorker" in navigator)) throw new Error("This browser does not support service workers");
  const workerUrl = "/service-worker.js?v=3";
  await navigator.serviceWorker.register(workerUrl, { scope: "/", updateViaCache: "none" });
  await navigator.serviceWorker.ready;
  if (!navigator.serviceWorker.controller || !navigator.serviceWorker.controller.scriptURL.endsWith(workerUrl)) {
    await new Promise((resolve) => navigator.serviceWorker.addEventListener("controllerchange", resolve, { once: true }));
  }
}

async function selectVideo(video) {
  const status = document.querySelector("#status");
  const player = document.querySelector("#player");
  currentVideo = video.id;
  status.textContent = `Preparing encrypted stream for ${video.name}…`;
  try {
    await ensureServiceWorker();
    if (currentVideo !== video.id) return;
    player.muted = false;
    player.volume = 1;
    player.src = `/decrypted/${encodeURIComponent(video.id)}`;
    player.load();
    status.textContent = `${video.name} is ready. Playback decrypts later ranges as needed.`;
    player.addEventListener("canplay", () => {
      if (currentVideo === video.id) status.textContent = `${video.name} can play while the rest decrypts.`;
    }, { once: true });
  } catch (error) {
    status.textContent = `Could not prepare ${video.name}. ${error.message}`;
  }
}

async function loadVideoList() {
  const list = document.querySelector("#video-list");
  const status = document.querySelector("#status");
  try {
    const response = await fetch("/api/videos");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const { videos } = await response.json();
    list.replaceChildren(...videos.map((video) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = video.name;
      const details = document.createElement("span");
      details.textContent = `${(video.size / 1024 / 1024).toFixed(1)} MiB`;
      button.append(details);
      button.addEventListener("click", () => selectVideo(video));
      return button;
    }));
    status.textContent = videos.length ? "Choose a video." : "No videos are available.";
  } catch (error) {
    status.textContent = `Could not load the video list. ${error.message}`;
  }
}

loadVideoList();
