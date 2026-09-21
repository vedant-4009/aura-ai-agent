import requests

from app.config import GITHUB_USERNAME, GITHUB_TOKEN


def github_user(user_input: str) -> str:
    """
    Fetch GitHub repository information using
    an authenticated GitHub API request.
    """

    username = GITHUB_USERNAME

    if not username:
        return "GitHub username is not configured."

    headers = {
        "Accept": "application/vnd.github+json"
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            headers=headers,
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