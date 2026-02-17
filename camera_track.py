# camera_track.py
import cv2
import av
from aiortc import VideoStreamTrack


class CameraVideoTrack(VideoStreamTrack):
    """
    A video track that reads frames from a local webcam using OpenCV.
    """
    kind = "video"

    def __init__(self, device_index: int = 0):
        super().__init__()
        self.cap = cv2.VideoCapture(device_index)

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {device_index}")

        # Optional: set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        print(f"[CAMERA] Opened device {device_index} — "
              f"{int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x"
              f"{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from camera")

        # OpenCV gives BGR — convert to RGB for aiortc / libav
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        video_frame = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

    def __del__(self):
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
            print("[CAMERA] Released")