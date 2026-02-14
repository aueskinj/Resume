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


PINNED_CONTENT = {
        "RAG": {
                "title": "RAG notebook deep dive",
                "description": "LangChain-powered RAG notebook with FAISS, FLAN-T5, MiniLM embeddings, PDF ingestion, and conversational memory.",
                "body_html": """
<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Technologies Used</h2>
    <ul class=\"list-disc pl-5 space-y-2 text-slate-700 dark:text-slate-300\">
        <li><strong>LangChain</strong>: Chains the document loaders, splitters, vector store, and LLM.</li>
        <li><strong>Hugging Face (Transformers &amp; Embeddings)</strong>: <em>google/flan-t5-large</em> for generation; <em>sentence-transformers/all-MiniLM-L6-v2</em> for embeddings.</li>
        <li><strong>FAISS</strong>: Vector database for fast semantic search over chunks.</li>
        <li><strong>PyMuPDF</strong>: Parses uploaded PDFs into text.</li>
        <li><strong>PyTorch</strong>: Backend for the Hugging Face models.</li>
        <li><strong>ipywidgets</strong>: Interactive UI inside the notebook.</li>
    </ul>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Notebook Flow</h2>
    <ol class=\"list-decimal pl-5 space-y-2 text-slate-700 dark:text-slate-300\">
        <li><strong>Setup</strong>: Installs dependencies, detects GPU.</li>
        <li><strong>Data Ingestion</strong>: Uploads a PDF and splits text with <code>RecursiveCharacterTextSplitter</code>.</li>
        <li><strong>Vector Database</strong>: Embeds chunks and stores them in FAISS.</li>
        <li><strong>Model Initialization</strong>: Loads <em>flan-t5-large</em> and creates a text-generation pipeline.</li>
        <li><strong>Basic RAG</strong>: Retrieves context and answers single-turn questions.</li>
        <li><strong>Conversational Memory</strong>: Rewrites follow-ups into standalone questions to keep chat history coherent.</li>
        <li><strong>Final Interface</strong>: Chat UI showing responses plus history.</li>
    </ol>
</section>
""",
        },
        "Data-Science-Projects": {
                "title": "Data Science Projects notebook set",
                "description": "Collection of data science notebooks spanning EDA, translation, scraping, classical ML, and causal analysis.",
                "body_html": """
<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Technologies Used</h2>
    <p class=\"text-slate-700 dark:text-slate-300\">Python notebooks across analytics and ML; typical stack includes pandas, numpy, seaborn/matplotlib, scikit-learn, TensorFlow/Keras (for translation), BeautifulSoup (for scraping).</p>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Notebook Breakdown</h2>
    <ol class=\"list-decimal pl-5 space-y-4 text-slate-700 dark:text-slate-300\">
        <li><strong>Student Performance Indicator</strong> — EDA through model selection; walks the ML lifecycle from problem framing to training and choosing the best model.</li>
        <li><strong>Effect of Government Social Programs on Poverty in Kenya</strong> — Descriptive analytics and correlations to understand program impact.</li>
        <li><strong>Effect of Petroleum Prices on Demand in Kenya</strong> — Correlation and descriptive analysis of price changes vs demand.</li>
        <li><strong>Effect of Taxation on SME Performance</strong> — Frequency analysis plus descriptive analytics on taxation effects.</li>
        <li><strong>Fine-Tuning English-Swahili Translation Model</strong> — Deep-learning fine-tuning using TensorFlow/Keras and CIFAR-10 style preprocessing.</li>
        <li><strong>Lyrics Finder</strong> — Scrapes Genius.com to gather song lyrics (URL collection + HTML parsing).</li>
        <li><strong>English-Kiswahili Translation Notebook</strong> — GPU-backed fine-tuning for translation tasks.</li>
        <li><strong>PandemAI</strong> — Data cleaning and formatting pipeline preparation.</li>
        <li><strong>Supervised Learning with SVM</strong> — Implements and evaluates SVM models.</li>
        <li><strong>Supervised Learning with Random Forests</strong> — Attribute selection, training, and evaluation with confusion matrices.</li>
        <li><strong>Customer Churn Prediction</strong> — Feature engineering plus multiple classifiers (RF, AdaBoost, SVC, XGBoost) compared via accuracy and reports.</li>
        <li><strong>Causal Inference with Bayesian Networks</strong> — Bayesian causal analysis (as listed in the contents).</li>
    </ol>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Getting Started</h2>
    <p class=\"text-slate-700 dark:text-slate-300\">Each notebook is runnable in Google Colab via the provided links in the repository; prerequisites include Python 3.x plus common data/ML libraries (TensorFlow, Keras, Matplotlib, Seaborn, NumPy, scikit-learn, BeautifulSoup, pandas, etc.).</p>
</section>
""",
        },
        "KiteGame": {
                "title": "KiteGame (pivot from Beach Buggy)",
                "description": "Flask + SocketIO real-time kite/buggy prototype with tests-in-progress and a playful roadmap of issues.",
                "body_html": """
<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">What the Project Is</h2>
    <p class=\"text-slate-700 dark:text-slate-300\">Started as Beach Buggy Racing and pivoted into a Kite Flying simulator. Expect lingering <code>BeachBuggy</code> classes and sand-related variables while the kite physics take shape.</p>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Tech Stack</h2>
    <ul class=\"list-disc pl-5 space-y-2 text-slate-700 dark:text-slate-300\">
        <li><strong>Python 3.x</strong></li>
        <li><strong>Flask + SocketIO</strong> for real-time transport</li>
        <li><strong>Eventlet</strong> for monkey patching</li>
        <li><strong>HTML5 Canvas</strong> + JavaScript for rendering</li>
        <li><strong>Tests</strong>: pytest-centric TDD mindset (coverage aspirational)</li>
    </ul>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Known Issues / TODOs</h2>
    <ul class=\"list-disc pl-5 space-y-2 text-slate-700 dark:text-slate-300\">
        <li>Duplicated classes from copy/paste.</li>
        <li>Level progression can freeze the (kite-formerly-car).</li>
        <li>Event system exists but is not wired through gameplay.</li>
        <li>Physics and wind feel unfinished; promises/async confusion noted.</li>
        <li>Tests exist but are incomplete; focus is on making them pass.</li>
    </ul>
    <p class=\"text-slate-700 dark:text-slate-300\">See the repository issues for the full backlog and humor-laced context.</p>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">How to Run</h2>
    <pre class=\"p-4 rounded bg-primary/10 text-slate-800 dark:text-slate-200 text-sm overflow-x-auto\">git clone https://github.com/aueskinj/KiteGame.git
cd KiteGame
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py</pre>
    <p class=\"text-slate-700 dark:text-slate-300\">Navigate to <code>http://localhost:5000</code> to see the prototype; pytest commands are provided in the README for test runs and coverage.</p>
</section>
""",
        },
        "web_crawler": {
                "title": "Async Web Crawler API",
                "description": "FastAPI + HTTPX crawler with Beautiful Soup parsing, image extraction variant, and domain-constrained crawling.",
                "body_html": """
<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Technologies Used</h2>
    <ul class=\"list-disc pl-5 space-y-2 text-slate-700 dark:text-slate-300\">
        <li><strong>FastAPI</strong> exposes <code>/crawl</code> and root endpoints with automatic docs.</li>
        <li><strong>Pydantic</strong> validates request/response models (e.g., <code>CrawlRequest</code>, <code>PageData</code>).</li>
        <li><strong>HTTPX</strong> handles async fetching.</li>
        <li><strong>Beautiful Soup</strong> parses HTML for titles, links, and images.</li>
        <li><strong>asyncio</strong> manages batched concurrency and depth/host limits.</li>
    </ul>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Repository Layout</h2>
    <ul class=\"list-disc pl-5 space-y-2 text-slate-700 dark:text-slate-300\">
        <li><strong>main.py</strong>: Core crawler with FastAPI; extracts URL, title, status, depth, link count.</li>
        <li><strong>data.py</strong>: Enhanced variant adding <code>ImageData</code> plus <code>extract_images</code> for image metadata.</li>
        <li><strong>README.md</strong>: Brief project description.</li>
    </ul>
</section>

<section class=\"space-y-3\">
    <h2 class=\"text-2xl font-bold text-slate-900 dark:text-white\">Key Behaviors</h2>
    <ul class=\"list-disc pl-5 space-y-2 text-slate-700 dark:text-slate-300\">
        <li>Batched async crawling via <code>asyncio.gather</code> (default batch size 5).</li>
        <li>Optional same-domain restriction to stay within the starting host.</li>
        <li>Image scraping path for richer responses when using <code>data.py</code>.</li>
    </ul>
</section>
""",
        },
}


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
    pinned_order = ["Data-Science-Projects", "KiteGame", "web_crawler", "RAG"]
    pinned_lookup = {r.name: r for r in repos}
    pinned = [pinned_lookup[name] for name in pinned_order if name in pinned_lookup]
    featured = pinned if pinned else sorted(repos, key=lambda r: (r.stars, r.sort_key), reverse=True)[:3]

    pinned_pages = []
    for repo in repos:
        detail = PINNED_CONTENT.get(repo.name)
        if not detail:
            continue
        pinned_pages.append(
            {
                "repo": repo,
                "title": detail["title"],
                "description": detail["description"],
                "body_html": detail["body_html"],
            }
        )

    pinned_map = {page["repo"].name: page["repo"].slug for page in pinned_pages}

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
            "pinned_map": pinned_map,
            "root_prefix": ".",
            "generated_at": generated_at,
        },
        OUTPUT_DIR / "index.html",
    )

    # Projects page (all repos)
    render(
        env,
        "projects.html",
        {
            "title": "Projects",
            "description": "All repositories and forks",
            "posts": repos,
            "pinned_map": pinned_map,
            "root_prefix": "..",
            "generated_at": generated_at,
        },
        OUTPUT_DIR / "projects" / "index.html",
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
                "pinned_map": pinned_map,
                "root_prefix": "../..",
                "generated_at": generated_at,
            },
            OUTPUT_DIR / "posts" / repo.slug / "index.html",
        )

    # Dedicated pages for pinned projects
    for page in pinned_pages:
        render(
            env,
            "pinned.html",
            {
                "title": page["title"],
                "description": page["description"],
                "repo": page["repo"],
                "body_html": page["body_html"],
                "root_prefix": "../..",
                "generated_at": generated_at,
            },
            OUTPUT_DIR / "pinned" / page["repo"].slug / "index.html",
        )

    print(f"Built {len(repos)} posts into {OUTPUT_DIR}")


if __name__ == "__main__":
    build_site()
