import re
from typing import Any, Dict


README_SECTIONS = {
    "description": {
        "label": "Project description",
        "headings": [
            "description",
            "overview",
            "about",
        ],
    },
    "installation": {
        "label": "Installation instructions",
        "headings": [
            "installation",
            "install",
            "setup",
            "getting started",
        ],
    },
    "usage": {
        "label": "Usage instructions",
        "headings": [
            "usage",
            "how to use",
            "how it works",
            "examples",
            "example",
        ],
    },
    "configuration": {
        "label": "Configuration instructions",
        "headings": [
            "configuration",
            "config",
            "environment variables",
            "environment",
        ],
    },
    "deployment": {
        "label": "Deployment instructions",
        "headings": [
            "deployment",
            "deploy",
            "production",
            "hosting",
        ],
    },
}


def _extract_headings(readme: str) -> list[str]:
    """Extract Markdown headings from README content."""

    headings = []

    for line in readme.splitlines():
        match = re.match(
            r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$",
            line,
        )

        if match:
            heading = match.group(1).strip().lower()

            heading = re.sub(r"`", "", heading)
            heading = re.sub(r"\*\*", "", heading)
            heading = re.sub(r"__", "", heading)

            headings.append(heading)

    return headings


def _find_matching_heading(
    headings: list[str],
    keywords: list[str],
) -> str | None:

    for heading in headings:
        normalized_heading = heading.strip().lower()

        for keyword in keywords:
            if normalized_heading == keyword.lower():
                return heading

    return None


def _has_description_content(readme: str) -> bool:
    """
    Detect a meaningful introductory paragraph before
    the first Markdown heading after the title.
    """

    lines = readme.splitlines()
    content_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if content_lines:
                break
            continue

        if stripped.startswith("#"):
            if content_lines:
                break
            continue

        if stripped.startswith("!["):
            continue

        if stripped.startswith("[!["):
            continue

        content_lines.append(stripped)

    text = " ".join(content_lines).strip()

    return len(text.split()) >= 8


def _has_installation_content(readme: str) -> bool:
    patterns = [
        r"\bpip\s+install\b",
        r"\bnpm\s+install\b",
        r"\bnpm\s+i\b",
        r"\buv\s+pip\s+install\b",
        r"\buv\s+sync\b",
        r"\bpoetry\s+install\b",
        r"\bgit\s+clone\b",
    ]

    return any(
        re.search(pattern, readme, flags=re.IGNORECASE)
        for pattern in patterns
    )


def _has_usage_content(readme: str) -> bool:
    patterns = [
        r"\bpython\s+\S+\.py\b",
        r"\bpython\s+-m\b",
        r"\buvicorn\b",
        r"\bnpm\s+run\b",
        r"\bnpm\s+start\b",
        r"\bhow\s+to\s+use\b",
        r"\busage\b",
        r"\bexample\b",
    ]

    return any(
        re.search(pattern, readme, flags=re.IGNORECASE)
        for pattern in patterns
    )


def _has_configuration_content(readme: str) -> bool:
    patterns = [
        r"\.env\b",
        r"\benvironment\s+variables?\b",
        r"\bapi[_ -]?key\b",
        r"\bconfiguration\b",
        r"\bconfig\b",
    ]

    return any(
        re.search(pattern, readme, flags=re.IGNORECASE)
        for pattern in patterns
    )


def _has_deployment_content(readme: str) -> bool:
    patterns = [
        r"\bdeployment\b",
        r"\bdeploy\b",
        r"\bproduction\b",
        r"\bhosting\b",
        r"\bvercel\b",
        r"\brender\b",
        r"\brailway\b",
        r"\baws\b",
        r"\bazure\b",
        r"\bgcp\b",
    ]

    return any(
        re.search(pattern, readme, flags=re.IGNORECASE)
        for pattern in patterns
    )


def _content_match(section_name: str, readme: str) -> bool:
    if section_name == "description":
        return _has_description_content(readme)

    if section_name == "installation":
        return _has_installation_content(readme)

    if section_name == "usage":
        return _has_usage_content(readme)

    if section_name == "configuration":
        return _has_configuration_content(readme)

    if section_name == "deployment":
        return _has_deployment_content(readme)

    return False


def analyze_readme(readme: str) -> Dict[str, Any]:
    """
    Analyze README documentation using both:

    1. Markdown heading detection
    2. Content-pattern detection

    This does not guarantee documentation completeness.
    """

    if not readme or not readme.strip():
        return {
            "success": False,
            "error": "README content is empty.",
            "sections": {},
            "findings": [],
        }

    headings = _extract_headings(readme)

    sections = {}
    findings = []

    for section_name, config in README_SECTIONS.items():

        label = config["label"]
        keywords = config["headings"]

        matched_heading = _find_matching_heading(
            headings,
            keywords,
        )

        heading_found = matched_heading is not None
        content_found = _content_match(
            section_name,
            readme,
        )

        found = heading_found or content_found

        if heading_found:
            evidence = [
                f"Markdown heading: {matched_heading}"
            ]
            detection_method = "heading"

        elif content_found:
            evidence = [
                "README content pattern detected."
            ]
            detection_method = "content"

        else:
            evidence = [
                "README heading and content scan"
            ]
            detection_method = "not_detected"

        sections[section_name] = {
            "found": found,
            "matched_heading": matched_heading,
            "detection_method": detection_method,
            "expected_headings": keywords,
        }

        if found:
            findings.append({
                "title": f"{label} detected",
                "severity": "Informational",
                "fact": (
                    f"{label} were detected in the README."
                ),
                "evidence": evidence,
                "recommendation": (
                    f"Keep the {label.lower()} clear and up to date."
                ),
            })

        else:
            findings.append({
                "title": f"{label} missing",
                "severity": "Low",
                "fact": (
                    f"No recognizable {label.lower()} "
                    "were detected in the README."
                ),
                "evidence": evidence,
                "recommendation": (
                    f"Add clear {label.lower()} to help developers "
                    "understand and use the project."
                ),
            })

    return {
        "success": True,
        "analysis_type": "readme_content_quality",
        "headings": headings,
        "sections": sections,
        "findings": findings,
        "finding_count": len(findings),
    }