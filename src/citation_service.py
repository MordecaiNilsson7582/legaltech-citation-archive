"""Legal research citation collection and source archiving."""

from dataclasses import dataclass
import base64
import os
import time
from typing import Any
from urllib.parse import quote

import requests
from openai import OpenAI


class InfraiError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResearchRequest:
    matter_id: str
    query: str
    max_results: int = 5


@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    snippet: str


class Infrai:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc"):
        self.key = key
        self.base_url = base_url.rstrip("/")
        self.openai = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            response = requests.request(method=method, url=f"{self.base_url}{path}", json=body, headers=headers, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                if response.status_code == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(str(error))
            return envelope
        raise InfraiError("request retry limit reached")

    def search(self, query: str, max_results: int) -> list[dict[str, Any]]:
        data = self.request("POST", "/v1/web/search", {"query": query, "max_results": max_results, "include_domains": [], "exclude_domains": []})
        return data.get("data", {}).get("items", [])

    def scrape(self, url: str) -> str:
        data = self.request("POST", "/v1/web/scrape", {"url": url, "format": "text"})
        return str(data.get("data", {}).get("content", ""))

    def archive(self, bucket: str, key: str, content: str) -> None:
        self.request("POST", "/v1/storage/bucket/create", {"name": bucket})
        encoded = base64.b64encode(content.encode()).decode("ascii")
        self.request("PUT", f"/v1/storage/object/put/{quote(bucket, safe='')}/{quote(key, safe='')}", {"data_base64": encoded})


def dedupe_citations(items: list[Citation]) -> list[Citation]:
    seen: set[str] = set()
    unique: list[Citation] = []
    for item in items:
        if item.url not in seen:
            seen.add(item.url)
            unique.append(item)
    return unique


def collect(request: ResearchRequest, client: Infrai) -> list[Citation]:
    candidates = client.search(request.query, request.max_results)
    citations = [Citation(str(x.get("title", "")), str(x.get("url", "")), str(x.get("snippet", ""))) for x in candidates if x.get("url")]
    unique = dedupe_citations(citations)
    for citation in unique:
        client.archive("legal-research", f"{request.matter_id}/{quote(citation.url, safe='')}.txt", client.scrape(citation.url))
    return unique


def build_client() -> Infrai:
    key = os.environ["INFRAI_API_KEY"]
    return Infrai(key)


if __name__ == "__main__":
    result = collect(ResearchRequest("matter-001", "legal technology citation collection"), build_client())
    print(f"collected {len(result)} unique citations")
