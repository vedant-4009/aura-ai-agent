from typing import Any, Dict, List

from analyzers.readme_analyzer import analyze_readme
from analyzers.secret_scan import scan_repository_files


def _add_finding(
    findings: List[Dict[str, Any]],
    title: str,
    severity: str,
    fact: str,
    evidence: List[str],
    recommendation: str,
) -> None:
    findings.append(
        {
            "title": title,
            "severity": severity,
            "fact": fact,
            "evidence": evidence,
            "recommendation": recommendation,
        }
    )


def _extract_readme_content(readme_result: Any) -> str | None:
    """
    Extract README text from the result returned by github_readme().

    Supports:
    - direct string
    - {"readme": "..."}
    - {"repositories": [{"readme": "..."}]}
    """

    if isinstance(readme_result, str):
        content = readme_result.strip()
        return content if content else None

    if not isinstance(readme_result, dict):
        return None

    direct_readme = readme_result.get("readme")

    if isinstance(direct_readme, str):
        content = direct_readme.strip()
        if content:
            return content

    repositories = readme_result.get("repositories", [])

    if isinstance(repositories, list):
        for repository in repositories:
            if not isinstance(repository, dict):
                continue

            content = repository.get("readme")

            if isinstance(content, str) and content.strip():
                return content.strip()

    return None


def _analyze_readme_quality(
    snapshot: Dict[str, Any],
    findings: List[Dict[str, Any]],
) -> Dict[str, Any] | None:
    """
    Run the dedicated README content-quality analyzer.

    The analyzer is intentionally separate from the generic
    repository checks so README quality can evolve independently.
    """

    readme_result = snapshot.get("readme")
    readme_content = _extract_readme_content(readme_result)

    if not readme_content:
        return None

    analysis = analyze_readme(readme_content)

    if not analysis.get("success"):
        return analysis

    for item in analysis.get("findings", []):
        _add_finding(
            findings=findings,
            title=f"README: {item.get('title', 'Documentation finding')}",
            severity=item.get("severity", "Informational"),
            fact=item.get(
                "fact",
                "README documentation information was analyzed.",
            ),
            evidence=item.get(
                "evidence",
                ["README content analysis"],
            ),
            recommendation=item.get(
                "recommendation",
                "Keep README documentation clear and up to date.",
            ),
        )

    return analysis


def analyze_release_readiness(
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze a repository snapshot for release readiness.

    Design principles:
    - Evidence-first
    - Read-only analysis
    - No overall score
    - Severity-based findings
    - Facts, evidence and recommendations remain separate
    - Safe secret detection
    """

    if not isinstance(snapshot, dict):
        return {
            "success": False,
            "error": "Repository snapshot must be a dictionary.",
            "findings": [],
        }

    findings: List[Dict[str, Any]] = []

    repository = snapshot.get("repository", {})
    files = snapshot.get("files", [])
    directories = snapshot.get("directories", [])

    if not isinstance(repository, dict):
        repository = {}

    if not isinstance(files, list):
        files = []

    if not isinstance(directories, list):
        directories = []

    # ---------------------------------------------------------
    # Repository identity
    # ---------------------------------------------------------

    repository_name = repository.get(
        "full_name",
        repository.get("name", "Unknown repository"),
    )

    # ---------------------------------------------------------
    # README detection + README quality analysis
    # ---------------------------------------------------------

    readme_files = [
        item
        for item in files
        if isinstance(item, dict)
        and str(item.get("path", "")).lower()
        in {
            "readme",
            "readme.md",
            "readme.txt",
            "readme.rst",
        }
    ]

    readme_analysis = None

    if readme_files:
        _add_finding(
            findings=findings,
            title="README detected",
            severity="Informational",
            fact="A README file was detected in the repository.",
            evidence=[
                f"README file: {item.get('path')}"
                for item in readme_files
            ],
            recommendation=(
                "Keep the README accurate, complete, and aligned "
                "with the current project."
            ),
        )

        readme_analysis = _analyze_readme_quality(
            snapshot,
            findings,
        )

    else:
        _add_finding(
            findings=findings,
            title="README not detected",
            severity="Medium",
            fact="No recognizable README file was detected.",
            evidence=[
                "Repository file tree scan did not find README.md, "
                "README.txt, README.rst, or README."
            ],
            recommendation=(
                "Add a README containing project purpose, setup, "
                "usage, configuration, and deployment guidance."
            ),
        )

    # ---------------------------------------------------------
    # License
    # ---------------------------------------------------------

    license_names = {
        "license",
        "license.md",
        "license.txt",
        "copying",
        "copying.md",
    }

    license_files = [
        item
        for item in files
        if isinstance(item, dict)
        and str(item.get("path", "")).lower().split("/")[-1]
        in license_names
    ]

    if license_files:
        _add_finding(
            findings=findings,
            title="License detected",
            severity="Informational",
            fact="A license file was detected.",
            evidence=[
                f"License file: {item.get('path')}"
                for item in license_files
            ],
            recommendation=(
                "Verify that the selected license matches "
                "the intended project and distribution model."
            ),
        )
    else:
        _add_finding(
            findings=findings,
            title="License not detected",
            severity="Medium",
            fact="No common license file was detected.",
            evidence=[
                "Repository file tree scan did not find a common "
                "license file."
            ],
            recommendation=(
                "Add an appropriate license before distributing "
                "the project publicly."
            ),
        )

    # ---------------------------------------------------------
    # Automated tests
    # ---------------------------------------------------------

    test_file_patterns = (
        "test_",
        "tests/",
        "test/",
        "_test.py",
        ".test.js",
        ".test.ts",
        ".spec.js",
        ".spec.ts",
    )

    test_files = []

    for item in files:
        if not isinstance(item, dict):
            continue

        path = str(item.get("path", "")).lower()

        if any(pattern in path for pattern in test_file_patterns):
            test_files.append(path)

    if test_files:
        _add_finding(
            findings=findings,
            title="Automated tests detected",
            severity="Informational",
            fact="Potential automated test files were detected.",
            evidence=[
                f"Test candidate: {path}"
                for path in test_files[:10]
            ],
            recommendation=(
                "Keep automated tests maintained and run them "
                "before releases."
            ),
        )
    else:
        _add_finding(
            findings=findings,
            title="Automated tests not detected",
            severity="Medium",
            fact="No recognizable automated test files were detected.",
            evidence=[
                "Repository file tree scan did not find common "
                "test directories or test file patterns."
            ],
            recommendation=(
                "Add automated tests for important application "
                "logic and release-critical paths."
            ),
        )

    # ---------------------------------------------------------
    # CI/CD workflow
    # ---------------------------------------------------------

    ci_files = []

    for item in files:
        if not isinstance(item, dict):
            continue

        path = str(item.get("path", "")).lower()

        if (
            path.startswith(".github/workflows/")
            or path.startswith(".gitlab-ci")
            or path.startswith(".circleci/")
            or path in {
                "jenkinsfile",
                ".travis.yml",
                "azure-pipelines.yml",
            }
        ):
            ci_files.append(path)

    if ci_files:
        _add_finding(
            findings=findings,
            title="CI/CD workflow detected",
            severity="Informational",
            fact="A recognizable CI/CD configuration was detected.",
            evidence=[
                f"CI/CD file: {path}"
                for path in ci_files[:10]
            ],
            recommendation=(
                "Keep CI/CD checks aligned with the release "
                "requirements of the project."
            ),
        )
    else:
        _add_finding(
            findings=findings,
            title="CI workflow not detected",
            severity="Low",
            fact="No recognizable CI/CD workflow configuration was detected.",
            evidence=[
                "Repository file tree scan did not find common "
                "CI/CD configuration files."
            ],
            recommendation=(
                "Consider adding CI automation for tests, linting, "
                "build validation, and release checks."
            ),
        )

    # ---------------------------------------------------------
    # Dependency configuration
    # ---------------------------------------------------------

    dependency_files = []

    dependency_names = {
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "pipfile",
        "pipfile.lock",
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "go.mod",
        "go.sum",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "cargo.toml",
        "cargo.lock",
    }

    for item in files:
        if not isinstance(item, dict):
            continue

        filename = str(item.get("path", "")).lower().split("/")[-1]

        if filename in dependency_names:
            dependency_files.append(item.get("path"))

    if dependency_files:
        _add_finding(
            findings=findings,
            title="Dependency configuration detected",
            severity="Informational",
            fact="Dependency configuration files were detected.",
            evidence=[
                f"Dependency file: {path}"
                for path in dependency_files[:10]
            ],
            recommendation=(
                "Keep dependencies versioned and review dependency "
                "updates before releases."
            ),
        )
    else:
        _add_finding(
            findings=findings,
            title="Dependency configuration not detected",
            severity="Low",
            fact="No common dependency configuration file was detected.",
            evidence=[
                "Repository file tree scan did not find common "
                "dependency configuration files."
            ],
            recommendation=(
                "Add an explicit dependency configuration so "
                "environments can be reproduced reliably."
            ),
        )

    # ---------------------------------------------------------
    # Environment configuration
    # ---------------------------------------------------------

    environment_examples = []

    environment_names = {
        ".env.example",
        ".env.sample",
        ".env.template",
        "env.example",
    }

    for item in files:
        if not isinstance(item, dict):
            continue

        filename = str(item.get("path", "")).lower().split("/")[-1]

        if filename in environment_names:
            environment_examples.append(item.get("path"))

    if environment_examples:
        _add_finding(
            findings=findings,
            title="Environment configuration template detected",
            severity="Informational",
            fact="An environment configuration template was detected.",
            evidence=[
                f"Environment template: {path}"
                for path in environment_examples
            ],
            recommendation=(
                "Keep environment templates documented without "
                "including real credentials or secrets."
            ),
        )
    else:
        _add_finding(
            findings=findings,
            title="Environment configuration template not detected",
            severity="Low",
            fact="No common environment configuration template was detected.",
            evidence=[
                "Repository file tree scan did not find common "
                "environment template files."
            ],
            recommendation=(
                "Consider adding a sanitized environment template "
                "such as .env.example."
            ),
        )

    # ---------------------------------------------------------
    # Secret-prone files
    # ---------------------------------------------------------

    secret_scan = scan_repository_files(files)

    secret_findings = secret_scan.get("findings", [])

    if secret_findings:
        for item in secret_findings:
            _add_finding(
                findings=findings,
                title="Secret-prone file detected",
                severity="High",
                fact=(
                    "A filename commonly associated with sensitive "
                    "credentials or private keys was detected."
                ),
                evidence=[
                    item.get(
                        "evidence",
                        "Sensitive filename detected.",
                    ),
                    f"Path: {item.get('path', 'unknown')}",
                ],
                recommendation=(
                    "Do not commit secrets. Remove sensitive files "
                    "from the repository and use environment variables "
                    "or a dedicated secret manager."
                ),
            )
    else:
        _add_finding(
            findings=findings,
            title="No secret-prone filenames detected",
            severity="Informational",
            fact=(
                "No filenames commonly associated with local secrets "
                "or private keys were detected."
            ),
            evidence=[
                "Safe filename-based secret scan completed.",
                "No secret-prone filenames were detected.",
            ],
            recommendation=(
                "Continue keeping credentials outside source control "
                "and rotate exposed credentials immediately if found."
            ),
        )

    # ---------------------------------------------------------
    # Docker
    # ---------------------------------------------------------

    docker_files = []

    for item in files:
        if not isinstance(item, dict):
            continue

        path = str(item.get("path", "")).lower()

        if (
            path == "dockerfile"
            or path.endswith("/dockerfile")
            or "docker-compose" in path
            or "compose.yml" in path
            or "compose.yaml" in path
        ):
            docker_files.append(item.get("path"))

    if docker_files:
        _add_finding(
            findings=findings,
            title="Container configuration detected",
            severity="Informational",
            fact="Docker or container configuration was detected.",
            evidence=[
                f"Container file: {path}"
                for path in docker_files[:10]
            ],
            recommendation=(
                "Review container images, exposed ports, runtime "
                "permissions, and dependency versions before deployment."
            ),
        )

    # ---------------------------------------------------------
    # Deployment configuration
    # ---------------------------------------------------------

    deployment_files = []

    deployment_names = {
        "vercel.json",
        "render.yaml",
        "railway.json",
        "railway.toml",
        "fly.toml",
        "netlify.toml",
        "app.yaml",
        "app.yml",
        "serverless.yml",
        "serverless.yaml",
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    }

    for item in files:
        if not isinstance(item, dict):
            continue

        filename = str(item.get("path", "")).lower().split("/")[-1]

        if filename in deployment_names:
            deployment_files.append(item.get("path"))

    if deployment_files:
        _add_finding(
            findings=findings,
            title="Deployment configuration detected",
            severity="Informational",
            fact="A recognizable deployment configuration was detected.",
            evidence=[
                f"Deployment file: {path}"
                for path in deployment_files[:10]
            ],
            recommendation=(
                "Review deployment configuration and verify "
                "production environment settings before release."
            ),
        )
    else:
        _add_finding(
            findings=findings,
            title="Deployment configuration not detected",
            severity="Informational",
            fact="No common deployment configuration file was detected.",
            evidence=[
                "Repository file tree scan did not find common "
                "deployment configuration files."
            ],
            recommendation=(
                "If the project requires automated deployment, "
                "consider adding an explicit deployment configuration."
            ),
        )

    # ---------------------------------------------------------
    # Source code detection
    # ---------------------------------------------------------

    source_extensions = {
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
        ".rb",
        ".php",
    }

    source_files = []

    for item in files:
        if not isinstance(item, dict):
            continue

        path = str(item.get("path", ""))

        if "." in path:
            extension = "." + path.rsplit(".", 1)[-1].lower()

            if extension in source_extensions:
                source_files.append(path)

    if source_files:
        _add_finding(
            findings=findings,
            title="Source code detected",
            severity="Informational",
            fact="Application source files were detected.",
            evidence=[
                f"Source file: {path}"
                for path in source_files[:10]
            ],
            recommendation=(
                "Ensure critical source paths are covered by "
                "tests and reviewed before production releases."
            ),
        )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    severity_order = {
        "Critical": 0,
        "High": 1,
        "Medium": 2,
        "Low": 3,
        "Informational": 4,
    }

    findings.sort(
        key=lambda item: severity_order.get(
            item.get("severity", "Informational"),
            99,
        )
    )

    severity_counts = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "Informational": 0,
    }

    for finding in findings:
        severity = finding.get("severity", "Informational")

        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "success": True,
        "analysis_type": "release_readiness",
        "repository": repository_name,
        "finding_count": len(findings),
        "severity_counts": severity_counts,
        "findings": findings,
        "readme_analysis": readme_analysis,
        "secret_scan": {
            "success": secret_scan.get("success", False),
            "finding_count": secret_scan.get("finding_count", 0),
            "secrets_exposed": secret_scan.get(
                "secrets_exposed",
                False,
            ),
            "scan_type": secret_scan.get(
                "scan_type",
                "safe_secret_filename_scan",
            ),
        },
    }