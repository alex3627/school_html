#!/usr/bin/env python

from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.status import HTTP_303_SEE_OTHER


class SessionData(BaseModel):
    username: str


TEMPLATES = Jinja2Templates(directory="templates")

app = FastAPI()


class PasswordError(Exception):
    pass


@app.post("/login")
def login(username: Annotated[str, Form()], password: Annotated[str, Form()], response: Response):
    if password is None or password == '':
        raise PasswordError("Invalid password")
    print(username, password)
    if check_password(username, password):
        # TODO: Session handling?
        return RedirectResponse(url=app.url_path_for("read_root"), status_code=HTTP_303_SEE_OTHER)
    else:
        raise HTTPException(status_code=405, detail="Not allowed")


def check_password(username: str, password: str):
    # TODDO: Better implementation!
    return username == 'admin' and password == 'welcome'


@app.get("/")
def read_root(request: Request):
    return TEMPLATES.TemplateResponse('index.html', {'request': request, 'name': 'dummy'})


app.mount("/static", StaticFiles(directory="static"), name="static")
