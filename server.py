# server.py
import asyncio
import json
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from camera_track import CameraVideoTrack

pcs = set()


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    pc = RTCPeerConnection()
    pcs.add(pc)
    print("[WS] New client connected")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                msg_type = data.get("type")

                if msg_type == "offer":
                    print("[SDP] Received offer")

                    offer = RTCSessionDescription(sdp=data["sdp"], type="offer")
                    await pc.setRemoteDescription(offer)

                    # Add camera track AFTER setRemoteDescription
                    pc.addTrack(CameraVideoTrack())

                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)

                    # Wait for ICE gathering to complete so candidates are in SDP
                    while pc.iceGatheringState != "complete":
                        await asyncio.sleep(0.05)

                    print("[SDP] Sending answer (ICE complete)")
                    await ws.send_json({
                        "type": pc.localDescription.type,
                        "sdp": pc.localDescription.sdp,
                    })

                else:
                    print(f"[WS] Unknown message type: {msg_type}")

            elif msg.type == web.WSMsgType.ERROR:
                print(f"[WS] Error: {ws.exception()}")
                break

    finally:
        print("[WS] Client disconnected")
        await pc.close()
        pcs.discard(pc)

    return ws


async def on_shutdown(app):
    print("[SERVER] Shutting down, closing peer connections...")
    coros = [pc.close() for pc in list(pcs)]
    await asyncio.gather(*coros)
    pcs.clear()


@web.middleware
async def no_cache_middleware(request, handler):
    response = await handler(request)
    response.headers["Cache-Control"] = "no-store"
    return response


app = web.Application(middlewares=[no_cache_middleware])
app.router.add_get("/ws", websocket_handler)
app.router.add_get("/", lambda r: web.FileResponse("static/index.html"))
app.router.add_static("/static/", "static")
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    print("[SERVER] Starting on http://0.0.0.0:8080")
    web.run_app(app, host="0.0.0.0", port=8080)