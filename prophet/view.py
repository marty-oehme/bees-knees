# pyright: reportUnusedFunction=false

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from prophet.domain.improvement_repo import IImprovementRepo
from prophet.infra.improvement_pickle_repo import ImprovementPickleRepo

repo: IImprovementRepo = ImprovementPickleRepo()

templates = Jinja2Templates(directory="templates")


def define_routes(app: FastAPI):
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
                for item in sorted(
                    improved, key=lambda i: i.original.date, reverse=True
                )
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
                for item in sorted(
                    improved, key=lambda i: i.original.date, reverse=True
                )
            )
        )

    @app.get("/", response_class=HTMLResponse)
    def root_route(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")
