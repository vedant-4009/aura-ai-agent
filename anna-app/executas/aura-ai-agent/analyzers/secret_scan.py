import re
from typing import Any, Dict, List


SECRET_PATTERNS = [
    (
        "GitHub token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")
    ),
    (
        "Generic API key",
        re.compile(
            r"(?i)\b(?:api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"
        )
    ),
    (
        "Generic secret",
        re.compile(
            r"(?i)\b(?:secret|token|password|passwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        )
    ),
    (
        "Private key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
        )
    ),
]


SECRET_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
}


def _mask_value(value: str) -> str:
    """Never expose a detected secret value."""
    if len(value) <= 8:
        return "***"

    return f"{value[:4]}***{value[-4:]}"


def scan_text(text: str) -> List[Dict[str, Any]]:
    """
    Scan text for common credential-like patterns.

    Detected values are never returned in plaintext.
    """

    findings = []

    if not text:
        return findings

    for name, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            matched = match.group(0)

            findings.append(
                {
                    "type": name,
                    "evidence": _mask_value(matched),
                    "secret_exposed": False,
                }
            )

    return findings


def scan_file_path(path: str) -> List[Dict[str, Any]]:
    """
    Detect files whose names commonly indicate secret storage.
    """

    filename = path.replace("\\", "/").rsplit("/", 1)[-1].lower()

    if filename in SECRET_FILE_NAMES:
        return [
            {
                "type": "Secret-prone file",
                "path": path,
                "evidence": "Sensitive filename detected.",
                "secret_exposed": False,
            }
        ]

    return []


def scan_repository_files(
    files: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Perform safe filename-based secret scanning.

    This function does not expose file contents or secret values.
    """

    findings = []

    for item in files:
        path = item.get("path")

        if not path:
            continue

        findings.extend(scan_file_path(path))

    return {
        "success": True,
        "findings": findings,
        "finding_count": len(findings),
        "secrets_exposed": False,
        "scan_type": "safe_secret_filename_scan",
    }