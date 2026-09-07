# django_react fullstack example — ONE port, no CORS.
#
# Same pattern as fastapi_react, Django flavour: Django serves a JSON API under
# /api/*, AND serves the compiled React app (frontend/dist). Same origin/port,
# so the browser makes plain same-origin fetches — no CORS, one subdomain. This
# is the cleanest shape for the platform's port-based routing (CLAUDE.md §2).
#
# Binds TCP 8004 on 0.0.0.0 via runserver (§8). ALLOWED_HOSTS=['*'] lets the
# .example.com edge host through. my-container-8004.example.com -> :8004.
# NOTE: :8004 is a PROPOSED port (fullstack) — confirm with Anthony.
#
# Build the frontend first (`cd ../frontend && npm install && npm run build`).

import os
import platform
import sys
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse, Http404
from django.urls import path, re_path
from django.views.static import serve

APP_NAME = "django_react"
PORT = int(os.environ.get("PORT", 8004))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

DIST = (Path(__file__).parent.parent / "frontend" / "dist").resolve()

settings.configure(
    DEBUG=True,
    SECRET_KEY="dev-only-not-a-secret",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],  # accept the .example.com edge host (§8 equivalent)
    MIDDLEWARE=[],
)


def api_hello(request):
    return JsonResponse(
        {
            "message": "hello from the Django backend",
            "python": platform.python_version(),
            "served_by": platform.node(),
        }
    )


def api_health(request):
    return JsonResponse({"app": APP_NAME, "status": "ok"})


def index(request):
    # Serve the built SPA entry point. Read at request time so a rebuild is
    # picked up without restarting.
    idx = DIST / "index.html"
    if not idx.is_file():
        return HttpResponse(
            "<h1>frontend not built yet</h1><p>Run "
            "<code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>, "
            "then restart.</p>",
            content_type="text/html",
        )
    return HttpResponse(idx.read_text(), content_type="text/html")


def assets(request, path):
    # Serve Vite's hashed JS/CSS out of frontend/dist/assets.
    try:
        return serve(request, path, document_root=str(DIST / "assets"))
    except Http404:
        raise


urlpatterns = [
    path("api/hello", api_hello),
    path("api/health", api_health),
    re_path(r"^assets/(?P<path>.*)$", assets),
    path("", index),
]


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0], "runserver", "--noreload", f"{HOST}:{PORT}"])
