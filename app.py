#!/usr/bin/env python
#
# pip install fastapi uvicorn python-multipart
#
# To start:
# uvicorn app:app --reload
#

from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()


class PasswordError(Exception):
    pass


@app.post("/login")
def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    if password is None or password == '':
        raise PasswordError("Invalid password")
    # TODO: Some useful stuff
    return {'You': f"are logged in: {username}"}


@app.get("/")
def read_root():
    with open('index.html', encoding='UTF-8') as file_obj:
        return HTMLResponse(file_obj.read())


app.mount("/static", StaticFiles(directory="static"), name="static")
