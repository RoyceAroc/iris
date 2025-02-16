import requests

from typing import Generator
from .base import VendorModel, Frame, FrameStatus


class LlamaVisionModel(VendorModel):
    def __init__(self) -> None:
        self.keys = [
            "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",
            "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",
        ]
        self.current_key = 0

        self.api_key = self.keys[self.current_key]
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

        # Load and cache model prompts
        with open("src/prompts/classify.txt", "r") as f:
            self.classify_prompt = f.read().strip()
        with open("src/prompts/caption.txt", "r") as f:
            self.caption_prompt = f.read().strip()

        # Prepare headers with the current key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.base_payload = {
            "model": "llama-3.2-11b-vision-preview",
            "max_completion_tokens": 5,
            "stop": "\n",
        }

        self.session = requests.Session()

    def __del__(self):
        self.session.close()

    def _rotate_key(self):
        self.current_key = 1 - self.current_key
        self.api_key = self.keys[self.current_key]
        self.headers["Authorization"] = f"Bearer {self.api_key}"

    def classify(self, frame: Frame) -> FrameStatus:
        image_data = frame.as_encoded()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.classify_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    },
                ],
            },
        ]

        payload = self.base_payload.copy()
        payload["messages"] = messages

        response = self.session.post(self.base_url, headers=self.headers, json=payload)

        # If we get a 429, rotate key and return Hazard
        if response.status_code == 429:
            self._rotate_key()
            return FrameStatus.Hazard

        # Otherwise, raise any other HTTP errors
        response.raise_for_status()
        resp_data = response.json()
        content = resp_data["choices"][0]["message"]["content"].strip().lower()

        if "no" in content:
            return FrameStatus.Safe
        else:
            return FrameStatus.Hazard

    def caption(self, frame: Frame) -> Generator[str, None, None]:
        raise NotImplementedError()
