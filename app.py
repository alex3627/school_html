#!/usr/bin/env python

import os
import secrets
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.frontends.implementations import (CookieParameters,
                                                        SessionCookie)
from fastapi_sessions.session_verifier import SessionVerifier
from pydantic import BaseModel
from starlette.status import HTTP_303_SEE_OTHER


class SessionData(BaseModel):
    username: str


COOKIE_NAME = 'LOGON_COOKIE'

cookie_params = CookieParameters()


def get_secret_key():
    secrets_file = Path(os.environ.get('TMP') or '/tmp') / 'secure_key.bin'
    if secrets_file.exists():
        with open(secrets_file, 'br') as fobj:
            return fobj.read()
    else:
        b = secrets.token_bytes(32)
        with open(secrets_file, 'bw') as fobj:
            fobj.write(b)
        return b


cookie = SessionCookie(
    cookie_name=COOKIE_NAME,
    identifier="general_verifier",
    auto_error=True,
    secret_key=get_secret_key(),
    cookie_params=cookie_params,
)

backend = InMemoryBackend[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(
        status_code=403, detail="invalid session"),
)

TEMPLATES = Jinja2Templates(directory="templates")

app = FastAPI()


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


class PasswordError(Exception):
    pass


@app.post("/login")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    if password is None or password == '':
        raise PasswordError("Invalid password")
    if check_password(username, password):
        session = uuid4()
        data = SessionData(username=username)
        await backend.create(session, data)
        response = RedirectResponse(url=app.url_path_for(
            "read_root"), status_code=HTTP_303_SEE_OTHER)
        cookie.attach_to_response(response, session)
        return response
    else:
        raise HTTPException(status_code=405, detail="Not allowed")


def check_password(username: str, password: str):
    # TODDO: Better implementation!
    return password == 'welcome'


@app.get("/")
async def read_root(request: Request):
    session_cookie_str = request.cookies.get(COOKIE_NAME)
    if session_cookie_str == None:
        session_data = SessionData(username='dummy')
    else:
        cookie_data = cookie(request)
        session_data = await backend.read(cookie_data)
        if session_data is None:
            session_data = SessionData(username='dummy')
    return TEMPLATES.TemplateResponse('index.html', {'request': request, 'data': session_data})


app.mount("/static", StaticFiles(directory="static"), name="static")
