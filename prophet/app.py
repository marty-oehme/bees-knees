import json
from datetime import datetime

import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi_utils.tasks import repeat_every

from prophet.domain.improvement import Improvement
from prophet.domain.improvement_repo import IImprovementRepo
from prophet.domain.original import Original
from prophet.infra.improvement_pickle_repo import ImprovementPickleRepo
from prophet.llm import LLMClient

BEE_FEED = "https://babylonbee.com/feed"
BEE_FEED_TEST = "test/resources/feed_short.atom"  # NOTE: Switch out when done testing

REFRESH_PERIOD = 3600  # between fetching articles, in seconds

llm: LLMClient = LLMClient()
repo: IImprovementRepo = ImprovementPickleRepo()


def grab_latest_originals() -> list[Original]:
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


def keep_only_new_originals(
    additional: list[Original], existing: list[Original] | None = None
):
    if not existing:
        existing = [e.original for e in repo.get_all()]

    existing_hashes = set([e.id for e in existing])

    remaining: list[Original] = []
    for new in additional:
        if new.id not in existing_hashes:
            remaining.append(new)

    return remaining


def improve_originals(originals: list[Original]) -> list[Improvement]:
    improvements: list[Improvement] = []
    for orig in originals:
        new_title = llm.rewrite_title(orig.title)
        new_summary = llm.rewrite_summary(orig, new_title)

        improvements.append(
            Improvement(original=orig, title=new_title, summary=new_summary)
        )
    return improvements


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
    return llm.rewrite_title(content)


@app.get("/improve-summary")
def improve_summary(original_title: str, new_title: str, original_summary: str):
    o = Original(
        title=original_title, summary=original_summary, link="", date=datetime.now()
    )
    return llm.rewrite_summary(o, new_title)


@app.on_event("startup")
@repeat_every(seconds=REFRESH_PERIOD)
def refresh_articles():
    adding = keep_only_new_originals(grab_latest_originals())
    improved = improve_originals(adding)
    repo.add_all(improved)
    print(f"Updated articles. Added {len(improved)} new ones.")


@app.get("/update")
async def fetch_update():
    await refresh_articles()
    return json.dumps(improved)


## HTML (& hyperdata) responses
@app.get("/improvements", response_class=HTMLResponse)
def list_improvements():
    improved = repo.get_all()
    return (
        """<button hx-get="/originals" hx-target="#content">Originals</button> """
        + "\n".join(
            f"""
<div class="card">
    <div class="card-img">
        <img src="{item.original.image_link if item.original.image_link else "https://placehold.co/300x200"}" width="600">
    </div>
<div class="card-title">{item.title}</div>
<div class="card-summary">{item.summary}</div>
</div>"""
            for item in sorted(improved, key=lambda i: i.original.date, reverse=True)
        )
    )


@app.get("/originals", response_class=HTMLResponse)
def list_originals():
    improved = repo.get_all()
    return (
        """<button hx-get="/improvements" hx-target="#content">Improvements</button> """
        + "\n".join(
            f"""
<div class="card">
    <div class="card-img">
        <img src="{item.original.image_link if item.original.image_link else "https://placehold.co/300x200"}" width="600">
    </div>
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

    # adding = keep_only_new_originals(grab_latest_originals())
    # improved = improve_originals(adding)
    # save_new_improvements(improved)

    # migrate to newer version
    improved = repo.get_all()
    for imp in improved:
        imp.original.__post_init__()
        print(f"Old Title: {imp.original.title}")
        print(f"Old Summary: {imp.original.summary}")
        print(f"Old picture: {imp.original.image_link}")
        print("\n")
        print(f"Title: {imp.title}")
        print(f"Summary: {imp.summary}")

        print("-" * 50)
    repo.add_all(improved)
