import hashlib
import json
import os
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from groq import Groq

BEE_FEED = "https://babylonbee.com/feed"
BEE_FEED_TEST = "test/resources/feed_short.atom"  # NOTE: Switch out when done testing

PICKLE_DIR = "/tmp/pollenprophet"


@dataclass
class Original:  # BadJoke: Sting
    title: str
    summary: str
    link: str
    date: datetime
    id: str = field(init=False)

    def __post_init__(self):
        self.id = hashlib.sha256(self.link.encode()).hexdigest()


@dataclass
class Improvement:  # GoodJoke: Queen
    original: Original
    title: str
    summary: str
    id: str = str(uuid4())


def grab_latest_originals() -> list[Original]:
    # TODO: Implement skipping any we already have
    feed: feedparser.FeedParserDict = feedparser.parse(BEE_FEED_TEST)  # noqa: F841
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
                "role": "user",
                "content": f"Improve on the following satirical headline. The headline should be funny, can involve current political events and should have an edge to it. Print only the suggestions, with one suggestion on each line.\nOriginal: '{original_content}'",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print("Suggestions: ", suggestions.choices[0].message.content)
    winner = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"From the following satirical headline suggestions, pick the strongest one and print it. Do not print anything else. The chosen suggestion should be the most edgy, able to trend on social media and funniest. The suggestions:\n\n{suggestions}",
            }
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


@app.get("/update")
def fetch_update():
    adding = keep_only_new_originals(grab_latest_originals())
    improved = improve_originals(adding)
    save_new_improvements(improved)
    return json.dumps(improved)

@app.get("/", response_class=HTMLResponse)
def root_route():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>FastAPI with HTMX</title>
    <script src="https://unpkg.com/htmx.org@1.6.1"></script>
</head>
<body>
    <h1>Welcome to FastAPI with HTMX</h1>
    <div id="content"></div>
    <button hx-get="/fetch-data" hx-target="#content">Fetch Data</button>
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
