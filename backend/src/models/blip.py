import io
import torch
import threading

from PIL import Image
from typing import AsyncGenerator
from transformers import (
    BlipForConditionalGeneration,
    BlipProcessor,
    TextIteratorStreamer,
)
from .base import DeviceModel, Frame, FrameStatus


class BlipModel(DeviceModel):
    def __init__(self) -> None:
        self.model_id = "Salesforce/blip-image-captioning-base"
        self.device = torch.device("cuda:0")

        # Enable Tensor Cores and cuDNN optimizations
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.set_float32_matmul_precision("medium")
        torch.backends.cudnn.benchmark = True

        # Initialize BLIP model and processor
        self.model = BlipForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16,
        ).to(self.device)
        self.processor = BlipProcessor.from_pretrained(self.model_id)

        # Put model in eval/compiled mode
        self.model.eval()
        self.model = torch.compile(
            self.model,
            fullgraph=True,
            dynamic=True,
            mode="max-autotune",
        )

        # Load model prompts from files
        with open("src/prompts/classify.txt", "r") as f:
            self.classify_prompt = f.read().strip()
        with open("src/prompts/caption.txt", "r") as f:
            self.caption_prompt = f.read().strip()

    def _process_input(self, frame: Frame, text: str = None):
        # Process the frame, using the resized pillow image
        inputs = self.processor(
            images=frame.as_image(),
            text=text,
            return_tensors="pt",
        )

        return inputs.to(self.device, dtype=torch.float16, non_blocking=True)

    @torch.inference_mode()
    def warmup(self) -> None:
        # Create a dummy 128x128 image
        dummy = Image.new("RGB", (128, 128), color="white")
        buffer = io.BytesIO()
        dummy.save(buffer, format="PNG")

        # Pass the frame through processor
        frame = Frame(buffer.getvalue())
        inputs = self._process_input(frame)

        for _ in range(3):
            _ = self.model.generate(
                **inputs,
                max_new_tokens=10,
                num_beams=1,
                do_sample=False,
                use_cache=True,
            )

        torch.cuda.synchronize()

    @torch.inference_mode()
    async def classify(self, _: Frame) -> FrameStatus:
        raise NotImplementedError()

    @torch.inference_mode()
    async def caption(self, frame: Frame) -> AsyncGenerator[str, None]:
        streamer = TextIteratorStreamer(
            tokenizer=self.processor.tokenizer,
            skip_special_tokens=True,
        )

        # Prepare generation config (limit to 25 tokens)
        generation_config = dict(
            max_new_tokens=25,
            num_beams=1,
            do_sample=False,
            min_length=5,
            length_penalty=1.0,
            use_cache=True,
            streamer=streamer,
        )

        inputs = self._process_input(frame, text=self.caption_prompt)

        # Generate the model response in a separate thread
        def generate():
            self.model.generate(**inputs, **generation_config)

        generator = threading.Thread(target=generate)
        generator.start()

        # Stream tokens in the current thread
        for token_text in streamer:
            yield token_text

        generator.join()
