import transformers
import asyncio
import picows
import uvloop

from models.base import Frame, DeviceModel, VendorModel, FrameStatus
from models.llava import LlavaModel
from models.groq import LlamaVisionModel

transformers.logging.set_verbosity_error()


class Server(picows.WSListener):
    def __init__(
        self,
        caption_model: DeviceModel,
        classify_model: VendorModel,
    ) -> None:
        self.caption_model = caption_model
        self.classify_model = classify_model
        super().__init__()

    def handle_frame(
        self, transport: picows.WSTransport, scene_frame: Frame, caption_id: str
    ) -> None:
        classification_result = self.classify_model.classify(scene_frame)
        print(f"Classification result for {caption_id}: {classification_result}")

        # If safe, don't process further
        if classification_result == FrameStatus.Safe:
            return

        # If hazard, stream all tokens
        for token in self.caption_model.caption(scene_frame):
            payload = f"{caption_id}|{token}".encode("utf-8")
            transport.send(picows.WSMsgType.TEXT, payload)

        # Send end token for hazard cases
        end_payload = f"{caption_id}|<end>".encode("utf-8")
        transport.send(picows.WSMsgType.TEXT, end_payload)

    def on_ws_connected(self, transport: picows.WSTransport) -> None:
        print("New client connected")

    def on_ws_frame(self, transport: picows.WSTransport, frame: picows.WSFrame) -> None:
        if frame.msg_type == picows.WSMsgType.BINARY:
            data = frame.get_payload_as_bytes()
            parts = data.split(b"|", 1)
            caption_id = parts[0].decode("utf-8")
            image_bytes = parts[1]
            scene_frame = Frame(image_bytes)

            # Stream captions on main thread while classification runs in background
            self.handle_frame(transport, scene_frame, caption_id)
        elif frame.msg_type == picows.WSMsgType.CLOSE:
            transport.send_close(frame.get_close_code(), frame.get_close_message())
            transport.disconnect()
        elif frame.msg_type == picows.WSMsgType.PING:
            transport.send_pong(frame.get_payload_as_bytes())


async def main():
    print("Beginning model warmup")
    caption_model = LlavaModel()
    caption_model.warmup()
    classify_model = LlamaVisionModel()

    server = await picows.ws_create_server(
        lambda _: Server(caption_model, classify_model), "0.0.0.0", 2222
    )
    for s in server.sockets:
        print(f"Server started on {s.getsockname()}")

    await server.serve_forever()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
