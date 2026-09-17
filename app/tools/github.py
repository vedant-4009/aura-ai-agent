import os
import requests

def github_user(username: str) -> str:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        return (
            f"Username: {data.get('login')}\n"
            f"Name: {data.get('name')}\n"
            f"Bio: {data.get('bio')}\n"
            f"Public repositories: {data.get('public_repos')}\n"
            f"Followers: {data.get('followers')}\n"
            f"Following: {data.get('following')}\n"
            f"Profile: {data.get('html_url')}"
        )
    except Exception as exc:
        return f"GitHub request failed: {exc}"
