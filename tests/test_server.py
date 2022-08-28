from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.
from http.server import HTTPServer
import requests
from threading import Thread
import json
import pytest






def test_(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USE_CACHE","True")

    from api.index import handler
    from api.util import APIResponse
    def start_server(port: int=3003):
        HTTPServer(("",port),handler).handle_request()

    p = Thread(target=start_server)
    p.start()
    res = requests.get("http://localhost:3003/api?location=brandywine")

    assert res.status_code == 200
    print(res.content.decode('utf-8'))
    body = json.loads(res.content)

    parsed_body = APIResponse(**body)

    print(parsed_body)

    p.join()
