import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


def web_search(query: str, max_results: int = 5):
    """Search the web and return a simple list of result dictionaries."""
    try:
        results = list(
            DDGS(verify=True).text(
                query=query,
                max_results=max_results,
                region="en-us",
                safesearch="on",
            )
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        return [{"error": f"search failed: {exc}"}]

    return [
        {
            "title": item.get("title", ""),
            "href": item.get("href", ""),
            "body": item.get("body", ""),
        }
        for item in results
        if isinstance(item, dict)
    ]


def open_url(url: str):
    """Fetch a URL and return cleaned text content."""
    if not url:
        return "error: no url provided"

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"error: failed to fetch url: {exc}"

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as exc:  # pragma: no cover - defensive guard
        return f"error: failed to parse html: {exc}"

    text = soup.get_text("\n", strip=True)
    return text[:4000] if len(text) > 4000 else text
