"""
Local LLM client implementation using llama-cpp-python.
"""

import asyncio
from queue import Empty, Queue
from threading import Thread
from typing import AsyncGenerator, ClassVar

from loguru import logger
from pydantic import SecretStr

from skene_growth.llm.base import LLMClient


class LocalClient(LLMClient):
    """
    Local LLM client using llama-cpp-python.

    Runs GGUF models directly without external services.
    Uses lazy loading and class-level singleton to avoid reloading models.

    Example:
        client = LocalClient(
            api_key=SecretStr("unused"),  # Not needed for local models
            model_name="qwen-2.5-3b"
        )
        response = await client.generate_content("Hello!")
    """

    # Class-level model cache to avoid reloading
    _loaded_models: ClassVar[dict] = {}
    _model_lock: ClassVar[asyncio.Lock | None] = None

    def __init__(
        self,
        api_key: SecretStr,
        model_name: str,
        n_ctx: int | None = None,
        n_gpu_layers: int | None = None,
    ):
        """
        Initialize the local LLM client.

        Args:
            api_key: Ignored for local models (kept for interface compatibility)
            model_name: Model ID from registry or path to GGUF file
            n_ctx: Context length (uses registry defaults if not specified)
            n_gpu_layers: GPU layers (-1 = auto, 0 = CPU only)
        """
        self.model_name = model_name
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._model = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the model loading lock."""
        if cls._model_lock is None:
            cls._model_lock = asyncio.Lock()
        return cls._model_lock

    async def _ensure_model_loaded(self):
        """Load the model if not already loaded (lazy loading)."""
        if self._model is not None:
            return

        cache_key = (self.model_name, self.n_ctx, self.n_gpu_layers)
        if cache_key in LocalClient._loaded_models:
            self._model = LocalClient._loaded_models[cache_key]
            return

        async with self._get_lock():
            # Double-check after acquiring lock
            if cache_key in LocalClient._loaded_models:
                self._model = LocalClient._loaded_models[cache_key]
                return

            # Load model in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(None, self._load_model_sync)
            LocalClient._loaded_models[cache_key] = self._model

    def _load_model_sync(self):
        """Synchronously load the model."""
        from pathlib import Path

        from skene_growth.llm.local import get_registry, load_model, load_model_from_path

        # Check if model_name is a path to a file
        model_path = Path(self.model_name)
        if model_path.exists() and model_path.suffix == ".gguf":
            logger.info(f"Loading model from path: {self.model_name}")
            kwargs = {}
            if self.n_ctx is not None:
                kwargs["n_ctx"] = self.n_ctx
            if self.n_gpu_layers is not None:
                kwargs["n_gpu_layers"] = self.n_gpu_layers
            return load_model_from_path(self.model_name, **kwargs)

        # Otherwise, load from registry
        registry = get_registry()
        config = registry.get_model(self.model_name)
        if not config:
            raise ValueError(
                f"Model '{self.model_name}' not found in registry. "
                f"Available models: {[m.id for m in registry.list_models()]}"
            )

        logger.info(f"Loading model: {config.name}")
        return load_model(
            self.model_name,
            n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers,
        )

    async def generate_content(self, prompt: str) -> str:
        """
        Generate text from the local LLM.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated text as a string

        Raises:
            RuntimeError: If generation fails
        """
        await self._ensure_model_loaded()

        try:
            # Run inference in executor (llama-cpp-python is sync)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._generate_sync,
                prompt,
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Error generating content with local model: {e}")

    def _generate_sync(self, prompt: str) -> str:
        """Synchronous generation."""
        response = self._model.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"].strip()

    async def generate_content_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Generate content with streaming.

        Uses a background thread + queue pattern to bridge
        llama-cpp-python's sync streaming to async.

        Args:
            prompt: The prompt to send to the model

        Yields:
            Text chunks as they are generated

        Raises:
            RuntimeError: If streaming fails
        """
        await self._ensure_model_loaded()

        # Use queue-based streaming with background thread
        queue: Queue = Queue()
        error_holder: list = []

        def stream_worker():
            try:
                for chunk in self._model.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                ):
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        queue.put(content)
                queue.put(None)  # Signal completion
            except Exception as e:
                error_holder.append(e)
                queue.put(None)

        # Start background thread
        thread = Thread(target=stream_worker, daemon=True)
        thread.start()

        # Yield chunks as they arrive
        while True:
            try:
                # Use asyncio-friendly polling
                while True:
                    try:
                        chunk = queue.get_nowait()
                        break
                    except Empty:
                        await asyncio.sleep(0.01)

                if chunk is None:
                    break
                yield chunk
            except Exception as e:
                raise RuntimeError(f"Error in streaming generation: {e}")

        # Check for errors from worker thread
        if error_holder:
            raise RuntimeError(f"Error in streaming generation: {error_holder[0]}")

    def get_model_name(self) -> str:
        """Return the name of the underlying model."""
        return self.model_name

    def get_provider_name(self) -> str:
        """Return the provider name."""
        return "local"
