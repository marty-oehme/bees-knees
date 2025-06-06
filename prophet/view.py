from fastapi.responses import HTMLResponse

from prophet import app
from prophet.domain.improvement_repo import IImprovementRepo
from prophet.infra.improvement_pickle_repo import ImprovementPickleRepo

repo: IImprovementRepo = ImprovementPickleRepo()

html_app = app.app


@html_app.get("/improvements", response_class=HTMLResponse)
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


@html_app.get("/originals", response_class=HTMLResponse)
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


@html_app.get("/", response_class=HTMLResponse)
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
