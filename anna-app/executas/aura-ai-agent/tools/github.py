import base64
import re

import requests

from aura_core.config import GITHUB_USERNAME, GITHUB_TOKEN


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


def github_repository(repository: str) -> dict:
    """Return structured metadata for one GitHub repository."""

    username = GITHUB_USERNAME

    if not username:
        return {
            "success": False,
            "error": "GitHub username is not configured."
        }

    repository = repository.strip().strip("/")

    if "/" in repository:
        owner, repo_name = repository.split("/", 1)
    else:
        owner, repo_name = username, repository

    if not repo_name:
        return {
            "success": False,
            "error": "Repository name is required."
        }

    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 404:
            return {
                "success": False,
                "repository": repo_name,
                "error": "Repository not found."
            }

        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "repository": {
                "full_name": data.get("full_name"),
                "name": data.get("name"),
                "description": data.get("description"),
                "language": data.get("language"),
                "default_branch": data.get("default_branch"),
                "visibility": data.get("visibility"),
                "private": data.get("private"),
                "fork": data.get("fork"),
                "archived": data.get("archived"),
                "updated_at": data.get("updated_at"),
                "html_url": data.get("html_url")
            }
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "repository": repo_name,
            "error": f"GitHub request failed: {exc}"
        }


def github_repository_tree(repository: str, path: str = "") -> dict:
    """Return a read-only list of files and directories from a GitHub repository."""

    username = GITHUB_USERNAME

    if not username:
        return {
            "success": False,
            "error": "GitHub username is not configured."
        }

    repository = repository.strip().strip("/")

    if "/" in repository:
        owner, repo_name = repository.split("/", 1)
    else:
        owner, repo_name = username, repository

    api_path = f"https://api.github.com/repos/{owner}/{repo_name}/contents"

    if path.strip("/"):
        api_path += "/" + path.strip("/")

    try:
        response = requests.get(
            api_path,
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 404:
            return {
                "success": False,
                "repository": repo_name,
                "path": path,
                "error": "Repository path not found."
            }

        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            return {
                "success": False,
                "repository": repo_name,
                "path": path,
                "error": "Expected a directory listing from GitHub."
            }

        items = []

        for item in data:
            items.append({
                "name": item.get("name"),
                "type": item.get("type"),
                "path": item.get("path")
            })

        return {
            "success": True,
            "repository": repo_name,
            "path": path or "/",
            "items": items
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "repository": repo_name,
            "path": path,
            "error": f"GitHub request failed: {exc}"
        }


def github_repository_tree_recursive(
    repository: str,
    path: str = "",
    max_depth: int = 3,
    max_files: int = 200,
) -> dict:
    """Recursively scan a GitHub repository tree with safety limits."""

    if max_depth < 0:
        return {
            "success": False,
            "error": "max_depth must be 0 or greater."
        }

    if max_files <= 0:
        return {
            "success": False,
            "error": "max_files must be greater than 0."
        }

    repository = repository.strip().strip("/")

    if not repository:
        return {
            "success": False,
            "error": "Repository name is required."
        }

    username = GITHUB_USERNAME

    if not username:
        return {
            "success": False,
            "error": "GitHub username is not configured."
        }

    if "/" in repository:
        owner, repo_name = repository.split("/", 1)
    else:
        owner, repo_name = username, repository

    base_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"

    files = []
    directories = []
    visited = set()
    errors = []

    def scan(current_path: str, depth: int) -> None:
        if len(files) >= max_files:
            return

        normalized_path = current_path.strip("/")

        if normalized_path in visited:
            return

        visited.add(normalized_path)

        api_path = base_url

        if normalized_path:
            api_path += "/" + normalized_path

        try:
            response = requests.get(
                api_path,
                headers=get_headers(),
                timeout=10
            )

            if response.status_code == 404:
                errors.append({
                    "path": normalized_path or "/",
                    "error": "Repository path not found."
                })
                return

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                errors.append({
                    "path": normalized_path or "/",
                    "error": "Expected a directory listing from GitHub."
                })
                return

        except requests.RequestException as exc:
            errors.append({
                "path": normalized_path or "/",
                "error": f"GitHub request failed: {exc}"
            })
            return

        for item in data:
            item_type = item.get("type")
            item_path = item.get("path", "")
            item_name = item.get("name", "")

            entry = {
                "name": item_name,
                "type": item_type,
                "path": item_path
            }

            if item_type == "file":
                if len(files) >= max_files:
                    return

                files.append(entry)

            elif item_type == "dir":
                directories.append(entry)

                if depth < max_depth and len(files) < max_files:
                    scan(item_path, depth + 1)

    scan(path, 0)

    return {
        "success": True,
        "repository": f"{owner}/{repo_name}",
        "path": path or "/",
        "max_depth": max_depth,
        "max_files": max_files,
        "files": files,
        "directories": directories,
        "file_count": len(files),
        "directory_count": len(directories),
        "truncated": len(files) >= max_files,
        "errors": errors
    }


def extract_repo_names(text: str):
    """
    Extract repository names from natural-language requests.

    Supports:
    - owner/repository
    - GitHub repository URLs
    - repository/project names in natural language
    """

    text = text.strip()
    repo_names = []

    # 1. owner/repository format
    full_repo_pattern = r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b"
    full_matches = re.findall(full_repo_pattern, text)

    for match in full_matches:
        if match not in repo_names:
            repo_names.append(match)

    # 2. GitHub repository URL
    url_pattern = r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    url_matches = re.findall(url_pattern, text, flags=re.IGNORECASE)

    for match in url_matches:
        if match not in repo_names:
            repo_names.append(match)

    # If owner/repository was found, return only those.
    # This prevents "vedant-4009/aura-ai-agent"
    # from becoming two separate repositories.
    if repo_names:
        return repo_names

    # 3. Single repository name from natural language
    patterns = [
        r"""(?:repository|repo|project)\s+(?:named\s+|called\s+)?['"]?([A-Za-z0-9_.-]+)['"]?""",
        r"""(?:README|readme)\s+(?:of|for)\s+(?:my\s+)?['"]?([A-Za-z0-9_.-]+)""",
        r"""(?:analyze|analyse|read|check)\s+(?:the\s+)?(?:README\s+)?(?:of|for)\s+(?:my\s+)?['"]?([A-Za-z0-9_.-]+)"""
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            if isinstance(match, tuple):
                match = match[-1]

            if match and match not in repo_names:
                repo_names.append(match)

    # 4. Hyphenated repository-like names
    tokens = re.findall(
        r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b",
        text
    )

    ignored_tokens = {
        "machine-learning",
        "github-readme",
        "machine-learning-project",
        "release-readiness",
    }

    for token in tokens:
        if token.lower() not in ignored_tokens:
            if token not in repo_names:
                repo_names.append(token)

    # 5. Remove common natural-language words
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
    }

    cleaned = []

    for repo in repo_names:
        repo = repo.strip(".,:;!?\"'`()[]{}")

        if not repo:
            continue

        if repo.lower() in {
            word.lower() for word in ignored_words
        }:
            continue

        if repo not in cleaned:
            cleaned.append(repo)

    return cleaned


def github_readme(repo_name: str):
    """Fetch and decode README content from one or more repositories."""

    username = GITHUB_USERNAME

    if not username:
        return {
            "error": "GitHub username is not configured."
        }

    repo_names = extract_repo_names(repo_name)

    if not repo_names:
        return {
            "error": "No repository names were found."
        }

    results = []

    for repository in repo_names:
        # Support owner/repository input.
        if "/" in repository:
            owner, repository_name = repository.split("/", 1)
        else:
            owner = username
            repository_name = repository

        try:
            response = requests.get(
                f"https://api.github.com/repos/{owner}/{repository_name}/readme",
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