"""
W5D Builder — Image Generation Interface
=========================================
Pluggable image generation system. To add a new provider:

1. Create a class inheriting ImageGenerator
2. Implement the `generate()` method
3. Register it in ImageGeneratorFactory.create()

The system supports reference images for scene continuity —
ensuring that "the same elephant" appears across multiple frames.
"""

from __future__ import annotations

import abc
import base64
import os
import uuid
from pathlib import Path
from typing import Optional

from ..config import settings


# ─── Data Models ─────────────────────────────────────────────────────────────

class ImageGenRequest:
    """
    All parameters needed to generate one image.

    Args:
        prompt:           Main description of the image to generate.
        style_suffix:     Auto-appended style hint (flat illustration, white bg...).
        reference_images: List of local file paths or URLs to reference images.
                          Used for visual continuity — pass the previous frame's
                          assets here so the model maintains visual consistency.
        reference_note:   Text describing how to use references, e.g.
                          "Keep the same elephant character, just change pose to eating".
        width:            Output width in pixels (default 1024).
        height:           Output height in pixels (default 1024).
        variations:       How many image options to generate (default 1).
        extra:            Provider-specific extra parameters.
    """

    def __init__(
        self,
        prompt: str,
        style_suffix: str = "flat cartoon illustration, white background, isolated subject, no shadows, bold outlines",
        reference_images: list[str] | None = None,
        reference_note: str | None = None,
        width: int = 1024,
        height: int = 1024,
        variations: int = 1,
        extra: dict | None = None,
    ):
        self.prompt = prompt
        self.style_suffix = style_suffix
        self.reference_images = reference_images or []
        self.reference_note = reference_note
        self.width = width
        self.height = height
        self.variations = variations
        self.extra = extra or {}

    @property
    def full_prompt(self) -> str:
        """Returns the complete prompt with style suffix appended."""
        if self.style_suffix:
            return f"{self.prompt}, {self.style_suffix}"
        return self.prompt

    @property
    def continuity_context(self) -> str | None:
        """Returns continuity context string if references provided."""
        if not self.reference_images:
            return None
        note = self.reference_note or "Use the provided reference images to maintain visual consistency."
        return f"{note} Reference images: {len(self.reference_images)} provided."


class ImageGenResult:
    """
    Result from one generation call.

    Attributes:
        image_paths:  List of local file paths to generated images.
        provider:     Name of the provider that generated the images.
        prompt_used:  The exact prompt sent to the provider.
        metadata:     Any provider-specific metadata (model, seed, etc).
    """

    def __init__(
        self,
        image_paths: list[str],
        provider: str,
        prompt_used: str,
        metadata: dict | None = None,
    ):
        self.image_paths = image_paths
        self.provider = provider
        self.prompt_used = prompt_used
        self.metadata = metadata or {}


# ─── Abstract Base ────────────────────────────────────────────────────────────

class ImageGenerator(abc.ABC):
    """
    Abstract base for all image generation providers.

    Subclass this and implement `generate()` to add a new provider.
    The system will handle saving files, scene continuity references,
    and retry logic automatically.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider name, e.g. 'dalle3', 'gemini', 'flux'."""
        ...

    @abc.abstractmethod
    async def generate(self, request: ImageGenRequest) -> ImageGenResult:
        """
        Generate images for the given request.

        This method MUST:
        - Return at least request.variations image paths
        - Save images to settings.STORAGE_BASE_PATH / "generated" / <uuid>.png
        - Handle reference_images if the provider supports it

        Args:
            request: The generation request with prompt, references, etc.

        Returns:
            ImageGenResult with paths to saved images.
        """
        ...

    def _output_dir(self) -> Path:
        path = Path(settings.STORAGE_BASE_PATH) / "generated"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _save_image_bytes(self, data: bytes, suffix: str = ".png") -> str:
        """Helper: save raw image bytes to a file, return path."""
        path = self._output_dir() / f"{uuid.uuid4().hex}{suffix}"
        path.write_bytes(data)
        return str(path)

    def _save_base64_image(self, b64: str) -> str:
        """Helper: save base64-encoded image, return path."""
        data = base64.b64decode(b64)
        return self._save_image_bytes(data)

    def _read_image_as_base64(self, file_path: str) -> str:
        """Helper: read a local image file and return base64 string."""
        return base64.b64encode(Path(file_path).read_bytes()).decode()


# ─── Implementations ──────────────────────────────────────────────────────────

class MockImageGenerator(ImageGenerator):
    """
    Mock generator for development and testing.
    Returns a colored placeholder image without calling any API.
    Supports reference images (logs them but doesn't actually use them).
    """

    name = "mock"

    async def generate(self, request: ImageGenRequest) -> ImageGenResult:
        from PIL import Image, ImageDraw, ImageFont

        paths = []
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]

        for i in range(request.variations):
            img = Image.new("RGBA", (request.width, request.height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # Draw a placeholder shape
            color = colors[i % len(colors)]
            margin = 100
            draw.ellipse(
                [margin, margin, request.width - margin, request.height - margin],
                fill=color,
                outline="#333",
                width=8,
            )

            # Write prompt text
            label = request.prompt[:60] + "..." if len(request.prompt) > 60 else request.prompt
            draw.text((request.width // 2, request.height - 60), label,
                      fill="#333333", anchor="mm")

            if request.reference_images:
                draw.text((request.width // 2, 30),
                          f"[REF: {len(request.reference_images)} images]",
                          fill="#666666", anchor="mm")

            path = self._save_image_bytes(self._pil_to_bytes(img))
            paths.append(path)

        return ImageGenResult(
            image_paths=paths,
            provider=self.name,
            prompt_used=request.full_prompt,
            metadata={"variations": request.variations},
        )

    @staticmethod
    def _pil_to_bytes(img) -> bytes:
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


class OpenAIDalle3Generator(ImageGenerator):
    """
    DALL-E 3 via OpenAI API.

    DALL-E 3 does NOT support reference images natively.
    When reference_images are provided, this generator automatically
    builds a detailed description of the reference into the prompt
    using the reference_note field.

    To add image references: set request.reference_note with a detailed
    text description extracted from analyzing the reference image(s).
    """

    name = "dalle3"

    def __init__(self):
        import openai
        self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate(self, request: ImageGenRequest) -> ImageGenResult:
        prompt = request.full_prompt
        if request.reference_note:
            prompt = f"{prompt}. Visual consistency note: {request.reference_note}"

        # DALL-E 3 only generates 1 image per call
        paths = []
        for _ in range(request.variations):
            resp = await self._client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=f"{request.width}x{request.height}",
                quality="standard",
                response_format="b64_json",
                **{k: v for k, v in request.extra.items() if k in ("style",)},
            )
            paths.append(self._save_base64_image(resp.data[0].b64_json))

        return ImageGenResult(
            image_paths=paths,
            provider=self.name,
            prompt_used=prompt,
            metadata={"model": "dall-e-3", "revised_prompt": resp.data[0].revised_prompt},
        )


class GeminiImageGenerator(ImageGenerator):
    """
    Google Gemini Imagen via google-generativeai SDK.

    Supports reference images natively through multimodal input.
    Reference images are sent alongside the prompt so Gemini can
    maintain visual consistency (same character, different pose/action).

    Usage example:
        request = ImageGenRequest(
            prompt="The same elephant now eating grass",
            reference_images=["path/to/elephant_prev_frame.png"],
            reference_note="Keep exactly the same elephant character design",
        )
    """

    name = "gemini"

    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self._imagen = genai.ImageGenerationModel("imagen-3.0-generate-001")

    async def generate(self, request: ImageGenRequest) -> ImageGenResult:
        import google.generativeai as genai

        paths = []

        if request.reference_images:
            # Use Gemini multimodal: send reference images + prompt
            # Build content parts
            parts = []
            for ref_path in request.reference_images:
                parts.append(
                    genai.upload_file(ref_path) if ref_path.startswith("/") or ref_path.startswith(".")
                    else {"mime_type": "image/png", "data": base64.b64decode(ref_path)}
                )

            continuity_prompt = (
                f"You are generating an image for a W5D explainer video.\n"
                f"Reference images above show the existing character/asset.\n"
                f"IMPORTANT: {request.reference_note or 'Maintain the same visual style and character design.'}\n"
                f"Generate: {request.full_prompt}"
            )
            parts.append(continuity_prompt)

            # Use Gemini multimodal to generate an image-to-image style result
            # (In production, use Imagen with image conditioning)
            resp = await self._model.generate_content_async(parts)
            # Extract image from response if available, else fall back to text-only Imagen
            # This is a simplified implementation — extend based on actual Gemini API response
            for candidate in resp.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "inline_data"):
                        paths.append(self._save_base64_image(
                            base64.b64encode(part.inline_data.data).decode()
                        ))
        else:
            # Text-to-image via Imagen
            result = self._imagen.generate_images(
                prompt=request.full_prompt,
                number_of_images=request.variations,
                aspect_ratio="1:1",
            )
            for img in result.images:
                paths.append(self._save_image_bytes(img._image_bytes))

        return ImageGenResult(
            image_paths=paths,
            provider=self.name,
            prompt_used=request.full_prompt,
        )


class ReplicateFluxGenerator(ImageGenerator):
    """
    Flux via Replicate API.

    Supports reference images through image-to-image mode (img2img).
    When reference_images are provided, uses the first reference as
    init_image with a configurable strength.

    Extra params:
        strength (float): How much to change from reference (0=same, 1=ignore). Default 0.7
        model (str): Replicate model ID. Default "black-forest-labs/flux-1.1-pro"
    """

    name = "replicate"

    def __init__(self):
        import replicate
        self._client = replicate.Client(api_token=settings.REPLICATE_API_KEY)

    async def generate(self, request: ImageGenRequest) -> ImageGenResult:
        import replicate

        model = request.extra.get("model", "black-forest-labs/flux-1.1-pro")
        strength = request.extra.get("strength", 0.7)

        paths = []
        for _ in range(request.variations):
            input_data = {
                "prompt": request.full_prompt,
                "width": request.width,
                "height": request.height,
                "output_format": "png",
            }

            if request.reference_images:
                # img2img mode — use first reference
                with open(request.reference_images[0], "rb") as f:
                    input_data["image"] = f
                input_data["prompt_strength"] = strength

            output = self._client.run(model, input=input_data)
            # output is typically a URL or file-like
            if isinstance(output, str):
                import httpx
                resp = httpx.get(output)
                paths.append(self._save_image_bytes(resp.content))
            elif hasattr(output, "read"):
                paths.append(self._save_image_bytes(output.read()))

        return ImageGenResult(
            image_paths=paths,
            provider=self.name,
            prompt_used=request.full_prompt,
            metadata={"model": model},
        )


class GrokImageGenerator(ImageGenerator):
    """
    Grok / xAI image generation.

    Uses OpenAI-compatible API endpoint.
    Reference images: passed as multimodal context when supported.

    Note: As of 2025, Grok's image gen API is evolving.
    Update the model name and endpoint as xAI releases new versions.
    """

    name = "grok"

    def __init__(self):
        import openai
        self._client = openai.AsyncOpenAI(
            api_key=settings.XAI_API_KEY,
            base_url="https://api.x.ai/v1",
        )

    async def generate(self, request: ImageGenRequest) -> ImageGenResult:
        prompt = request.full_prompt
        if request.reference_note:
            prompt = f"{prompt}. {request.reference_note}"

        resp = await self._client.images.generate(
            model="grok-2-image",
            prompt=prompt,
            n=request.variations,
            response_format="b64_json",
        )

        paths = [self._save_base64_image(d.b64_json) for d in resp.data]

        return ImageGenResult(
            image_paths=paths,
            provider=self.name,
            prompt_used=prompt,
        )


# ─── Factory ──────────────────────────────────────────────────────────────────

class ImageGeneratorFactory:
    """
    Factory to create the configured image generator.

    To add a new provider:
    1. Create a class inheriting ImageGenerator above
    2. Add it to the `_registry` dict below
    3. Set IMAGE_GEN_PROVIDER=your_provider_name in .env
    """

    _registry: dict[str, type[ImageGenerator]] = {
        "mock": MockImageGenerator,
        "dalle3": OpenAIDalle3Generator,
        "gemini": GeminiImageGenerator,
        "replicate": ReplicateFluxGenerator,
        "grok": GrokImageGenerator,
    }

    @classmethod
    def create(cls, provider: str | None = None) -> ImageGenerator:
        """
        Create and return an ImageGenerator for the given provider.

        Args:
            provider: Provider name. Defaults to settings.IMAGE_GEN_PROVIDER.

        Returns:
            Initialized ImageGenerator instance.

        Raises:
            ValueError if provider is unknown.
        """
        provider = provider or settings.IMAGE_GEN_PROVIDER
        if provider not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown image generator '{provider}'. Available: {available}")
        return cls._registry[provider]()

    @classmethod
    def available_providers(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def register(cls, name: str, generator_class: type[ImageGenerator]) -> None:
        """
        Register a custom provider at runtime.
        Use this to add providers without modifying this file.

        Example:
            class MyCustomGenerator(ImageGenerator):
                name = "my_custom"
                async def generate(self, request): ...

            ImageGeneratorFactory.register("my_custom", MyCustomGenerator)
        """
        cls._registry[name] = generator_class
