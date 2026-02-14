"""
Static blog generator for GitHub repositories.

Loads public_repos.json, builds normalized repo objects, and renders
static pages into dist/ using Jinja templates.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:  # pragma: no cover
    print("Jinja2 is required. Install with: pip install jinja2", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "public_repos.json"
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "dist"
ASSETS_SRC = ROOT / "assets"
MEDIUM_PATH = ROOT / "medium.txt"


@dataclass
class RepoPost:
    slug: str
    name: str
    full_name: str
    description: str
    summary: str
    html_url: str
    homepage: Optional[str]
    language: str
    topics: List[str]
    license: Optional[str]
    fork: bool
    default_branch: str
    stargazers_count: int
    forks_count: int
    watchers_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    pushed_at: Optional[datetime]
    plan: Optional[str]

    def __post_init__(self) -> None:
        def fmt(dt: Optional[datetime]) -> str:
            return dt.strftime("%b %d, %Y") if dt else "n/a"

        self.created_label = fmt(self.created_at)
        self.updated_label = fmt(self.updated_at)
        self.pushed_label = fmt(self.pushed_at)
        # For sorting, prefer pushed_at then updated_at then created_at
        self.sort_key = self.pushed_at or self.updated_at or self.created_at or datetime.min
        self.tags = self._build_tags()

    @property
    def stars(self) -> int:
        return self.stargazers_count

    def _build_tags(self) -> List[str]:
        tags = []
        if self.language:
            tags.append(self.language)
        if self.fork:
            tags.append("fork")
        tags.extend(self.topics or [])
        return tags


@dataclass
class MediumPost:
    title: str
    link: str
    published: Optional[datetime]
    tags: List[str]

    @property
    def published_label(self) -> str:
        return self.published.strftime("%b %d, %Y") if self.published else "n/a"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "repo"


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_medium_date(value: str) -> Optional[datetime]:
    # Example: Fri, 19 Dec 2025 13:16:15 GMT
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def planned_changes(repo: RepoPost) -> str:
    lang = (repo.language or "project").lower()
    shared = (
        "Keep this fork close to upstream while tailoring it for my workflows. "
        "Document setup, add CI, and keep dependencies up to date."
    )
    if "python" in lang:
        extra = " Add type hints, tighten linting (ruff/black), and flesh out tests before feature work."
    elif "js" in lang or "typescript" in lang:
        extra = " Add linting/formatting, wire a minimal test runner, and improve DX docs."
    elif lang in {"c", "cpp", "c++"}:
        extra = " Add formatting/tooling, improve README build steps, and harden with small unit tests."
    else:
        extra = " Improve docs, add CI coverage, and ship small quality-of-life fixes."
    return shared + extra


def normalize_repo(raw: dict) -> RepoPost:
    name = raw.get("name") or "untitled"
    description = (raw.get("description") or "No description yet.").strip()
    summary = description if len(description) <= 180 else description[:177] + "..."
    repo = RepoPost(
        slug=slugify(name),
        name=name,
        full_name=raw.get("full_name") or name,
        description=description,
        summary=summary,
        html_url=raw.get("html_url") or "",
        homepage=raw.get("homepage") or None,
        language=raw.get("language") or "Unspecified",
        topics=raw.get("topics") or [],
        license=(raw.get("license") or {}).get("name"),
        fork=bool(raw.get("fork")),
        default_branch=raw.get("default_branch") or "main",
        stargazers_count=int(raw.get("stargazers_count") or 0),
        forks_count=int(raw.get("forks_count") or 0),
        watchers_count=int(raw.get("watchers_count") or 0),
        created_at=parse_date(raw.get("created_at")),
        updated_at=parse_date(raw.get("updated_at")),
        pushed_at=parse_date(raw.get("pushed_at")),
        plan=None,
    )
    if repo.fork:
        repo.plan = planned_changes(repo)
    return repo


def parse_medium_posts() -> List[MediumPost]:
    if not MEDIUM_PATH.exists():
        return []
    text = MEDIUM_PATH.read_text(encoding="utf-8")
    blocks = [block.strip() for block in text.split("---") if block.strip()]
    posts: List[MediumPost] = []
    for block in blocks:
        title = link = date = None
        tags: List[str] = []
        for line in block.splitlines():
            if line.startswith("Title:"):
                title = line.replace("Title:", "", 1).strip()
            elif line.startswith("Link:"):
                link = line.replace("Link:", "", 1).strip()
            elif line.startswith("Date:"):
                date = line.replace("Date:", "", 1).strip()
            elif line.startswith("Tags:"):
                raw_tags = line.replace("Tags:", "", 1).strip()
                # Tags line might be "None" or a Python-like list representation
                if raw_tags and raw_tags.lower() != "none":
                    raw_tags = raw_tags.strip().strip("[]")
                    tags = [t.strip(" ' \"") for t in raw_tags.split(",") if t.strip(" ' \"")]
        if not (title and link):
            continue
        posts.append(
            MediumPost(
                title=title,
                link=link,
                published=parse_medium_date(date or "") if date else None,
                tags=tags,
            )
        )
    posts.sort(key=lambda p: p.published or datetime.min, reverse=True)
    return posts


def load_repos() -> List[RepoPost]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return [normalize_repo(raw) for raw in data]


def build_tags(repos: Iterable[RepoPost]) -> List[dict]:
    tag_map: dict[str, List[RepoPost]] = {}
    for repo in repos:
        for tag in repo.tags:
            tag_map.setdefault(tag, []).append(repo)
    tags = [
        {
            "name": name,
            "slug": slugify(name),
            "count": len(items),
            "repos": sorted(items, key=lambda r: r.sort_key, reverse=True),
        }
        for name, items in tag_map.items()
    ]
    tags.sort(key=lambda t: t["name"].lower())
    return tags


def copy_assets() -> None:
    target = OUTPUT_DIR / "assets"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ASSETS_SRC, target)


def ensure_output_dir() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def render(env: Environment, template_name: str, context: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    html = env.get_template(template_name).render(**context)
    destination.write_text(html, encoding="utf-8")


def build_site() -> None:
    repos = load_repos()
    repos.sort(key=lambda r: r.sort_key, reverse=True)
    medium_posts = parse_medium_posts()
    featured = sorted(repos, key=lambda r: (r.stars, r.sort_key), reverse=True)[:3]

    ensure_output_dir()
    copy_assets()

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    generated_at = datetime.now(timezone.utc).strftime("%b %d, %Y")
    stats = {
        "total": len(repos),
        "forks": sum(1 for r in repos if r.fork),
        "languages": len({r.language for r in repos if r.language}),
        "last_pushed": repos[0].pushed_label if repos else "n/a",
    }

    tags = build_tags(repos)

    # Index
    render(
        env,
        "index.html",
        {
            "title": "Home",
            "description": "Blog listing of repositories and forks",
            "featured": featured,
            "posts": repos,
            "stats": stats,
            "medium_posts": medium_posts[:3],
            "root_prefix": ".",
            "generated_at": generated_at,
        },
        OUTPUT_DIR / "index.html",
    )

    # Tags index
    render(
        env,
        "tags.html",
        {
            "title": "Tags",
            "description": "Browse repositories by language or topic",
            "tags": tags,
            "root_prefix": "..",
            "generated_at": generated_at,
        },
        OUTPUT_DIR / "tags" / "index.html",
    )

    # Individual tags
    for tag in tags:
        render(
            env,
            "tag.html",
            {
                "title": f"Tag: {tag['name']}",
                "description": f"Repositories tagged with {tag['name']}",
                "tag": tag,
                "posts": tag["repos"],
                "root_prefix": "../..",
                "generated_at": generated_at,
            },
            OUTPUT_DIR / "tags" / tag["slug"] / "index.html",
        )

    # Individual posts
    for repo in repos:
        render(
            env,
            "post.html",
            {
                "title": repo.name,
                "description": repo.summary,
                "repo": repo,
                "root_prefix": "../..",
                "generated_at": generated_at,
            },
            OUTPUT_DIR / "posts" / repo.slug / "index.html",
        )

    print(f"Built {len(repos)} posts into {OUTPUT_DIR}")


if __name__ == "__main__":
    build_site()
