import requests
from ddgs import DDGS
from bs4 import BeautifulSoup

def web_search(query: str, max_results: int = 5):
    results = list(DDGS(verify=True).text(
        query=query,
        max_results=max_results,
        region="en-us",
        safesearch="on"))

    return results

def open_url(url: str):
    if not url.startswith("https://"):
        url = f"https://{url}"

    html = requests.get(url, timeout=10).text

    soup = BeautifulSoup(html, "html.parser")

    return soup.get_text(
        "\n",
        strip=True
    )
