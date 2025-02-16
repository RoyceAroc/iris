import picows
import asyncio
import uvloop
import uuid
import cv2


class VideoClient(picows.WSListener):
    def __init__(self) -> None:
        super().__init__()
        self.transport = None

        # Caption metadata
        self.captions = {}
        self.curr_caption_id = None

    async def send_frames(self, transport: picows.WSTransport) -> None:
        # Open the video file
        capture = cv2.VideoCapture("data/video/broll.mp4")
        if not capture.isOpened():
            raise ValueError("Error opening video file")

        # Retrieve FPS of video
        fps = capture.get(cv2.CAP_PROP_FPS) if capture.get(cv2.CAP_PROP_FPS) > 0 else 30
        interval = int(round(fps * 2))
        print(f"Video FPS: {fps}, frames to skip: {interval}")
        current_frame = 0

        # Begin sending frames to server at 2 FPS
        while True:
            # Read the next frame from the video
            ret, frame = capture.read()
            if not ret:
                break

            # Send the current frame once per second
            if current_frame % interval == 0:
                ret, buffer = cv2.imencode(".jpg", frame)
                if ret:
                    self.curr_caption_id = str(uuid.uuid4())
                    transport.send(
                        picows.WSMsgType.BINARY,
                        f"{self.curr_caption_id}|".encode() + buffer.tobytes(),
                    )

            current_frame += 1

        capture.release()

    def on_ws_connected(self, transport: picows.WSTransport) -> None:
        print("Established connection to server")
        self.transport = transport
        asyncio.create_task(self.send_frames(transport))

    def on_ws_frame(self, transport: picows.WSTransport, frame: picows.WSFrame) -> None:
        if frame.msg_type == picows.WSMsgType.TEXT:
            payload = frame.get_payload_as_ascii_text()
            caption_id, token = payload.split("|")
            token = token.strip()

            # If token is the <end> token, the caption has been completed
            if token == "<end>":
                if caption_id == self.curr_caption_id:
                    print("Received final caption, initiating disconnection")
                    transport.disconnect()
                return

            if caption_id not in self.captions:
                self.captions[caption_id] = token
            else:
                self.captions[caption_id] += " " + token

            print(f"---\n{self.captions}")


async def main() -> None:
    transport, _ = await picows.ws_connect(VideoClient, "ws://209.20.159.34:2222")
    await transport.wait_disconnected()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
