# django environment example — a minimal, single-file Django backend.
# Django is normally a multi-file project (manage.py, settings.py, urls.py...);
# this collapses the essentials into one file so the tile stays as small and
# self-contained as the other examples. It still runs on Django's real machinery.
#
# Binds TCP 3005 on 0.0.0.0 via `runserver 0.0.0.0:3005`. The platform routes the
# public subdomain by PORT (my-container-3005.example.com -> container:3005),
# so it MUST bind 0.0.0.0, and ALLOWED_HOSTS must permit the .example.com host —
# the Django equivalent of Vite's allowedHosts. See CLAUDE.md §2/§8.
#
# NOTE: :3005 is a PROPOSED port (backend 8000s block) — confirm with Anthony.

import os
import platform
import sys

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import path

APP_NAME = "django"
PORT = int(os.environ.get("PORT", 3005))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

settings.configure(
    DEBUG=True,
    SECRET_KEY="dev-only-not-a-secret",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],  # accept the .example.com edge host (§8 equivalent)
    MIDDLEWARE=[],
)


def page() -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{APP_NAME} — hello world</title>
  <style>
    body {{ font: 16px/1.5 system-ui, sans-serif; margin: 0;
           display: grid; place-items: center; min-height: 100vh;
           background: #0f1117; color: #e6e8ee; }}
    .card {{ text-align: center; padding: 2rem 2.5rem; border: 1px solid #262b38;
            border-radius: 12px; background: #161a23; }}
    h1 {{ margin: 0 0 .25rem; font-size: 1.4rem; }}
    code {{ background: #0f1117; padding: .1rem .4rem; border-radius: 4px;
           color: #7dd3fc; }}
    .meta {{ color: #8a93a6; font-size: .85rem; margin-top: 1rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>👋 hello from <code>{APP_NAME}</code></h1>
    <div>Python · Django · no database</div>
    <div class="meta">
      served by {platform.node()} · python {platform.python_version()}<br>
      listening on {HOST}:{PORT} ·
      <a href="/health" style="color:#7dd3fc">/health</a>
    </div>
  </div>
</body>
</html>"""


def root(request):
    return HttpResponse(page())


def health(request):
    return JsonResponse({"app": APP_NAME, "status": "ok", "python": platform.python_version()})


urlpatterns = [
    path("", root),
    path("health", health),
]


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    # --noreload keeps this to a single process (cleaner for the tile).
    execute_from_command_line([sys.argv[0], "runserver", "--noreload", f"{HOST}:{PORT}"])
