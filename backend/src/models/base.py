import base64
import io

from abc import ABC, abstractmethod
from collections.abc import Generator, AsyncGenerator
from enum import Enum
from PIL import Image


class Frame:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.image = None
        self.encoded = None

    def as_image(self) -> Image.Image:
        if not self.image:
            self.image = (
                Image.open(io.BytesIO(self.data)).convert("RGB").resize((128, 128))
            )

        return self.image

    def as_encoded(self) -> str:
        self.encoded = self.encoded or base64.b64encode(self.data).decode("utf-8")
        return self.encoded


class FrameStatus(Enum):
    Hazard = "hazard"
    Safe = "safe"


class DeviceModel(ABC):
    @abstractmethod
    def warmup(self) -> None:
        pass

    @abstractmethod
    def classify(self, frame: Frame) -> FrameStatus:
        pass

    @abstractmethod
    def caption(self, frame: Frame) -> Generator[str, None, None]:
        pass


class VendorModel(ABC):
    @abstractmethod
    def classify(self, frame: Frame) -> FrameStatus:
        pass

    @abstractmethod
    def caption(self, frame: Frame) -> AsyncGenerator[str, None]:
        pass
