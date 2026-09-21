import requests

from app.config import GITHUB_USERNAME


def github_user(user_input: str) -> str:
    """
    Fetch GitHub repository information.

    The tool accepts a natural-language request and uses the
    configured GitHub username instead of treating the whole
    sentence as a username.
    """

    username = GITHUB_USERNAME

    if not username:
        return "GitHub username is not configured."

    try:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
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