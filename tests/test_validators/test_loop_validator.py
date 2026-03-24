"""Integration tests for loop_validator with JS/TS support."""

from __future__ import annotations

from pathlib import Path

import pytest

from skene.validators.loop_validator import (
    extract_all_functions,
    validate_file_requirement,
    validate_function_requirement,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sample_repo"


# ---------------------------------------------------------------------------
# validate_file_requirement — JS/TS
# ---------------------------------------------------------------------------


class TestValidateFileRequirementJSTS:
    def test_function_exists_in_ts(self):
        req = {
            "path": "src/app.ts",
            "purpose": "Main app entry",
            "required": True,
            "checks": [{"type": "function_exists", "pattern": "startConversation", "description": "main fn"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.exists
        assert result.passed
        assert result.checks[0].status.value == "passed"

    def test_class_exists_in_ts(self):
        req = {
            "path": "src/app.ts",
            "purpose": "Chat service",
            "required": True,
            "checks": [{"type": "class_exists", "pattern": "ChatService", "description": "service class"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.passed

    def test_interface_detected_as_class_in_ts(self):
        req = {
            "path": "src/app.ts",
            "purpose": "Config interface",
            "required": True,
            "checks": [{"type": "class_exists", "pattern": "ConversationConfig", "description": "config interface"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.passed

    def test_import_exists_in_ts(self):
        req = {
            "path": "src/app.ts",
            "purpose": "SDK import",
            "required": True,
            "checks": [{"type": "import_exists", "pattern": "chatbot-sdk", "description": "SDK import"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.passed

    def test_function_exists_in_js(self):
        req = {
            "path": "src/bootstrap.js",
            "purpose": "Bootstrap",
            "required": True,
            "checks": [{"type": "function_exists", "pattern": "initializeApp", "description": "init fn"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.passed

    def test_class_exists_in_js(self):
        req = {
            "path": "src/bootstrap.js",
            "purpose": "Server class",
            "required": True,
            "checks": [{"type": "class_exists", "pattern": "AppServer", "description": "server class"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.passed

    def test_import_exists_in_js_commonjs(self):
        req = {
            "path": "src/bootstrap.js",
            "purpose": "Express import",
            "required": True,
            "checks": [{"type": "import_exists", "pattern": "express", "description": "express import"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.passed

    def test_function_not_found_in_ts(self):
        req = {
            "path": "src/app.ts",
            "purpose": "Missing fn",
            "required": True,
            "checks": [{"type": "function_exists", "pattern": "nonExistentFunc", "description": "missing"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert not result.passed
        assert result.checks[0].status.value == "failed"


# ---------------------------------------------------------------------------
# validate_function_requirement — TS
# ---------------------------------------------------------------------------


class TestValidateFunctionRequirementTS:
    @pytest.mark.asyncio
    async def test_ts_function_found(self):
        req = {
            "file": "src/app.ts",
            "name": "startConversation",
            "required": True,
            "signature": "",
        }
        result = await validate_function_requirement(req, FIXTURES)
        assert result.found
        assert result.passed

    @pytest.mark.asyncio
    async def test_ts_function_not_found(self):
        req = {
            "file": "src/app.ts",
            "name": "missingFunction",
            "required": True,
            "signature": "",
        }
        result = await validate_function_requirement(req, FIXTURES)
        assert not result.found
        assert not result.passed


# ---------------------------------------------------------------------------
# extract_all_functions — JS/TS included
# ---------------------------------------------------------------------------


class TestExtractAllFunctionsJSTS:
    def test_includes_js_ts_functions(self):
        functions = extract_all_functions(FIXTURES)
        names = [f.name for f in functions]
        # JS functions
        assert "initializeApp" in names
        assert "handleRequest" in names
        # TS functions
        assert "startConversation" in names
        assert "loadHistory" in names


# ---------------------------------------------------------------------------
# Regression: Python validation unchanged
# ---------------------------------------------------------------------------


class TestPythonRegressionValidation:
    def test_python_function_exists(self):
        req = {
            "path": "src/main.py",
            "purpose": "Main module",
            "required": True,
            "checks": [{"type": "function_exists", "pattern": "main", "description": "entry point"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        # The file exists — check that Python parsing still works
        assert result.exists

    def test_python_contains_check(self):
        req = {
            "path": "src/main.py",
            "purpose": "Main module",
            "required": True,
            "checks": [{"type": "contains", "pattern": "def ", "description": "has a function"}],
        }
        result = validate_file_requirement(req, FIXTURES)
        assert result.exists
