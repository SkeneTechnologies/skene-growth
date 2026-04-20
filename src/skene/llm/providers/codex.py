"""
Codex CLI-backed LLM client.
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from pydantic import SecretStr

from skene.llm.base import LLMClient


class CodexClient(LLMClient):
    """Use the local Codex CLI as the runtime for prompt execution."""

    def __init__(self, api_key: SecretStr, model_name: str):
        self.model_name = model_name
        self._codex_path = shutil.which("codex")

    async def _run_command(self, *args: str, cwd: str | None = None) -> tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    async def _ensure_ready(self) -> None:
        if not self._codex_path:
            raise RuntimeError("Codex CLI is not installed or not on PATH. Install it, then run `codex login`.")

        code, stdout, stderr = await self._run_command(self._codex_path, "login", "status")
        status_text = " ".join(part for part in (stdout.strip(), stderr.strip()) if part).strip().lower()
        if code != 0 or "not logged in" in status_text or "logged out" in status_text or "logged in" not in status_text:
            raise RuntimeError("Codex CLI is not logged in. Run `codex login` and try again.")

    async def _execute_prompt(self, prompt: str) -> str:
        await self._ensure_ready()

        with tempfile.TemporaryDirectory(prefix="skene-codex-") as temp_dir:
            output_path = Path(temp_dir) / "last-message.txt"
            args = [
                self._codex_path,
                "exec",
                "--ephemeral",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--color",
                "never",
                "--output-last-message",
                str(output_path),
            ]
            if self.model_name != "auto":
                args.extend(["-m", self.model_name])
            args.append(prompt)

            code, stdout, stderr = await self._run_command(*args, cwd=temp_dir)
            if code != 0:
                detail = "\n".join(part for part in (stderr.strip(), stdout.strip()) if part)
                if detail:
                    raise RuntimeError(f"Codex CLI execution failed: {detail}")
                raise RuntimeError("Codex CLI execution failed.")

            content = output_path.read_text(encoding="utf-8").strip() if output_path.exists() else ""
            if not content:
                raise RuntimeError("Codex CLI returned an empty response.")
            return content

    async def generate_content_with_usage(self, prompt: str) -> tuple[str, dict[str, int] | None]:
        return await self._execute_prompt(prompt), None

    async def generate_content_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        yield await self._execute_prompt(prompt)

    def get_model_name(self) -> str:
        return self.model_name

    def get_provider_name(self) -> str:
        return "codex"
