from http.server import HTTPServer
import requests
from threading import Thread
import json
import pytest

from api.index import handler
from api.util import APIResponse





def test_server(monkeypatch: pytest.MonkeyPatch):
    """
    Launches the server in another thread, sends a request to it, 
    and checks that the response fits to the right schema. This uses
    the live campusdish API.

    """
    def start_server(port: int=3003):
        HTTPServer(("",port),handler).handle_request()

    for location in ("anteatery", "brandywine"):
        """
        The server crashes if you run both requests sequentially on the same thread without closing it
        and making a new one first. No idea why. If you have the energy, go ahead and fix it. It isn't a problem
        since we're running serverless, so the instance of the server only gets one request across its lifespan anyways.
        """
        p = Thread(target=start_server)
        p.start()
        try:
                res = requests.get(f"http://localhost:3003/api?location={location}")

                assert res.status_code == 200
                print(res.content.decode('utf-8'))
                body = json.loads(res.content)

                parsed_body = APIResponse(**body)

                print(parsed_body)
        finally:
            p.join()
