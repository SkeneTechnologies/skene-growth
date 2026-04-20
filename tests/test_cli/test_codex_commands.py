from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from skene.cli.app import app

runner = CliRunner()


def test_analyze_codex_bypasses_sample_preview(monkeypatch, tmp_path: Path):
    import skene.llm
    analyze_module = importlib.import_module("skene.cli.commands.analyze")

    async def fake_run_analysis(path, output, llm, debug, product_docs, exclude_folders=None):
        return SimpleNamespace(success=True, data={}), {"tech_stack": {}, "current_growth_features": []}

    async def fake_write_growth_template(llm, manifest_data, output):
        return {}

    def fail_sample(*args, **kwargs):
        raise AssertionError("sample preview should not run for codex")

    monkeypatch.setattr(skene.llm, "create_llm_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(analyze_module, "run_analysis", fake_run_analysis)
    monkeypatch.setattr(analyze_module, "write_growth_template", fake_write_growth_template)
    monkeypatch.setattr(analyze_module, "show_sample_report", fail_sample)

    output = tmp_path / "growth-manifest.json"
    result = runner.invoke(app, ["analyze", str(tmp_path), "--provider", "codex", "--model", "auto", "-o", str(output)])

    assert result.exit_code == 0, result.stdout


def test_plan_codex_bypasses_sample_preview(monkeypatch, tmp_path: Path):
    plan_module = importlib.import_module("skene.cli.commands.plan")

    async def fake_run_generate_plan(**kwargs):
        assert kwargs["provider"] == "codex"
        assert kwargs["api_key"] == ""
        return "memo", {}

    def fail_sample(*args, **kwargs):
        raise AssertionError("sample preview should not run for codex")

    monkeypatch.setattr(plan_module, "run_generate_plan", fake_run_generate_plan)
    monkeypatch.setattr(plan_module, "show_sample_report", fail_sample)

    output = tmp_path / "growth-plan.md"
    result = runner.invoke(app, ["plan", "--provider", "codex", "--model", "auto", "-o", str(output)])

    assert result.exit_code == 0, result.stdout


def test_build_codex_bypasses_api_key_validation(monkeypatch, tmp_path: Path):
    build_module = importlib.import_module("skene.cli.commands.build")
    import skene.engine
    import skene.feature_registry
    import skene.growth_loops.push as push_module
    import skene.llm

    plan_path = tmp_path / "growth-plan.md"
    plan_path.write_text("# Plan", encoding="utf-8")
    prompt_file = tmp_path / "implementation-prompt.md"

    def fake_create_llm_client(provider, api_key, model_name, **kwargs):
        assert provider == "codex"
        assert api_key.get_secret_value() == ""
        assert model_name == "auto"
        return object()

    async def fake_build_prompt_with_llm(*args, **kwargs):
        return "prompt"

    monkeypatch.setattr(skene.llm, "create_llm_client", fake_create_llm_client)
    monkeypatch.setattr(build_module, "extract_technical_execution", lambda path: {"overview": "Overview"})
    monkeypatch.setattr(build_module, "build_prompt_with_llm", fake_build_prompt_with_llm)
    monkeypatch.setattr(build_module, "save_prompt_to_file", lambda prompt, output_dir: prompt_file)

    monkeypatch.setattr(skene.engine, "ensure_engine_dir", lambda project_root: None)
    monkeypatch.setattr(skene.engine, "default_engine_path", lambda project_root: project_root / "skene" / "engine.yaml")
    monkeypatch.setattr(skene.engine, "load_engine_document", lambda *args, **kwargs: SimpleNamespace(features=[]))
    monkeypatch.setattr(skene.engine, "generate_engine_delta_with_llm", fake_build_prompt_with_llm)
    monkeypatch.setattr(skene.engine, "merge_engine_documents", lambda existing, delta: existing)
    monkeypatch.setattr(skene.engine, "write_engine_document", lambda *args, **kwargs: None)
    monkeypatch.setattr(skene.engine, "engine_features_to_loop_definitions", lambda engine_doc: [])

    monkeypatch.setattr(skene.feature_registry, "load_features_for_build", lambda base_output_dir: [])
    monkeypatch.setattr(skene.feature_registry, "get_registry_path_for_output", lambda output: tmp_path / "feature-registry.json")
    monkeypatch.setattr(skene.feature_registry, "upsert_registry_from_engine", lambda engine_doc, registry_path: None)

    monkeypatch.setattr(push_module, "ensure_base_schema_migration", lambda project_root: tmp_path / "schema.sql")
    monkeypatch.setattr(push_module, "build_loops_to_supabase", lambda loop_defs, project_root: tmp_path / "loops.sql")

    result = runner.invoke(
        app,
        ["build", "--provider", "codex", "--model", "auto", "--plan", str(plan_path), "--target", "file"],
    )

    assert result.exit_code == 0, result.stdout
