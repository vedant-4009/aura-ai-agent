import requests
from bs4 import BeautifulSoup

def fetch_webpage(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "AI-Agent/1.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = " ".join(soup.stripped_strings)
        return text[:20000]
    except Exception as exc:
        return f"Web request failed: {exc}"
