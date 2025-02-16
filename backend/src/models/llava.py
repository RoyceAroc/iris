import io
import torch
import threading

from PIL import Image
from typing import Generator
from transformers import (
    AutoProcessor,
    LlavaForConditionalGeneration,
    TextIteratorStreamer,
)
from .base import DeviceModel, Frame, FrameStatus


class LlavaModel(DeviceModel):
    def __init__(self) -> None:
        self.model_id = "llava-hf/llava-interleave-qwen-0.5b-hf"
        self.device = torch.device("cuda:0")

        # Enable Tensor Cores and cuDNN optimizations
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.set_float32_matmul_precision("medium")
        torch.backends.cudnn.benchmark = True

        # Initialize Llava model and processor
        self.model = LlavaForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        ).to(self.device)
        self.processor = AutoProcessor.from_pretrained(self.model_id, use_fast=True)

        # Put model in eval/compiled mode
        self.model.eval()
        self.model = torch.compile(
            self.model,
            fullgraph=True,
            dynamic=True,
            mode="max-autotune",
        )

        # Load and pre-process model prompts
        with open("src/prompts/classify.txt", "r") as f:
            classify_text = f.read().strip()
            self.classify_prompt = self.processor.apply_chat_template(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": classify_text},
                            {"type": "image"},
                        ],
                    }
                ],
                add_generation_prompt=False,
            )

        with open("src/prompts/caption.txt", "r") as f:
            caption_text = f.read().strip()
            self.caption_prompt = self.processor.apply_chat_template(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": caption_text},
                            {"type": "image"},
                        ],
                    }
                ],
                add_generation_prompt=False,
            )

    def _process_input(self, frame: Frame, text: str) -> dict:
        # Process the frame with the provided prompt text
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

        # Pass the frame through processor with a simple warmup prompt
        frame = Frame(buffer.getvalue())
        inputs = self._process_input(frame, text=self.caption_prompt)

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
    def classify(self, frame: Frame) -> FrameStatus:
        inputs = self._process_input(frame, text=self.classify_prompt)

        # Generation configuration for classification
        generation_config = dict(
            max_new_tokens=3,
            num_beams=1,
            do_sample=False,
            use_cache=True,
        )

        # Run the model's generate call directly on the main thread
        output_ids = self.model.generate(**inputs, **generation_config)

        # Decode the model's response, skipping the prompt tokens
        prompt_length = len(inputs["input_ids"][0])
        response = (
            self.processor.decode(
                output_ids[0][prompt_length:], skip_special_tokens=True
            )
            .strip()
            .lower()
        )

        return FrameStatus.Hazard if "no" in response else FrameStatus.Safe

    @torch.inference_mode()
    def caption(self, frame) -> Generator[str, None, None]:
        streamer = TextIteratorStreamer(
            tokenizer=self.processor.tokenizer,
            skip_special_tokens=True,
            skip_prompt=True,
        )

        # Prepare generation config
        generation_config = dict(
            max_new_tokens=20,
            num_beams=1,
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
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
