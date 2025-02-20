import requests
import json

from typing import Generator
from .base import VendorModel, Frame, FrameStatus


class LlamaVisionModel(VendorModel):
    def __init__(self) -> None:
        self.keys = [
            "API_KEY_HERE",
        ]
        self.current_key_index = 0
        self.api_key = self.keys[self.current_key_index]
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

        # Load prompts
        with open("src/prompts/classify.txt", "r") as f:
            self.classify_prompt = f.read().strip()
        with open("src/prompts/caption.txt", "r") as f:
            self.caption_prompt = f.read().strip()

    def classify(self, frame: Frame, attempt: int = 0) -> FrameStatus:
        if attempt >= len(self.keys):
            return FrameStatus.Safe

        image_data = frame.as_encoded()
        payload = {
            "model": "llama-3.2-11b-vision-preview",
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.classify_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            },
                        },
                    ],
                }
            ],
            "max_completion_tokens": 25,
            "response_format": {"type": "text"},
            "stream": False,
        }

        response = self.session.post(
            self.base_url,
            json=payload,
        )

        if response.status_code == 429:
            return self.classify(frame, attempt + 1)

        resp_data = response.json()
        text_response = resp_data["choices"][0]["message"]["content"].lower()

        if "yes" in text_response:
            return FrameStatus.Hazard
        elif "no" in text_response:
            return FrameStatus.Safe

        return FrameStatus.Hazard

    def caption(self, frame: Frame, attempt: int = 0) -> Generator[str, None, None]:
        if attempt >= len(self.keys):
            yield "<end>"
            return

        image_data = frame.as_encoded()
        payload = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.caption_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            },
                        },
                    ],
                }
            ],
            "max_completion_tokens": 50,
            "response_format": {"type": "text"},
            "stream": True,
        }

        response = self.session.post(
            self.base_url,
            json=payload,
            stream=True,
        )

        if response.status_code == 429:
            yield from self.caption(frame, attempt + 1)
            return

        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue

            data_str = line[len("data: ") :].strip()
            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
                if chunk.get("choices") and chunk["choices"][0].get("delta"):
                    content = chunk["choices"][0]["delta"].get("content")
                    if content:
                        yield content
            except json.JSONDecodeError:
                continue
