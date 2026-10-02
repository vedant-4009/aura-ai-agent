import re
from typing import Any, Dict

from tools.github import (
    github_repository,
    github_readme,
    github_repository_tree,
    github_repository_tree_recursive,
)

from analyzers.release_readiness import analyze_release_readiness


def _extract_repository(value: str) -> str:
    value = value.strip()

    match = re.search(
        r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b",
        value,
    )

    if match:
        return match.group(1)

    match = re.search(
        r"\b(?:repository|repo)\s+([A-Za-z0-9_.-]+)",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        return value

    return value


def analyze_repository(repository: str) -> Dict[str, Any]:
    repository = _extract_repository(repository)

    # ---------------------------------------------------------
    # Repository metadata
    # ---------------------------------------------------------

    metadata = github_repository(repository)

    if not metadata.get("success"):
        return {
            "success": False,
            "repository": repository,
            "error": metadata.get(
                "error",
                "Repository metadata could not be retrieved.",
            ),
        }

    repo_data = metadata.get("repository", {})

    # ---------------------------------------------------------
    # README
    # ---------------------------------------------------------

    readme_result = github_readme(repository)

    # ---------------------------------------------------------
    # Normal repository tree
    # ---------------------------------------------------------

    tree_result = github_repository_tree(repository)

    # ---------------------------------------------------------
    # Recursive repository scan
    # ---------------------------------------------------------

    recursive_tree_result = github_repository_tree_recursive(
        repository,
        max_depth=3,
        max_files=200,
    )

    # ---------------------------------------------------------
    # Base repository snapshot
    # ---------------------------------------------------------

    snapshot = {
        "success": True,
        "repository": repo_data,
        "readme": readme_result,
        "tree": tree_result,
        "recursive_tree": recursive_tree_result,
        "evidence": {
            "metadata_source": "GitHub repository API",
            "readme_source": "GitHub README API",
            "tree_source": "GitHub repository contents API",
            "recursive_tree_source": (
                "GitHub recursive repository contents API"
            ),
        },
    }

    # ---------------------------------------------------------
    # Release-readiness analysis
    # ---------------------------------------------------------

    if recursive_tree_result.get("success"):
        release_snapshot = {
            "success": True,
            "repository": repo_data,

            # Important:
            # README content is now passed into the
            # release-readiness analyzer.
            "readme": readme_result,

            "files": recursive_tree_result.get(
                "files",
                [],
            ),
            "directories": recursive_tree_result.get(
                "directories",
                [],
            ),
        }

        release_analysis = analyze_release_readiness(
            release_snapshot
        )

        snapshot["release_analysis"] = release_analysis

    else:
        snapshot["release_analysis"] = {
            "success": False,
            "error": recursive_tree_result.get(
                "error",
                "Recursive repository scan failed.",
            ),
            "findings": [],
        }

    return snapshot


def analyze_release_readiness_tool(
    repository: str,
) -> Dict[str, Any]:
    """
    Public AURA tool for release-readiness analysis.

    Runs the repository analyzer and exposes only the
    release-readiness analysis result.
    """

    result = analyze_repository(repository)

    if not result.get("success"):
        return {
            "success": False,
            "repository": result.get(
                "repository",
                repository,
            ),
            "error": result.get(
                "error",
                "Repository analysis failed.",
            ),
        }

    release_analysis = result.get(
        "release_analysis"
    )

    if not release_analysis:
        return {
            "success": False,
            "repository": result.get(
                "repository",
                repository,
            ),
            "error": (
                "Release-readiness analysis "
                "was not generated."
            ),
        }

    return release_analysis