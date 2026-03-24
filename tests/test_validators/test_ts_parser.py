"""Unit tests for ts_parser.py — tree-sitter based JS/TS parsing."""

from __future__ import annotations

import tempfile
from pathlib import Path

from skene.validators.ts_parser import parse_js_ts


def _parse_source(source: str, suffix: str = ".js") -> object:
    """Write source to a temp file and parse it."""
    with tempfile.NamedTemporaryFile(suffix=suffix, mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        f.flush()
        result = parse_js_ts(Path(f.name))
    assert result is not None, f"parse_js_ts returned None for {suffix} source"
    return result


# ---------------------------------------------------------------------------
# JS function detection
# ---------------------------------------------------------------------------


class TestJSFunctionDetection:
    def test_function_declaration(self):
        tree = _parse_source("function greet(name) { return name; }")
        assert "greet" in tree.function_names()

    def test_arrow_function(self):
        tree = _parse_source("const add = (a, b) => a + b;")
        assert "add" in tree.function_names()

    def test_function_expression(self):
        tree = _parse_source("const multiply = function(a, b) { return a * b; };")
        assert "multiply" in tree.function_names()

    def test_export_function(self):
        tree = _parse_source("export function fetchData(url) { return url; }")
        assert "fetchData" in tree.function_names()

    def test_export_default_function(self):
        tree = _parse_source("export default function main() { return 1; }")
        assert "main" in tree.function_names()

    def test_class_method(self):
        source = """
class Foo {
  bar() { return 1; }
  baz(x) { return x; }
}
"""
        tree = _parse_source(source)
        names = tree.function_names()
        assert "bar" in names
        assert "baz" in names

    def test_export_arrow(self):
        tree = _parse_source("export const handler = (req, res) => res.send('ok');")
        assert "handler" in tree.function_names()


# ---------------------------------------------------------------------------
# TS function detection
# ---------------------------------------------------------------------------


class TestTSFunctionDetection:
    def test_typed_function(self):
        tree = _parse_source("function greet(name: string): string { return name; }", ".ts")
        assert "greet" in tree.function_names()

    def test_async_function(self):
        tree = _parse_source("async function fetchData(url: string): Promise<string> { return ''; }", ".ts")
        assert "fetchData" in tree.function_names()

    def test_export_with_interface_param(self):
        source = """
interface Config { url: string; }
export function init(config: Config): void {}
"""
        tree = _parse_source(source, ".ts")
        assert "init" in tree.function_names()


# ---------------------------------------------------------------------------
# Class detection
# ---------------------------------------------------------------------------


class TestClassDetection:
    def test_js_class(self):
        tree = _parse_source("class MyService { constructor() {} }")
        assert "MyService" in tree.class_names()

    def test_ts_interface(self):
        tree = _parse_source("interface UserProfile { name: string; }", ".ts")
        assert "UserProfile" in tree.class_names()

    def test_exported_class(self):
        tree = _parse_source("export class AppController { run() {} }")
        assert "AppController" in tree.class_names()

    def test_exported_interface(self):
        tree = _parse_source("export interface Config { key: string; }", ".ts")
        assert "Config" in tree.class_names()


# ---------------------------------------------------------------------------
# Import detection
# ---------------------------------------------------------------------------


class TestImportDetection:
    def test_esm_named_import(self):
        tree = _parse_source('import { useState } from "react";')
        names = tree.import_names()
        assert "react" in names
        assert "react.useState" in names

    def test_esm_default_import(self):
        tree = _parse_source('import React from "react";')
        names = tree.import_names()
        assert "react" in names
        assert "react.React" in names

    def test_esm_star_import(self):
        tree = _parse_source('import * as utils from "utils";')
        names = tree.import_names()
        assert "utils" in names
        assert "utils.utils" in names

    def test_commonjs_require(self):
        tree = _parse_source('const express = require("express");')
        names = tree.import_names()
        assert "express" in names

    def test_multiple_named_imports(self):
        tree = _parse_source('import { Chatbot, Agent } from "chatbot-sdk";')
        names = tree.import_names()
        assert "chatbot-sdk" in names
        assert "chatbot-sdk.Chatbot" in names
        assert "chatbot-sdk.Agent" in names


# ---------------------------------------------------------------------------
# Signature extraction
# ---------------------------------------------------------------------------


class TestSignatureExtraction:
    def test_js_simple(self):
        tree = _parse_source("function greet(name) { return name; }")
        sig = tree.function_signature("greet")
        assert sig is not None
        assert "greet" in sig
        assert "name" in sig

    def test_ts_typed(self):
        tree = _parse_source("function add(a: number, b: number): number { return a + b; }", ".ts")
        sig = tree.function_signature("add")
        assert sig is not None
        assert "add" in sig
        assert "number" in sig

    def test_not_found_returns_none(self):
        tree = _parse_source("function foo() {}")
        assert tree.function_signature("bar") is None

    def test_arrow_signature(self):
        tree = _parse_source("const greet = (name: string): string => name;", ".ts")
        sig = tree.function_signature("greet")
        assert sig is not None
        assert "greet" in sig
        assert "string" in sig


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_file(self):
        tree = _parse_source("")
        assert tree.function_names() == []
        assert tree.class_names() == []
        assert tree.import_names() == []

    def test_binary_file(self):
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")
            f.flush()
            result = parse_js_ts(Path(f.name))
        # Should still parse (tree-sitter handles binary gracefully)
        assert result is not None

    def test_unsupported_suffix(self):
        with tempfile.NamedTemporaryFile(suffix=".rb", mode="w", delete=False) as f:
            f.write("def foo; end")
            f.flush()
            result = parse_js_ts(Path(f.name))
        assert result is None

    def test_function_infos(self):
        source = """
function alpha() {}
const beta = () => {};
"""
        tree = _parse_source(source)
        infos = tree.function_infos()
        names = [fi.name for fi in infos]
        assert "alpha" in names
        assert "beta" in names

    def test_tsx_support(self):
        source = """
import React from "react";
export function App(): JSX.Element { return <div/>; }
"""
        tree = _parse_source(source, ".tsx")
        assert "App" in tree.function_names()
