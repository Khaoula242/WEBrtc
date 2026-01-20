
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
import numpy as np
import cv2
from aiohttp import web
from camera_track import CameraVideoTrack



class CameraTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)  # PC webcam

        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        ret, frame = self.cap.read()
        if not ret:
            await asyncio.sleep(0.03)
            return await self.recv()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

    pc = RTCPeerConnection()
    pc.addTrack(CameraTrack())


    # negotiate
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # wait ICE
    while pc.iceGatheringState != 'complete':
        await asyncio.sleep(0.1)

    return web.json_response({
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    })

if __name__ == '__main__':
    app = web.Application()
    app.router.add_post('/offer', offer)
    app.router.add_get('/', lambda req: web.FileResponse('static/index.html'))
    app.router.add_static('/static/', path='static', show_index=False)

    web.run_app(app, host="0.0.0.0", port=8080)
    # #web.run_app(app, port=8080)

