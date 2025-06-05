import hashlib
import json
import os
import pickle
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi_utils.tasks import repeat_every
from groq import Groq

BEE_FEED = "https://babylonbee.com/feed"
BEE_FEED_TEST = "test/resources/feed_short.atom"  # NOTE: Switch out when done testing

PICKLE_DIR = "/tmp/pollenprophet"

REFRESH_PERIOD = 3600  # between fetching articles, in seconds


@dataclass
class Original:  # BadJoke: Sting
    title: str
    summary: str
    link: str
    date: datetime
    image_link: str | None = None
    id: str = field(init=False)

    def _extract_img(self, s: str) -> tuple[str, str]:  # [img_link, rest of string]
        img: str
        m = re.match(r'<img src="(?P<img>.+?)"', s)
        try:
            img = m.group("img")
        except (IndexError, NameError):
            return ("", s)

        if img:
            rest = re.sub(r"<img src=.+?>", "", s)
            return (img, rest)

    def __post_init__(self):
        self.id = hashlib.sha256(self.link.encode()).hexdigest()

        extracted = self._extract_img(self.summary)
        if extracted[0]:
            self.image_link = extracted[0]
            self.summary = extracted[1]


@dataclass
class Improvement:  # GoodJoke: Queen
    original: Original
    title: str
    summary: str
    id: str = str(uuid4())


def grab_latest_originals() -> list[Original]:
    # TODO: Implement skipping any we already have
    feed: feedparser.FeedParserDict = feedparser.parse(BEE_FEED)  # noqa: F841
    results: list[Original] = []
    for entry in feed.entries:
        o = Original(
            title=entry.title,
            summary=entry.summary,
            link=entry.link,
            date=datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z"),
        )
        results.append(o)
    return results


def save_new_improvements(improvements: list[Improvement]) -> None:
    save_dir = Path(PICKLE_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)
    for imp in improvements:
        fname = save_dir / f"{int(imp.original.date.timestamp())}_{imp.id}"
        try:
            with open(fname, "wb") as f:
                pickle.dump(imp, f)
                print(f"Saved {fname}")
        except Exception as e:
            print(f"Error saving file {fname}: {e}")


def load_existing_improvements() -> list[Improvement]:
    improvements: list[Improvement] = []
    for fname in Path(PICKLE_DIR).iterdir():
        if not fname.is_file():
            continue

        try:
            with open(fname, "rb") as f:
                obj: Improvement = pickle.load(f)
                improvements.append(obj)
        except FileNotFoundError as e:
            print(f"Error loading file {fname}: {e}")
    return improvements


def keep_only_new_originals(
    additional: list[Original], existing: list[Original] | None = None
):
    if not existing:
        existing = [e.original for e in load_existing_improvements()]

    existing_hashes = set([e.id for e in existing])

    remaining: list[Original] = []
    for new in additional:
        if new.id not in existing_hashes:
            remaining.append(new)

    return remaining


def improve_originals(originals: list[Original]) -> list[Improvement]:
    improvements: list[Improvement] = []
    for orig in originals:
        new_title = rewrite_title_with_groq(orig.title)
        new_summary = rewrite_summary_with_groq(orig, new_title)

        improvements.append(
            Improvement(original=orig, title=new_title, summary=new_summary)
        )
    return improvements


def rewrite_title_with_groq(original_content: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY", "NO_API_KEY_FOUND"))

    suggestions = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a comedy writer at a satirical newspaper. Improve on the following satirical headline. Your new headline is funny, can involve current political events and has an edge to it. Print only the suggestions, with one suggestion on each line.",
            },
            {
                "role": "user",
                "content": original_content,
            },
        ],
        model="llama-3.3-70b-versatile",
    )
    suggestions_str = suggestions.choices[0].message.content
    if not suggestions_str:
        raise ValueError
    print("Suggestions: ", suggestions_str)
    winner = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an editor at a satirical newspaper. Improve on the following satirical headline. For a given headline, you diligently evaluate: (1) Whether the headline is funny; (2) Whether the headline follows a clear satirical goal; (3) Whether the headline has sufficient substance and bite. Based on the outcomes of your review, you pick your favorite headline from the given suggestions and you make targeted revisions to it. Your output consists solely of the revised headline.",
            },
            {
                "role": "user",
                "content": suggestions_str,
            },
        ],
        model="llama-3.3-70b-versatile",
    )
    print("Winner: ", winner.choices[0].message.content)
    winner_str = winner.choices[0].message.content
    if not winner_str:
        raise ValueError
    return winner_str.strip(" \"'")


def rewrite_summary_with_groq(orig: Original, improved_title: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY", "NO_API_KEY_FOUND"))

    summary = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Below there is an original title and an original summary. Then follows an improved title. Write an improved summary based on the original summary which fits to the improved title. Only output the improved summary.\n\nTitle:{orig.title}\nSummary:{orig.summary}\n---\nTitle:{improved_title}\nSummary:",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    summary_str = summary.choices[0].message.content
    if not summary_str:
        raise ValueError
    print("Improved summary", summary_str)
    return summary_str.strip(" \"'")


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/improve-title")
def improve_headline(content: str):
    return rewrite_title_with_groq(content)


@app.get("/improve-summary")
def improve_summary(original_title: str, new_title: str, original_summary: str):
    o = Original(
        title=original_title, summary=original_summary, link="", date=datetime.now()
    )
    return rewrite_summary_with_groq(o, new_title)


@app.on_event("startup")
@repeat_every(seconds=REFRESH_PERIOD)
def refresh_articles():
    adding = keep_only_new_originals(grab_latest_originals())
    improved = improve_originals(adding)
    save_new_improvements(improved)
    print(f"Updated articles. Added {len(improved)} new ones.")


@app.get("/update")
async def fetch_update():
    await refresh_articles()
    return json.dumps(improved)


@app.get("/improvements", response_class=HTMLResponse)
def list_improvements():
    improved = load_existing_improvements()
    return (
        """<button hx-get="/originals" hx-target="#content">Originals</button> """
        + "\n".join(
            f"""<div class="card">
<div class="card-img"><img src="https://placehold.co/300x200"></div>
<div class="card-title">{item.title}</div>
<div class="card-summary">{item.summary}</div>
</div>"""
            for item in sorted(improved, key=lambda i: i.original.date, reverse=True)
        )
    )


@app.get("/originals", response_class=HTMLResponse)
def list_originals():
    improved = load_existing_improvements()
    return (
        """<button hx-get="/improvements" hx-target="#content">Improvements</button> """
        + "\n".join(
            f"""
<div class="card">
    <div class="card-img"><img src="https://placehold.co/300x200"></div>
    <div class="card-title">{item.original.title}</div>
    <div class="card-summary">{item.original.summary}</div>
</div>"""
            for item in sorted(improved, key=lambda i: i.original.date, reverse=True)
        )
    )


style = """
.card {
  border: 1px solid #ccc;
  padding: 10px;
  margin: auto;
  margin-bottom: 40px;
  width: 600px;
}

.card-title {
  font-size: 24px;
  margin-bottom: 5px;
}
"""


@app.get("/", response_class=HTMLResponse)
def root_route():
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>The Pollen Prophet</title>
    <script src="https://unpkg.com/htmx.org@1.6.1"></script>
    <style>
        {style}
    </style>
</head>
<body>
    <h1>The Pollen Prophet</h1>
    <h2>Making funny since 2025 what ought not bee.</h2>
    <div hx-get="/improvements" hx-target="#content" hx-trigger="load" id="content"></div>
</body>
</html>
        """


def start() -> None:
    from uvicorn import run

    run("prophet.app:app", reload=True)


if __name__ == "__main__":
    # start()

    adding = keep_only_new_originals(grab_latest_originals())
    improved = improve_originals(adding)
    save_new_improvements(improved)

    improved = load_existing_improvements()
    for imp in improved:
        print(f"Old Title: {imp.original.title}")
        print(f"Old Summary: {imp.original.summary}")
        print("\n")
        print(f"Title: {imp.title}")
        print(f"Summary: {imp.summary}")

        print("-" * 50)
