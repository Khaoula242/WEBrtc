

window.addEventListener('load', async () => {
    const pc = new RTCPeerConnection({ iceServers: [] });
    const video = document.getElementById('video');

    pc.addTransceiver('video', { direction: 'recvonly' });

    pc.ontrack = event => {
        if (event.track.kind === 'video') {
        video.srcObject = event.streams[0];
        }
    };
  
    pc.onicecandidate = async e => {
      if (e.candidate === null) {
        const offer = pc.localDescription;
        try {
          const response = await fetch('/offer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(offer)
          });
          const answer = await response.json();
          await pc.setRemoteDescription(answer);
        } catch (err) {
          console.error('Error sending offer:', err);
        }
      }
    };
  
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
  });


