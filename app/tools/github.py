import base64
import re

import requests

from app.config import GITHUB_USERNAME, GITHUB_TOKEN


def get_headers():
    headers = {
        "Accept": "application/vnd.github+json"
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    return headers


def github_user(user_input: str) -> str:
    username = GITHUB_USERNAME

    if not username:
        return "GitHub username is not configured."

    try:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            headers=get_headers(),
            params={
                "per_page": 100,
                "sort": "updated"
            },
            timeout=10
        )

        response.raise_for_status()

        repositories = response.json()

        if not repositories:
            return f"No public repositories found for {username}."

        repo_lines = []

        for repo in repositories:
            name = repo.get("name", "Unknown")
            description = repo.get("description") or "No description"
            language = repo.get("language") or "Unknown"

            repo_lines.append(
                f"- {name} | {language} | {description}"
            )

        return (
            f"GitHub repositories for {username}:\n"
            + "\n".join(repo_lines)
        )

    except requests.RequestException as exc:
        return f"GitHub request failed: {exc}"


def extract_repo_names(text: str):
    """
    Extract repository names from natural-language requests.

    Supports examples such as:

    Analyze the README of my heart-disease-prediction-ml project

    Read README for heart-disease-prediction-ml

    Analyze these repositories:
    heart-disease-prediction-ml
    fracture-detection-cnn
    """

    repo_names = []

    # GitHub repository URL
    url_pattern = r"github\.com/[^/\s]+/([A-Za-z0-9_.-]+)"
    repo_names.extend(re.findall(url_pattern, text))

    # Words that commonly identify repository names
    patterns = [
        r"(?:repository|repo|project)\s+(?:named\s+|called\s+)?['\"]?([A-Za-z0-9_.-]+)['\"]?",
        r"(?:README|readme)\s+(?:of|for)\s+(?:my\s+)?['\"]?([A-Za-z0-9_.-]+)",
        r"(?:analyze|analyse|read|check)\s+(?:the\s+)?(?:README\s+)?(?:of|for)\s+(?:my\s+)?['\"]?([A-Za-z0-9_.-]+)"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            if isinstance(match, tuple):
                match = match[-1]

            repo_names.append(match)

    # Explicit known repository-like tokens
    tokens = re.findall(
        r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b",
        text
    )

    for token in tokens:
        if (
            token.lower() not in {
                "machine-learning",
                "github-readme",
                "machine-learning-project"
            }
            and token not in repo_names
        ):
            repo_names.append(token)

    # Remove common natural-language words
    ignored_words = {
        "analyze",
        "analyse",
        "analysis",
        "read",
        "README",
        "github",
        "project",
        "projects",
        "repository",
        "repositories",
        "related",
        "machine-learning"
    }

    cleaned = []

    for repo in repo_names:
        repo = repo.strip(".,:;!?\"'`()[]{}")

        if not repo:
            continue

        if repo.lower() in {word.lower() for word in ignored_words}:
            continue

        if repo not in cleaned:
            cleaned.append(repo)

    return cleaned


def github_readme(repo_name: str) -> str:
    username = GITHUB_USERNAME

    if not username:
        return "GitHub username is not configured."

    repo_names = extract_repo_names(repo_name)

    if not repo_names:
        return {
            "error": "No repository names were found."
        }

    results = []

    for repository in repo_names:
        try:
            response = requests.get(
                f"https://api.github.com/repos/{username}/{repository}/readme",
                headers=get_headers(),
                timeout=10
            )

            if response.status_code == 404:
                results.append({
                    "repository": repository,
                    "success": False,
                    "error": "README not found."
                })
                continue

            response.raise_for_status()

            data = response.json()

            content = data.get("content")

            if not content:
                results.append({
                    "repository": repository,
                    "success": False,
                    "error": "README content is empty."
                })
                continue

            decoded_content = base64.b64decode(
                content
            ).decode(
                "utf-8",
                errors="replace"
            )

            results.append({
                "repository": repository,
                "success": True,
                "readme": decoded_content
            })

        except requests.RequestException as exc:
            results.append({
                "repository": repository,
                "success": False,
                "error": f"GitHub request failed: {exc}"
            })

        except Exception as exc:
            results.append({
                "repository": repository,
                "success": False,
                "error": f"Failed to decode README: {exc}"
            })

    return {
        "repositories": results
    }