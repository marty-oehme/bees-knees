# pyright: reportUnusedFunction=false

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from prophet.domain.improvement_repo import IImprovementRepo
from prophet.infra.improvement_pickle_repo import ImprovementPickleRepo
from prophet.infra.improvement_supa_repo import ImprovementSupaRepo

repo: IImprovementRepo = ImprovementSupaRepo()

templates = Jinja2Templates(directory="templates")


def define_routes(app: FastAPI):
    @app.get("/improvements", response_class=HTMLResponse)
    def list_improvements(request: Request):
        improved = repo.get_all()
        return templates.TemplateResponse(
            request=request,
            name="list_improvements.html",
            context={"articles": improved},
        )

    @app.get("/originals", response_class=HTMLResponse)
    def list_originals(request: Request):
        improved = repo.get_all()
        return templates.TemplateResponse(
            request=request, name="list_originals.html", context={"articles": improved}
        )

    @app.get("/", response_class=HTMLResponse)
    def root_route(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")
