from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from skene.llm.factory import create_llm_client
from skene.llm.providers.codex import CodexClient


def test_factory_creates_codex_client():
    client = create_llm_client(
        provider="codex",
        api_key=SecretStr(""),
        model_name="auto",
    )
    assert isinstance(client, CodexClient)
    assert client.get_provider_name() == "codex"
    assert client.get_model_name() == "auto"


class _FakeProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "", on_communicate=None):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self._on_communicate = on_communicate

    async def communicate(self):
        if self._on_communicate is not None:
            self._on_communicate()
        return self._stdout.encode(), self._stderr.encode()


@pytest.mark.asyncio
async def test_codex_client_omits_model_flag_for_auto(monkeypatch):
    from skene.llm.providers import codex as codex_module

    calls: list[dict[str, object]] = []

    async def fake_exec(*args, cwd=None, stdout=None, stderr=None):
        calls.append({"args": args, "cwd": cwd})
        if args[:3] == ("/usr/bin/codex", "login", "status"):
            return _FakeProcess(returncode=0, stdout="Logged in using ChatGPT")

        output_idx = args.index("--output-last-message") + 1
        output_path = Path(args[output_idx])
        return _FakeProcess(returncode=0, on_communicate=lambda: output_path.write_text("codex reply", encoding="utf-8"))

    monkeypatch.setattr(codex_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(codex_module.asyncio, "create_subprocess_exec", fake_exec)

    client = CodexClient(api_key=SecretStr(""), model_name="auto")
    content, usage = await client.generate_content_with_usage("hello")
    stream_chunks = [chunk async for chunk in client.generate_content_stream("hello again")]

    exec_call = calls[1]["args"]
    assert exec_call[0:7] == (
        "/usr/bin/codex",
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--color",
    )
    assert "-m" not in exec_call
    assert content == "codex reply"
    assert usage is None
    assert stream_chunks == ["codex reply"]
    assert calls[1]["cwd"] != calls[2]["cwd"]


@pytest.mark.asyncio
async def test_codex_client_passes_explicit_model(monkeypatch):
    from skene.llm.providers import codex as codex_module

    calls: list[tuple[str, ...]] = []

    async def fake_exec(*args, cwd=None, stdout=None, stderr=None):
        calls.append(args)
        if args[:3] == ("/usr/bin/codex", "login", "status"):
            return _FakeProcess(returncode=0, stdout="Logged in using ChatGPT")

        output_idx = args.index("--output-last-message") + 1
        output_path = Path(args[output_idx])
        return _FakeProcess(returncode=0, on_communicate=lambda: output_path.write_text("ok", encoding="utf-8"))

    monkeypatch.setattr(codex_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(codex_module.asyncio, "create_subprocess_exec", fake_exec)

    client = CodexClient(api_key=SecretStr(""), model_name="gpt-5.4")
    await client.generate_content_with_usage("hello")

    exec_call = calls[1]
    model_idx = exec_call.index("-m")
    assert exec_call[model_idx : model_idx + 2] == ("-m", "gpt-5.4")


@pytest.mark.asyncio
async def test_codex_client_fails_when_binary_missing(monkeypatch):
    from skene.llm.providers import codex as codex_module

    monkeypatch.setattr(codex_module.shutil, "which", lambda _: None)

    client = CodexClient(api_key=SecretStr(""), model_name="auto")
    with pytest.raises(RuntimeError, match="Codex CLI is not installed"):
        await client.generate_content_with_usage("hello")


@pytest.mark.asyncio
async def test_codex_client_fails_when_logged_out(monkeypatch):
    from skene.llm.providers import codex as codex_module

    async def fake_exec(*args, cwd=None, stdout=None, stderr=None):
        return _FakeProcess(returncode=0, stdout="Not logged in")

    monkeypatch.setattr(codex_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(codex_module.asyncio, "create_subprocess_exec", fake_exec)

    client = CodexClient(api_key=SecretStr(""), model_name="auto")
    with pytest.raises(RuntimeError, match="Run `codex login`"):
        await client.generate_content_with_usage("hello")


@pytest.mark.asyncio
async def test_codex_client_fails_on_non_zero_exit(monkeypatch):
    from skene.llm.providers import codex as codex_module

    async def fake_exec(*args, cwd=None, stdout=None, stderr=None):
        if args[:3] == ("/usr/bin/codex", "login", "status"):
            return _FakeProcess(returncode=0, stdout="Logged in using ChatGPT")
        return _FakeProcess(returncode=1, stderr="boom")

    monkeypatch.setattr(codex_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(codex_module.asyncio, "create_subprocess_exec", fake_exec)

    client = CodexClient(api_key=SecretStr(""), model_name="auto")
    with pytest.raises(RuntimeError, match="boom"):
        await client.generate_content_with_usage("hello")


@pytest.mark.asyncio
async def test_codex_client_fails_on_empty_output(monkeypatch):
    from skene.llm.providers import codex as codex_module

    async def fake_exec(*args, cwd=None, stdout=None, stderr=None):
        if args[:3] == ("/usr/bin/codex", "login", "status"):
            return _FakeProcess(returncode=0, stdout="Logged in using ChatGPT")
        return _FakeProcess(returncode=0)

    monkeypatch.setattr(codex_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(codex_module.asyncio, "create_subprocess_exec", fake_exec)

    client = CodexClient(api_key=SecretStr(""), model_name="auto")
    with pytest.raises(RuntimeError, match="empty response"):
        await client.generate_content_with_usage("hello")
