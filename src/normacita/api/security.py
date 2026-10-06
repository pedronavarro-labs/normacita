"""Medidas de seguridad básicas de la capa HTTP.

- Cabeceras de seguridad (CSP estricta, nosniff, anti-clickjacking…).
- Límite de peticiones por IP en memoria (protege del abuso y del gasto en IA).
  Es suficiente para una sola instancia; con varias réplicas habría que usar
  Redis u otro almacén compartido (ver ROADMAP).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response: Response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        return response


class RateLimiter:
    """Ventana deslizante de 60 s por clave (IP)."""

    def __init__(self, limit_per_minute: int, clock=time.monotonic) -> None:  # type: ignore[no-untyped-def]
        self.limit = limit_per_minute
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        if self.limit <= 0:  # 0 o negativo = desactivado
            return True
        now = self._clock()
        q = self._hits[key]
        while q and now - q[0] >= 60:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
