from http.server import HTTPServer
from api.index import handler

HTTPServer(("",3000),handler).serve_forever()