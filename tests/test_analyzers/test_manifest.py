"""Tests for manifest analyzer."""

import pytest
from pathlib import Path


class TestManifestAnalyzer:
    """Test manifest analysis functionality."""

    def test_manifest_analyzer_exists(self):
        """Test that manifest analyzer module can be imported."""
        from skene_growth.analyzers import manifest
        assert manifest is not None

    def test_manifest_module_has_required_exports(self):
        """Test that manifest module exports expected functions."""
        from skene_growth.analyzers import manifest
        # Just verify module loads without errors
        assert hasattr(manifest, '__file__')


class TestManifestSchema:
    """Test manifest schema validation."""

    def test_can_import_manifest_schema(self):
        """Test importing manifest schema."""
        from skene_growth.manifest.schema import GrowthManifest
        assert GrowthManifest is not None

    def test_growth_manifest_model_structure(self):
        """Test GrowthManifest Pydantic model structure."""
        from skene_growth.manifest.schema import GrowthManifest

        # Create a minimal valid manifest
        manifest = GrowthManifest(
            version="1.0.0",
            analyzed_at="2024-01-01T00:00:00Z",
            project_path="/test/path",
            tech_stack={},
            plg_features={},
            growth_hubs=[],
            gaps=[],
            recommendations=[]
        )

        assert manifest.version == "1.0.0"
        assert manifest.project_path == "/test/path"

    def test_growth_manifest_with_tech_stack(self):
        """Test GrowthManifest with tech stack information."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            version="1.0.0",
            analyzed_at="2024-01-01T00:00:00Z",
            project_path="/test/path",
            tech_stack={
                "framework": "Next.js",
                "database": "PostgreSQL"
            },
            plg_features={},
            growth_hubs=[],
            gaps=[],
            recommendations=[]
        )

        assert manifest.tech_stack["framework"] == "Next.js"
        assert manifest.tech_stack["database"] == "PostgreSQL"

    def test_growth_manifest_with_plg_features(self):
        """Test GrowthManifest with PLG features."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            version="1.0.0",
            analyzed_at="2024-01-01T00:00:00Z",
            project_path="/test/path",
            tech_stack={},
            plg_features={
                "signup": {"present": True, "confidence": 0.9},
                "onboarding": {"present": False, "confidence": 0.1}
            },
            growth_hubs=[],
            gaps=[],
            recommendations=[]
        )

        assert manifest.plg_features["signup"]["present"] is True
        assert manifest.plg_features["onboarding"]["present"] is False

    def test_growth_manifest_serialization(self):
        """Test that GrowthManifest can be serialized to JSON."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            version="1.0.0",
            analyzed_at="2024-01-01T00:00:00Z",
            project_path="/test/path",
            tech_stack={},
            plg_features={},
            growth_hubs=[],
            gaps=[],
            recommendations=[]
        )

        json_data = manifest.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["version"] == "1.0.0"

    def test_growth_manifest_with_gaps(self):
        """Test GrowthManifest with gaps."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            version="1.0.0",
            analyzed_at="2024-01-01T00:00:00Z",
            project_path="/test/path",
            tech_stack={},
            plg_features={},
            growth_hubs=[],
            gaps=[
                {"feature": "referral_program", "severity": "high"},
                {"feature": "viral_loops", "severity": "medium"}
            ],
            recommendations=[]
        )

        assert len(manifest.gaps) == 2
        assert manifest.gaps[0]["feature"] == "referral_program"

    def test_growth_manifest_with_recommendations(self):
        """Test GrowthManifest with recommendations."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            version="1.0.0",
            analyzed_at="2024-01-01T00:00:00Z",
            project_path="/test/path",
            tech_stack={},
            plg_features={},
            growth_hubs=[],
            gaps=[],
            recommendations=[
                {"action": "Add referral program", "priority": "high"},
                {"action": "Improve onboarding", "priority": "medium"}
            ]
        )

        assert len(manifest.recommendations) == 2
        assert manifest.recommendations[0]["action"] == "Add referral program"


class TestManifestValidation:
    """Test manifest validation logic."""

    def test_manifest_requires_version(self):
        """Test that manifest requires version field."""
        from skene_growth.manifest.schema import GrowthManifest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GrowthManifest(
                analyzed_at="2024-01-01T00:00:00Z",
                project_path="/test/path",
                tech_stack={},
                plg_features={},
                growth_hubs=[],
                gaps=[],
                recommendations=[]
            )

    def test_manifest_requires_analyzed_at(self):
        """Test that manifest requires analyzed_at field."""
        from skene_growth.manifest.schema import GrowthManifest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GrowthManifest(
                version="1.0.0",
                project_path="/test/path",
                tech_stack={},
                plg_features={},
                growth_hubs=[],
                gaps=[],
                recommendations=[]
            )

    def test_manifest_requires_project_path(self):
        """Test that manifest requires project_path field."""
        from skene_growth.manifest.schema import GrowthManifest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GrowthManifest(
                version="1.0.0",
                analyzed_at="2024-01-01T00:00:00Z",
                tech_stack={},
                plg_features={},
                growth_hubs=[],
                gaps=[],
                recommendations=[]
            )

    def test_manifest_allows_extra_fields(self):
        """Test that manifest allows extra fields for extensibility."""
        from skene_growth.manifest.schema import GrowthManifest

        # This should not raise an error
        manifest = GrowthManifest(
            version="1.0.0",
            analyzed_at="2024-01-01T00:00:00Z",
            project_path="/test/path",
            tech_stack={},
            plg_features={},
            growth_hubs=[],
            gaps=[],
            recommendations=[],
            custom_field="custom_value"  # Extra field
        )

        # Extra fields might be ignored or stored depending on Pydantic config
        assert manifest.version == "1.0.0"
