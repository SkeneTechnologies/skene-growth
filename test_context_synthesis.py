#!/usr/bin/env python3
"""
Test script for Context Synthesis Layer integration.

This script tests:
1. Imports work correctly
2. Context synthesis step can be instantiated
3. Analyzer includes context synthesis step
4. Models can be created and validated
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from skene_growth.models.context import ContextSignals, ProductContext
from skene_growth.synthesis.heuristics import apply_heuristic_tags
from skene_growth.strategies.steps import ContextSynthesisStep
from skene_growth.analyzers import ManifestAnalyzer


def test_imports():
    """Test that all imports work."""
    print("✓ Testing imports...")
    try:
        from skene_growth.models.context import ContextSignals, ProductContext
        from skene_growth.synthesis import ContextSynthesizer, extract_context_signals
        from skene_growth.strategies.steps import ContextSynthesisStep
        from skene_growth.analyzers import ManifestAnalyzer
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_models():
    """Test that models can be created and validated."""
    print("\n✓ Testing models...")
    try:
        # Test ContextSignals
        signals = ContextSignals(
            database_tables=["users", "organizations", "subscriptions"],
            api_routes=["/api/users", "/api/organizations"],
            dependencies=["stripe", "sendgrid"],
        )
        assert len(signals.database_tables) == 3
        print("  ✓ ContextSignals created successfully")

        # Test ProductContext
        context = ProductContext(
            industry="Developer Tools",
            target_audience="B2B SaaS teams",
            value_proposition="Helps teams collaborate better",
            business_model="B2B SaaS",
            confidence_score=0.85,
        )
        assert context.industry == "Developer Tools"
        print("  ✓ ProductContext created successfully")

        return True
    except Exception as e:
        print(f"  ✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_heuristics():
    """Test heuristic tagging."""
    print("\n✓ Testing heuristics...")
    try:
        signals = ContextSignals(
            database_tables=["organizations", "workspaces", "subscriptions"],
            dependencies=["stripe", "sendgrid"],
            api_routes=["/api/organizations", "/api/auth"],
        )
        tags = apply_heuristic_tags(signals)
        assert isinstance(tags, list)
        assert len(tags) > 0
        print(f"  ✓ Generated {len(tags)} heuristic tags: {tags[:5]}")
        return True
    except Exception as e:
        print(f"  ✗ Heuristics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analyzer_steps():
    """Test that ManifestAnalyzer includes context synthesis step."""
    print("\n✓ Testing analyzer steps...")
    try:
        analyzer = ManifestAnalyzer()
        step_names = [step.name for step in analyzer.steps]
        
        # Check that context_synthesis step is present
        assert "context_synthesis" in step_names, f"context_synthesis not found in steps: {step_names}"
        
        # Check step order (should be after tech_stack, before growth_hubs)
        tech_stack_idx = step_names.index("analyze")  # First analyze is tech stack
        context_idx = step_names.index("context_synthesis")
        growth_hubs_idx = [i for i, name in enumerate(step_names) if name == "analyze"][1]  # Second analyze is growth hubs
        
        assert context_idx > tech_stack_idx, "Context synthesis should come after tech stack"
        assert context_idx < growth_hubs_idx, "Context synthesis should come before growth hubs"
        
        print(f"  ✓ Analyzer has {len(analyzer.steps)} steps")
        print(f"  ✓ Context synthesis step is at position {context_idx}")
        print(f"  ✓ Step order is correct")
        return True
    except Exception as e:
        print(f"  ✗ Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_instantiation():
    """Test that ContextSynthesisStep can be instantiated."""
    print("\n✓ Testing step instantiation...")
    try:
        step = ContextSynthesisStep(
            output_key="product_context",
            source_key="context_file_contents",
        )
        assert step.name == "context_synthesis"
        assert step.output_key == "product_context"
        print("  ✓ ContextSynthesisStep instantiated successfully")
        return True
    except Exception as e:
        print(f"  ✗ Step instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Context Synthesis Layer - Integration Tests")
    print("=" * 60)

    tests = [
        test_imports,
        test_models,
        test_heuristics,
        test_step_instantiation,
        test_analyzer_steps,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
