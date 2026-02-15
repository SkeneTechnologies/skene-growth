"""
Structural Entropy Analyzer

Measures codebase "physics" and organizational health:
- Module cohesion: How related are functions in the same file?
- File organization: Are files logically grouped?
- Dependency dispersion: Are imports scattered or focused?
- Naming consistency: Do names follow patterns?

Lower entropy = better organization.
"""

from pathlib import Path
from typing import Any
import re
from collections import Counter, defaultdict
import math

from ..manifest.schema import EntropyReport, EntropyMetric
from ..strategies.multi_step import MultiStepStrategy
from ..strategies.steps.select_files import SelectFilesStep
from ..strategies.steps.read_files import ReadFilesStep


class EntropyAnalyzer(MultiStepStrategy):
    """Analyzes structural entropy and organizational health."""

    def __init__(self):
        super().__init__(
            steps=[
                SelectFilesStep(patterns=["**/*.py", "**/*.ts", "**/*.tsx"], max_files=100),
                ReadFilesStep(),
            ]
        )

    async def analyze(self, context: dict[str, Any]) -> EntropyReport:
        """Calculate entropy metrics."""
        files = context.get("files", [])

        if not files:
            return self._empty_report()

        # Calculate individual metrics
        module_cohesion = self._calculate_module_cohesion(files)
        file_organization = self._calculate_file_organization(files)
        dependency_dispersion = self._calculate_dependency_dispersion(files)
        naming_consistency = self._calculate_naming_consistency(files)

        # Overall entropy (weighted average)
        weights = {
            "module_cohesion": 0.3,
            "file_organization": 0.25,
            "dependency_dispersion": 0.25,
            "naming_consistency": 0.2,
        }

        overall_entropy = (
            module_cohesion.value * weights["module_cohesion"]
            + file_organization.value * weights["file_organization"]
            + dependency_dispersion.value * weights["dependency_dispersion"]
            + naming_consistency.value * weights["naming_consistency"]
        )

        health_score = 100 - (overall_entropy * 100)

        recommendations = self._generate_recommendations(
            module_cohesion, file_organization, dependency_dispersion, naming_consistency
        )

        return EntropyReport(
            module_cohesion=module_cohesion.value,
            file_organization=file_organization.value,
            dependency_dispersion=dependency_dispersion.value,
            naming_consistency=naming_consistency.value,
            overall_entropy=overall_entropy,
            health_score=health_score,
            metrics=[
                module_cohesion,
                file_organization,
                dependency_dispersion,
                naming_consistency,
            ],
            recommendations=recommendations,
        )

    def _calculate_module_cohesion(self, files: list[dict]) -> EntropyMetric:
        """
        Calculate module cohesion using naming similarity.

        High cohesion = functions/classes in same file share naming patterns.
        """
        cohesion_scores = []

        for file_data in files:
            content = file_data.get("content", "")

            # Extract function/class names
            names = self._extract_symbols(content)

            if len(names) < 2:
                continue  # Skip files with <2 symbols

            # Calculate naming similarity (simplified Levenshtein distance)
            similarities = []
            for i, name1 in enumerate(names):
                for name2 in names[i + 1 :]:
                    similarity = self._name_similarity(name1, name2)
                    similarities.append(similarity)

            if similarities:
                cohesion_scores.append(sum(similarities) / len(similarities))

        avg_cohesion = sum(cohesion_scores) / len(cohesion_scores) if cohesion_scores else 0.5
        entropy = 1.0 - avg_cohesion  # Convert cohesion to entropy

        interpretation = self._interpret_entropy(entropy, "Module cohesion")
        recommendations = []

        if entropy > 0.6:
            recommendations.append("Consider splitting large files with unrelated functions")
        elif entropy > 0.4:
            recommendations.append("Some files could benefit from better grouping")

        return EntropyMetric(
            name="module_cohesion",
            value=entropy,
            interpretation=interpretation,
            recommendations=recommendations,
        )

    def _calculate_file_organization(self, files: list[dict]) -> EntropyMetric:
        """
        Calculate file organization entropy.

        Low entropy = files are well-organized in logical directories.
        """
        # Group files by directory
        directory_groups = defaultdict(list)

        for file_data in files:
            path = Path(file_data.get("path", ""))
            directory = str(path.parent)
            directory_groups[directory].append(file_data)

        # Calculate variance in directory sizes
        dir_sizes = [len(files) for files in directory_groups.values()]

        if len(dir_sizes) < 2:
            return EntropyMetric(
                name="file_organization",
                value=0.5,
                interpretation="Not enough directories to assess organization",
                recommendations=[],
            )

        # Shannon entropy of directory distribution
        total_files = sum(dir_sizes)
        probabilities = [size / total_files for size in dir_sizes]
        entropy = -sum(p * math.log2(p) if p > 0 else 0 for p in probabilities)

        # Normalize to 0-1 (log2(n) is max entropy)
        max_entropy = math.log2(len(dir_sizes))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.5

        interpretation = self._interpret_entropy(normalized_entropy, "File organization")
        recommendations = []

        if normalized_entropy > 0.7:
            recommendations.append("Consider reorganizing files into more balanced directories")
        elif normalized_entropy < 0.3:
            recommendations.append("Files are highly concentrated; consider splitting large directories")

        return EntropyMetric(
            name="file_organization",
            value=normalized_entropy,
            interpretation=interpretation,
            recommendations=recommendations,
        )

    def _calculate_dependency_dispersion(self, files: list[dict]) -> EntropyMetric:
        """
        Calculate dependency dispersion.

        Low entropy = imports are focused (good).
        High entropy = imports are scattered (bad).
        """
        import_counts = Counter()

        for file_data in files:
            content = file_data.get("content", "")
            imports = self._extract_imports(content)
            import_counts.update(imports)

        if not import_counts:
            return EntropyMetric(
                name="dependency_dispersion",
                value=0.5,
                interpretation="No imports found",
                recommendations=[],
            )

        # Calculate variance in import frequency
        counts = list(import_counts.values())
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        std_dev = math.sqrt(variance)

        # Coefficient of variation (normalized)
        cv = std_dev / mean if mean > 0 else 0

        # Normalize to 0-1 (cap at CV=2.0)
        entropy = min(cv / 2.0, 1.0)

        interpretation = self._interpret_entropy(entropy, "Dependency dispersion")
        recommendations = []

        if entropy > 0.6:
            recommendations.append("Dependencies are highly scattered; consider consolidating imports")
        elif entropy < 0.3:
            recommendations.append("Dependencies are well-focused")

        return EntropyMetric(
            name="dependency_dispersion",
            value=entropy,
            interpretation=interpretation,
            recommendations=recommendations,
        )

    def _calculate_naming_consistency(self, files: list[dict]) -> EntropyMetric:
        """
        Calculate naming consistency.

        Low entropy = consistent naming (camelCase, snake_case, etc.)
        High entropy = mixed naming styles.
        """
        naming_patterns = {
            "camelCase": 0,
            "PascalCase": 0,
            "snake_case": 0,
            "SCREAMING_SNAKE": 0,
            "kebab-case": 0,
        }

        for file_data in files:
            content = file_data.get("content", "")
            names = self._extract_symbols(content)

            for name in names:
                pattern = self._detect_naming_pattern(name)
                if pattern:
                    naming_patterns[pattern] += 1

        total = sum(naming_patterns.values())

        if total == 0:
            return EntropyMetric(
                name="naming_consistency",
                value=0.5,
                interpretation="No symbols found",
                recommendations=[],
            )

        # Shannon entropy of naming pattern distribution
        probabilities = [count / total for count in naming_patterns.values() if count > 0]
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

        # Normalize (max entropy with 5 patterns is log2(5) ≈ 2.32)
        normalized_entropy = entropy / 2.32

        interpretation = self._interpret_entropy(normalized_entropy, "Naming consistency")
        recommendations = []

        if normalized_entropy > 0.5:
            recommendations.append("Naming styles are inconsistent; establish a style guide")
        else:
            recommendations.append("Naming is consistent")

        return EntropyMetric(
            name="naming_consistency",
            value=normalized_entropy,
            interpretation=interpretation,
            recommendations=recommendations,
        )

    def _extract_symbols(self, content: str) -> list[str]:
        """Extract function and class names from code."""
        # Python: def/class, TypeScript: function/class/const/let
        patterns = [
            r"(?:def|class|function|const|let)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"([A-Z][a-zA-Z0-9_]*)\s*=\s*(?:class|function)",
        ]

        names = []
        for pattern in patterns:
            names.extend(re.findall(pattern, content))

        return list(set(names))  # Unique names

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import sources from code."""
        # Python: from X import / import X
        # TypeScript: import X from 'Y'
        patterns = [
            r"from\s+['\"]?([a-zA-Z0-9_./\-@]+)",
            r"import\s+['\"]([a-zA-Z0-9_./\-@]+)",
            r"import.*from\s+['\"]([a-zA-Z0-9_./\-@]+)",
        ]

        imports = []
        for pattern in patterns:
            imports.extend(re.findall(pattern, content))

        return imports

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate naming similarity (0-1)."""
        # Simplified: check common prefix/suffix
        common_prefix = 0
        for c1, c2 in zip(name1, name2):
            if c1 == c2:
                common_prefix += 1
            else:
                break

        max_len = max(len(name1), len(name2))
        return common_prefix / max_len if max_len > 0 else 0

    def _detect_naming_pattern(self, name: str) -> str | None:
        """Detect naming pattern."""
        if re.match(r"^[A-Z][A-Z0-9_]*$", name):
            return "SCREAMING_SNAKE"
        elif re.match(r"^[A-Z][a-zA-Z0-9]*$", name):
            return "PascalCase"
        elif re.match(r"^[a-z][a-zA-Z0-9]*$", name):
            return "camelCase"
        elif re.match(r"^[a-z][a-z0-9_]*$", name):
            return "snake_case"
        elif re.match(r"^[a-z][a-z0-9\-]*$", name):
            return "kebab-case"
        return None

    def _interpret_entropy(self, entropy: float, metric_name: str) -> str:
        """Interpret entropy value."""
        if entropy < 0.3:
            return f"{metric_name} is excellent (low entropy)"
        elif entropy < 0.5:
            return f"{metric_name} is good"
        elif entropy < 0.7:
            return f"{metric_name} is moderate (some issues)"
        else:
            return f"{metric_name} is poor (high entropy)"

    def _generate_recommendations(
        self,
        module_cohesion: EntropyMetric,
        file_organization: EntropyMetric,
        dependency_dispersion: EntropyMetric,
        naming_consistency: EntropyMetric,
    ) -> list[str]:
        """Generate overall recommendations."""
        recommendations = []

        # Prioritize by impact
        if module_cohesion.value > 0.6:
            recommendations.append("HIGH PRIORITY: Improve module cohesion by grouping related functions")

        if dependency_dispersion.value > 0.6:
            recommendations.append("HIGH PRIORITY: Consolidate scattered dependencies")

        if file_organization.value > 0.7:
            recommendations.append("MEDIUM PRIORITY: Reorganize files into balanced directory structure")

        if naming_consistency.value > 0.5:
            recommendations.append("MEDIUM PRIORITY: Establish consistent naming conventions")

        if not recommendations:
            recommendations.append("Codebase organization is healthy!")

        return recommendations

    def _empty_report(self) -> EntropyReport:
        """Return empty report when no files found."""
        return EntropyReport(
            module_cohesion=0.5,
            file_organization=0.5,
            dependency_dispersion=0.5,
            naming_consistency=0.5,
            overall_entropy=0.5,
            health_score=50.0,
            metrics=[],
            recommendations=["No files to analyze"],
        )
