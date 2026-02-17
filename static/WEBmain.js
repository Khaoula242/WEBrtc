// WEBmain.js
(() => {
  // ─── State ────────────────────────────────────────────────────────────────
  let pc = null;
  let ws = null;

  const video   = document.getElementById("remoteVideo");
  const status  = document.getElementById("status");
  const startBtn = document.getElementById("startBtn");
  const stopBtn  = document.getElementById("stopBtn");

  // ─── UI helpers ───────────────────────────────────────────────────────────
  function setStatus(text, type = "info") {
    status.textContent = text;
    status.className = `status ${type}`;
  }

  function setButtons(streaming) {
    startBtn.disabled = streaming;
    stopBtn.disabled  = !streaming;
  }

  // ─── Start streaming ──────────────────────────────────────────────────────
  async function startStream() {
    setStatus("Connecting…", "info");
    setButtons(false);

    // 1. Open WebSocket
    const wsUrl = `ws://${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onclose = () => {
      setStatus("Disconnected", "error");
      setButtons(false);
      cleanup();
    };

    ws.onerror = (e) => {
      setStatus("WebSocket error", "error");
      console.error("[WS] error", e);
    };

    ws.onopen = async () => {
      setStatus("WebSocket open — creating offer…", "info");

      // 2. Create peer connection
      pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });

      // 3. Expect an incoming video track (recvonly)
      pc.addTransceiver("video", { direction: "recvonly" });

      // 4. Show remote stream
      pc.ontrack = (event) => {
        console.log("[PC] ontrack", event.track.kind);
        video.srcObject = event.streams[0];
        setStatus("Streaming ▶", "ok");
        setButtons(true);
      };

      pc.onconnectionstatechange = () => {
        console.log("[PC] connectionState:", pc.connectionState);
        if (pc.connectionState === "failed") {
          setStatus("Connection failed", "error");
          stopStream();
        }
      };

      // 5. Create and send offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      ws.send(JSON.stringify({ type: "offer", sdp: offer.sdp }));
      setStatus("Offer sent — waiting for answer…", "info");
    };

    // 6. Handle server messages
    ws.onmessage = async (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        console.warn("[WS] Non-JSON message ignored:", event.data);
        return;
      }

      if (data.type === "answer") {
        console.log("[SDP] Received answer");
        await pc.setRemoteDescription(new RTCSessionDescription(data));
        setStatus("Answer received — connecting…", "info");
      }
    };
  }

  // ─── Stop streaming ───────────────────────────────────────────────────────
  function stopStream() {
    cleanup();
    setStatus("Stopped", "info");
    setButtons(false);
  }

  function cleanup() {
    if (video.srcObject) {
      video.srcObject.getTracks().forEach((t) => t.stop());
      video.srcObject = null;
    }
    if (pc) { pc.close(); pc = null; }
    if (ws) { ws.close(); ws = null; }
  }

  // ─── Button events ────────────────────────────────────────────────────────
  startBtn.addEventListener("click", startStream);
  stopBtn.addEventListener("click", stopStream);
})();