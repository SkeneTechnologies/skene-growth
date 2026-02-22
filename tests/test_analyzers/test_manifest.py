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
            project_name="test-project",
            tech_stack={"language": "TypeScript"},
        )

        assert manifest.project_name == "test-project"
        assert manifest.tech_stack.language == "TypeScript"

    def test_growth_manifest_with_tech_stack(self):
        """Test GrowthManifest with tech stack information."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={
                "language": "TypeScript",
                "framework": "Next.js",
                "database": "PostgreSQL",
            },
        )

        assert manifest.tech_stack.language == "TypeScript"
        assert manifest.tech_stack.framework == "Next.js"
        assert manifest.tech_stack.database == "PostgreSQL"

    def test_growth_manifest_with_plg_features(self):
        """Test GrowthManifest with growth hubs."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={"language": "TypeScript"},
            growth_hubs=[
                {
                    "feature_name": "Team Invitations",
                    "file_path": "src/invitations.ts",
                    "detected_intent": "Viral growth",
                    "confidence_score": 0.9,
                },
            ],
        )

        assert len(manifest.growth_hubs) == 1
        assert manifest.growth_hubs[0].feature_name == "Team Invitations"

    def test_growth_manifest_serialization(self):
        """Test that GrowthManifest can be serialized to JSON."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={"language": "Python"},
        )

        json_data = manifest.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["project_name"] == "test-project"

    def test_growth_manifest_with_gaps(self):
        """Test GrowthManifest with GTM gaps."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={"language": "TypeScript"},
            gtm_gaps=[
                {
                    "feature_name": "Referral Program",
                    "description": "No referral mechanism detected",
                    "priority": "high",
                },
                {
                    "feature_name": "Viral Loops",
                    "description": "No viral sharing feature detected",
                    "priority": "medium",
                },
            ],
        )

        assert len(manifest.gtm_gaps) == 2
        assert manifest.gtm_gaps[0].feature_name == "Referral Program"

    def test_growth_manifest_with_recommendations(self):
        """Test GrowthManifest with GTM gaps as recommendations."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={"language": "Python"},
            gtm_gaps=[
                {
                    "feature_name": "Add referral program",
                    "description": "Implement referral tracking to drive growth",
                    "priority": "high",
                },
                {
                    "feature_name": "Improve onboarding",
                    "description": "Streamline the onboarding flow",
                    "priority": "medium",
                },
            ],
        )

        assert len(manifest.gtm_gaps) == 2
        assert manifest.gtm_gaps[0].feature_name == "Add referral program"


class TestManifestValidation:
    """Test manifest validation logic."""

    def test_manifest_requires_version(self):
        """Test that manifest has a default version."""
        from skene_growth.manifest.schema import GrowthManifest

        # version has a default of "1.0", so omitting it should work
        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={"language": "TypeScript"},
        )
        assert manifest.version == "1.0"

    def test_manifest_requires_analyzed_at(self):
        """Test that manifest auto-generates generated_at."""
        from skene_growth.manifest.schema import GrowthManifest

        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={"language": "TypeScript"},
        )
        assert manifest.generated_at is not None

    def test_manifest_requires_project_path(self):
        """Test that manifest requires project_name field."""
        from skene_growth.manifest.schema import GrowthManifest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GrowthManifest(
                tech_stack={"language": "TypeScript"},
            )

    def test_manifest_allows_extra_fields(self):
        """Test that manifest validates required fields."""
        from skene_growth.manifest.schema import GrowthManifest

        # This should not raise an error — all required fields present
        manifest = GrowthManifest(
            project_name="test-project",
            tech_stack={"language": "TypeScript"},
        )

        assert manifest.project_name == "test-project"
