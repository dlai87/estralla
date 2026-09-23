"""Source registry and official-first source classification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

URL_PATTERN = re.compile(r"https?://[^\s)<>\]]+")


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    authority: str
    topics: tuple[str, ...]
    fit: str

    @property
    def is_official(self) -> bool:
        return self.authority.startswith("official")

    @property
    def is_practitioner_reference(self) -> bool:
        return self.authority == "practitioner_reference"


class SourceRegistry:
    def __init__(self, sources: list[Source], last_verified: str | None = None):
        self.sources = sources
        self.last_verified = last_verified

    @classmethod
    def load(cls, path: Path | None = None) -> SourceRegistry:
        registry_path = path or default_registry_path()
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
        sources = [
            Source(
                id=item["id"],
                name=item["name"],
                url=item["url"],
                authority=item["authority"],
                topics=tuple(item.get("topics", [])),
                fit=item.get("fit", ""),
            )
            for item in raw.get("sources", [])
        ]
        return cls(sources=sources, last_verified=raw.get("last_verified"))

    def get(self, source_id: str) -> Source | None:
        return next((source for source in self.sources if source.id == source_id), None)

    def classify_url(self, url: str) -> Source | None:
        normalized = normalize_url(url)
        parsed = urlparse(normalized)
        for source in self.sources:
            source_url = normalize_url(source.url)
            source_parsed = urlparse(source_url)
            if normalized.startswith(source_url):
                return source
            if (
                parsed.netloc == source_parsed.netloc
                and source_parsed.path
                and parsed.path.startswith(source_parsed.path.rstrip("/"))
            ):
                return source
            if parsed.netloc == source_parsed.netloc and not source_parsed.path.strip("/"):
                return source
        return None

    def preferred_sources(self, topics: list[str] | tuple[str, ...]) -> list[Source]:
        topic_set = set(topics)
        matches = [source for source in self.sources if topic_set.intersection(source.topics)]
        official = [source for source in matches if source.is_official]
        practitioner = [source for source in matches if source.is_practitioner_reference]
        return official + practitioner


def default_registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "source-registry.json"


def extract_urls(content: str) -> list[str]:
    urls: list[str] = []
    for match in URL_PATTERN.findall(content):
        urls.append(match.rstrip(".,;:"))
    return urls


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")
