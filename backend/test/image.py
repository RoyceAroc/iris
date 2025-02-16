import asyncio
import time
import picows
import uvloop
import argparse

from pathlib import Path


class Client(picows.WSListener):
    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
        self.start_time = None
        self.first_token_time = None
        self.transport = None

    def on_ws_connected(self, transport: picows.WSTransport):
        self.transport = transport

        try:
            if not Path(self.image_path).is_file():
                print(f"Error: Image file not found: {self.image_path}")
                transport.disconnect()
                return

            with open(self.image_path, "rb") as f:
                image_bytes = f.read()

            print("Connected to server, sending image...")
            self.start_time = time.perf_counter()
            transport.send(picows.WSMsgType.BINARY, image_bytes)
        except Exception as e:
            print(f"Error reading image: {e}")
            transport.disconnect()

    def on_ws_frame(self, transport: picows.WSTransport, frame: picows.WSFrame):
        if frame.msg_type == picows.WSMsgType.TEXT:
            token = frame.get_payload_as_ascii_text()

            if token == "<end>":
                total_time = time.perf_counter() - self.start_time
                print(f"\nTime for full caption: {total_time:.3f}s")
                transport.send_close(picows.WSCloseCode.OK)
                transport.disconnect()
                return

            if self.first_token_time is None:
                self.first_token_time = time.perf_counter() - self.start_time
                print(f"Time to first token: {self.first_token_time:.3f}s")

            print(token, end="", flush=True)
        elif frame.msg_type == picows.WSMsgType.CLOSE:
            transport.send_close(frame.get_close_code(), frame.get_close_message())
            transport.disconnect()
        elif frame.msg_type == picows.WSMsgType.PING:
            transport.send_pong(frame.get_payload_as_bytes())


async def main(image_path: str):
    transport, _ = await picows.ws_connect(
        lambda: Client(image_path), "ws://127.0.0.1:9001"
    )
    await transport.wait_disconnected()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Path to the image file to caption")
    args = parser.parse_args()

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main(args.image_path))
