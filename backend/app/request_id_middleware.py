from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
import uuid

class RequestIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            scope.setdefault("state", {})
            scope["state"]["request_id"] = str(uuid.uuid4())
        await self.app(scope, receive, send)
