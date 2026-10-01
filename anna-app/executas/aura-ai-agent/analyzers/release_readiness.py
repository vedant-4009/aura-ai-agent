from typing import Any, Dict, List

from analyzers.secret_scan import scan_repository_files


def _normalize_paths(snapshot: Dict[str, Any]) -> List[str]:
    """Return all discovered repository paths in lowercase."""

    paths = []

    for item in snapshot.get("files", []):
        path = item.get("path")

        if path:
            paths.append(path.lower())

    for item in snapshot.get("directories", []):
        path = item.get("path")

        if path:
            paths.append(path.lower())

    return paths


def _has_exact_file(paths: List[str], names: set) -> str | None:
    """Return the first matching file path."""

    for path in paths:
        filename = path.rsplit("/", 1)[-1]

        if filename in names:
            return path

    return None


def _has_path_prefix(paths: List[str], prefixes: tuple) -> str | None:
    """Return the first path matching one of the prefixes."""

    for path in paths:
        for prefix in prefixes:
            if path.startswith(prefix):
                return path

    return None


def _add_finding(
    findings: List[Dict[str, Any]],
    severity: str,
    title: str,
    fact: str,
    evidence: List[str],
    recommendation: str,
) -> None:
    """Add one structured LaunchGuard finding."""

    findings.append(
        {
            "severity": severity,
            "title": title,
            "fact": fact,
            "evidence": evidence,
            "recommendation": recommendation,
        }
    )


def analyze_release_readiness(
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze a repository snapshot using deterministic release-readiness rules.

    This analyzer does not calculate an overall score.
    """

    if not snapshot.get("success"):
        return {
            "success": False,
            "error": snapshot.get(
                "error",
                "Repository snapshot is unavailable."
            ),
            "findings": [],
        }

    paths = _normalize_paths(snapshot)

    findings = []

    # ---------------------------------------------------------
    # Repository metadata
    # ---------------------------------------------------------

    repository_data = snapshot.get("repository", {})

    if isinstance(repository_data, dict):
        repository = repository_data
        repository_name = repository.get(
            "full_name",
            "Unknown repository"
        )
    else:
        repository = {}
        repository_name = str(repository_data)

    if repository.get("archived"):
        _add_finding(
            findings,
            "High",
            "Repository is archived",
            "GitHub reports that this repository is archived.",
            ["GitHub repository metadata: archived=true"],
            "Unarchive the repository if it is intended for active development.",
        )

    if repository.get("fork"):
        _add_finding(
            findings,
            "Informational",
            "Repository is a fork",
            "GitHub reports that this repository is a fork.",
            ["GitHub repository metadata: fork=true"],
            "Confirm that the repository ownership and distribution model are appropriate for the intended release.",
        )

    # ---------------------------------------------------------
    # README
    # ---------------------------------------------------------

    readme_path = _has_exact_file(
        paths,
        {"readme.md", "readme", "readme.txt"},
    )

    if readme_path:
        _add_finding(
            findings,
            "Informational",
            "README detected",
            "A README file was found in the repository.",
            [readme_path],
            "Keep the README updated with setup, usage, configuration, and deployment instructions.",
        )
    else:
        _add_finding(
            findings,
            "Medium",
            "README not detected",
            "No README file was found in the scanned repository tree.",
            ["Recursive repository tree scan"],
            "Add a README covering the project purpose, setup, configuration, usage, and deployment steps.",
        )

    # ---------------------------------------------------------
    # LICENSE
    # ---------------------------------------------------------

    license_path = _has_exact_file(
        paths,
        {
            "license",
            "license.md",
            "license.txt",
            "licence",
            "licence.md",
            "licence.txt",
        },
    )

    if license_path:
        _add_finding(
            findings,
            "Informational",
            "License detected",
            "A license file was found in the repository.",
            [license_path],
            "Keep the license aligned with how the project is intended to be distributed.",
        )
    else:
        _add_finding(
            findings,
            "Medium",
            "License not detected",
            "No common license file was found in the scanned repository tree.",
            ["Recursive repository tree scan"],
            "Add an appropriate license before distributing the project if licensing is required.",
        )

    # ---------------------------------------------------------
    # Tests
    # ---------------------------------------------------------

    test_path = _has_path_prefix(
        paths,
        (
            "tests/",
            "test/",
            "__tests__/",
        ),
    )

    test_file = None

    if not test_path:
        for path in paths:
            filename = path.rsplit("/", 1)[-1]

            if (
                filename.startswith("test_")
                or filename.endswith("_test.py")
                or filename.endswith(".test.js")
                or filename.endswith(".test.ts")
                or filename.endswith(".spec.js")
                or filename.endswith(".spec.ts")
            ):
                test_file = path
                break

    if test_path or test_file:
        evidence = [test_path or test_file]

        _add_finding(
            findings,
            "Informational",
            "Automated test files detected",
            "The repository contains a recognizable test directory or test file.",
            evidence,
            "Continue expanding automated tests for critical application behavior.",
        )
    else:
        _add_finding(
            findings,
            "Medium",
            "Automated tests not detected",
            "No recognizable test directory or common test filename was found in the scanned repository tree.",
            ["Recursive repository tree scan"],
            "Add automated tests for critical application behavior before release.",
        )

    # ---------------------------------------------------------
    # CI/CD
    # ---------------------------------------------------------

    workflow_path = _has_path_prefix(
        paths,
        (
            ".github/workflows/",
        ),
    )

    if workflow_path:
        _add_finding(
            findings,
            "Informational",
            "GitHub Actions workflow detected",
            "A GitHub Actions workflow path was found.",
            [workflow_path],
            "Keep CI checks running on relevant branches and pull requests.",
        )
    else:
        _add_finding(
            findings,
            "Low",
            "CI workflow not detected",
            "No GitHub Actions workflow directory was found in the scanned repository tree.",
            ["Recursive repository tree scan"],
            "Consider adding CI checks for tests, linting, validation, or build verification.",
        )

    # ---------------------------------------------------------
    # Dependency files
    # ---------------------------------------------------------

    dependency_path = _has_exact_file(
        paths,
        {
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
            "pipfile",
            "pipfile.lock",
        },
    )

    if dependency_path:
        _add_finding(
            findings,
            "Informational",
            "Dependency configuration detected",
            "A recognizable dependency or package configuration file was found.",
            [dependency_path],
            "Keep dependencies pinned or constrained appropriately and review them before release.",
        )
    else:
        _add_finding(
            findings,
            "Low",
            "Dependency configuration not detected",
            "No common dependency configuration file was found in the scanned repository tree.",
            ["Recursive repository tree scan"],
            "Add an explicit dependency configuration appropriate for the project.",
        )

    # ---------------------------------------------------------
    # Environment example
    # ---------------------------------------------------------

    env_example_path = _has_exact_file(
        paths,
        {
            ".env.example",
            ".env.sample",
            ".env.template",
        },
    )

    if env_example_path:
        _add_finding(
            findings,
            "Informational",
            "Environment configuration template detected",
            "An environment configuration template was found.",
            [env_example_path],
            "Keep the template free of real secrets and document required configuration values.",
        )

    # ---------------------------------------------------------
    # Secret-prone files
    # ---------------------------------------------------------

    secret_scan = scan_repository_files(
        snapshot.get("files", [])
    )

    if secret_scan.get("success"):
        secret_findings = secret_scan.get("findings", [])

        if secret_findings:
            for secret in secret_findings:
                secret_path = secret.get("path", "Unknown path")

                _add_finding(
                    findings,
                    "High",
                    "Secret-prone file detected",
                    "A file commonly used to store credentials or private keys was found in the repository tree.",
                    [secret_path],
                    "Verify that the file does not contain real secrets and keep sensitive credentials outside the repository.",
                )
        else:
            _add_finding(
                findings,
                "Informational",
                "No secret-prone filenames detected",
                "No commonly recognized secret-storage filename was found in the scanned repository tree.",
                ["Safe secret filename scan"],
                "Continue keeping credentials outside source control and use environment or platform secret storage.",
            )

    # ---------------------------------------------------------
    # Docker
    # ---------------------------------------------------------

    dockerfile_path = _has_exact_file(
        paths,
        {
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
        },
    )

    if dockerfile_path:
        _add_finding(
            findings,
            "Informational",
            "Container configuration detected",
            "A Docker-related configuration file was found.",
            [dockerfile_path],
            "Review the image, runtime configuration, and secret handling before deployment.",
        )

    # ---------------------------------------------------------
    # Deployment configuration
    # ---------------------------------------------------------

    deployment_path = _has_exact_file(
        paths,
        {
            "vercel.json",
            "render.yaml",
            "fly.toml",
            "railway.json",
            "railway.toml",
        },
    )

    if deployment_path:
        _add_finding(
            findings,
            "Informational",
            "Deployment configuration detected",
            "A recognizable deployment configuration file was found.",
            [deployment_path],
            "Validate deployment settings and environment configuration before release.",
        )

    # ---------------------------------------------------------
    # Source code
    # ---------------------------------------------------------

    source_extensions = (
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".cpp",
        ".c",
        ".go",
        ".rs",
    )

    source_file = None

    for path in paths:
        if path.endswith(source_extensions):
            source_file = path
            break

    if not source_file:
        _add_finding(
            findings,
            "High",
            "Recognizable source files not detected",
            "No common application source-code file extension was found in the scanned repository tree.",
            ["Recursive repository tree scan"],
            "Verify that the repository contains the intended application source code.",
        )

    return {
        "success": True,
        "repository": repository_name,
        "findings": findings,
        "finding_count": len(findings),
        "analysis_type": "deterministic_release_readiness",
    }