#!/usr/bin/env bash
#
# deploy.sh — wire one example app into the Disent container.
#
# Handles the two shapes the examples come in:
#
#   proxy   — the app is a running process (nodejs, nextjs, django, fastapi…).
#             Creates a systemd unit to keep it alive + an nginx reverse proxy.
#
#   static  — the app is just files on disk (html_css_js, built vite/react).
#             Creates an nginx `root` block only. No process, no systemd unit.
#
# Usage:
#   ./deploy.sh --name nodejs --mode proxy --port 8978 \
#               --dir /root/projects/apps/nodejs \
#               --exec "/root/.nvm/versions/node/v22.22.2/bin/node server.js"
#
#   ./deploy.sh --name html-css-js --mode static \
#               --dir /root/projects/apps/html-css-js
#
#   Add --dry-run to print what would happen without touching anything.
#
set -euo pipefail

# --- configuration ----------------------------------------------------------
# Subdomain convention — VERIFIED LIVE 2026-08-10:
#   https://{PROJECT}-{PORT}.{DOMAIN}   ->   container:{PORT}
# Routing is BY PORT. The app NAME never appears in the hostname. Confirmed by
# testing my-container-8978.example.com: DNS resolves and the platform
# reaches the container directly on 8978 (it returned 502 only because the app
# was bound to 127.0.0.1 — see the bind check in the verify step below).
# The old `{project}-{name}.fastcontainers.net` scheme is RETIRED — that domain
# no longer resolves at all.
PROJECT="${PROJECT:-my-container}"
DOMAIN="${DOMAIN:-example.com}"

NAME=""; MODE=""; PORT=""; DIR=""; EXEC=""; DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)    NAME="$2"; shift 2 ;;
    --mode)    MODE="$2"; shift 2 ;;
    --port)    PORT="$2"; shift 2 ;;
    --dir)     DIR="$2";  shift 2 ;;
    --exec)    EXEC="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

# --- validation -------------------------------------------------------------
[[ -z "$NAME" ]] && { echo "ERROR: --name is required" >&2; exit 2; }
[[ -z "$DIR"  ]] && { echo "ERROR: --dir is required" >&2; exit 2; }

case "$MODE" in
  proxy)
    [[ -z "$PORT" ]] && { echo "ERROR: --port is required for proxy mode" >&2; exit 2; }
    [[ -z "$EXEC" ]] && { echo "ERROR: --exec is required for proxy mode" >&2; exit 2; }
    ;;
  static)
    [[ ! -f "$DIR/index.html" ]] && \
      echo "WARNING: no index.html in $DIR — static mode expects one" >&2
    ;;
  *) echo "ERROR: --mode must be 'proxy' or 'static'" >&2; exit 2 ;;
esac

[[ ! -d "$DIR" ]] && { echo "ERROR: directory not found: $DIR" >&2; exit 2; }

# Port-based, NOT name-based. Static apps have no port of their own — nginx
# serves them on :80, so they advertise {PROJECT}-80.{DOMAIN}.
HOSTNAME_FQDN="${PROJECT}-${PORT:-80}.${DOMAIN}"
NGINX_CONF="/etc/nginx/sites-available/${NAME}.conf"
UNIT="/etc/systemd/system/example-${NAME}.service"

echo "=============================================="
echo " app:    ${NAME}"
echo " mode:   ${MODE}"
echo " dir:    ${DIR}"
[[ "$MODE" == "proxy" ]] && echo " port:   ${PORT}"
[[ "$MODE" == "proxy" ]] && echo " exec:   ${EXEC}"
echo " host:   ${HOSTNAME_FQDN}"
echo "=============================================="

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    eval "$@"
  fi
}

write_file() {
  local path="$1" content="$2"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] would write ${path}:"
    echo "-----"; echo "$content"; echo "-----"
  else
    printf '%s\n' "$content" > "$path"
    echo "wrote ${path}"
  fi
}

# --- port collision check (proxy mode) --------------------------------------
if [[ "$MODE" == "proxy" ]]; then
  if ss -tlnH "sport = :${PORT}" 2>/dev/null | grep -q .; then
    echo "WARNING: port ${PORT} is already in use:"
    ss -tlnp "sport = :${PORT}" 2>/dev/null | tail -n +2
    echo "  (if this is a previous version of ${NAME}, that's expected)"
  fi
fi

# --- systemd unit (proxy mode only) -----------------------------------------
if [[ "$MODE" == "proxy" ]]; then
  read -r -d '' UNIT_CONTENT <<EOF || true
# Managed by deploy.sh — regenerated on each deploy.
[Unit]
Description=Disent container example app: ${NAME}
After=network.target

[Service]
Type=simple
WorkingDirectory=${DIR}
ExecStart=${EXEC}
Environment=PORT=${PORT}
# REQUIRED: the platform connects to container:${PORT} directly, so a
# 127.0.0.1-only listener is unreachable and returns 502 at the edge. Apps
# should default to 0.0.0.0 anyway; this makes it true regardless.
Environment=HOST=0.0.0.0
Environment=HOSTNAME=0.0.0.0
Environment=NODE_ENV=production
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=example-${NAME}

[Install]
WantedBy=multi-user.target
EOF
  write_file "$UNIT" "$UNIT_CONTENT"
  run "systemctl daemon-reload"
  run "systemctl enable example-${NAME}.service"
  # MUST be an explicit restart, not `enable --now`.
  # `--now` only STARTS a stopped service. For a service that is already
  # running it is a no-op, so a redeploy would rewrite the unit file and then
  # leave the OLD process running with the OLD code and OLD environment — a
  # deploy that silently deploys nothing. (This is exactly how the HOST=0.0.0.0
  # fix appeared to apply but didn't, on 2026-08-10.)
  run "systemctl restart example-${NAME}.service"
fi

# --- nginx config -----------------------------------------------------------
if [[ "$MODE" == "proxy" ]]; then
  read -r -d '' NGINX_CONTENT <<EOF || true
# Managed by deploy.sh — regenerated on each deploy.
server {
    listen 80;
    listen [::]:80;
    server_name ${HOSTNAME_FQDN};

    location / {
        proxy_pass         http://127.0.0.1:${PORT};
        proxy_http_version 1.1;

        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket upgrade — needed by Next.js/Vite hot reload; harmless else.
        proxy_set_header Upgrade    \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
else
  # Static apps still need their OWN port: routing is by port, so every static
  # app would otherwise collide on :80 (they'd all advertise {project}-80).
  # nginx listens directly on the app's port and serves the files — no process,
  # no systemd unit. Pass --port for a static app to get its own subdomain.
  # Without --port it falls back to :80 (the homepage/default slot).
  read -r -d '' NGINX_CONTENT <<EOF || true
# Managed by deploy.sh — regenerated on each deploy.
# Static app: no process to proxy to. nginx serves files off disk on :${PORT:-80}.
server {
    listen ${PORT:-80};
    listen [::]:${PORT:-80};
    server_name ${HOSTNAME_FQDN};

    root ${DIR};
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~* \.(css|js)\$ {
        expires 1h;
        add_header Cache-Control "public";
    }

    location = /index.html {
        add_header Cache-Control "no-cache";
    }
}
EOF
fi

write_file "$NGINX_CONF" "$NGINX_CONTENT"
run "ln -sf ${NGINX_CONF} /etc/nginx/sites-enabled/${NAME}.conf"

# --- validate BEFORE reloading (never reload a broken config) ---------------
if [[ $DRY_RUN -eq 0 ]]; then
  if ! nginx -t; then
    echo "ERROR: nginx config test FAILED — not reloading." >&2
    echo "       Removing the symlink so the next reload stays clean." >&2
    rm -f "/etc/nginx/sites-enabled/${NAME}.conf"
    exit 1
  fi
  systemctl reload nginx
  echo "nginx reloaded"
else
  echo "[dry-run] would run: nginx -t && systemctl reload nginx"
fi

# --- verify -----------------------------------------------------------------
if [[ $DRY_RUN -eq 0 ]]; then
  echo
  echo "--- verifying ---"
  # Poll for the listener instead of a fixed sleep. A uv-managed CPython can
  # take 4-5s to boot, and a flat `sleep 2` reported "nothing listening" for a
  # service that was starting perfectly normally (observed 2026-08-10) — a
  # false alarm that looks identical to a real failure.
  if [[ -n "$PORT" ]]; then
    for _ in $(seq 1 25); do
      ss -tlnH "sport = :${PORT}" 2>/dev/null | grep -q . && break
      sleep 1
    done
  else
    sleep 2
  fi

  # 1. BIND CHECK (proxy mode) — the #1 cause of a 502 at the edge. The platform
  #    connects to container:${PORT} directly, so the listener MUST be on
  #    0.0.0.0 (or ::). A 127.0.0.1-only listener passes every local test and
  #    still fails in the browser.
  if [[ -n "$PORT" ]]; then
    BIND=$(ss -tlnH "sport = :${PORT}" 2>/dev/null | awk '{print $4}' | head -1)
    echo "bind on :${PORT}  ->  ${BIND:-<nothing listening>}"
    case "$BIND" in
      0.0.0.0:*|\[::\]:*|*:::*)
        echo "OK: listening on all interfaces — reachable from the edge." ;;
      127.0.0.1:*|\[::1\]:*)
        echo "FAIL: bound to LOOPBACK ONLY. https://${HOSTNAME_FQDN}/ will 502." >&2
        echo "      Fix the app to bind 0.0.0.0 (it should read \$HOST/\$PORT)." >&2 ;;
      "") echo "FAIL: nothing is listening on :${PORT}." >&2
          echo "      journalctl -u example-${NAME} -n 30 --no-pager" >&2 ;;
      *)  echo "WARNING: unrecognised bind address — check manually." >&2 ;;
    esac
    echo
  fi

  # 2. HTTP check. If the app has its own port, hit that port directly — that
  #    is exactly what the platform edge does. Otherwise go through nginx:80
  #    with the Host header (the :80 / homepage slot).
  if [[ -n "$PORT" ]]; then
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/" 2>/dev/null)
    [[ -z "$CODE" ]] && CODE="000"
    echo "GET http://127.0.0.1:${PORT}/ (direct — same path as the edge)  ->  HTTP ${CODE}"
  else
    CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: ${HOSTNAME_FQDN}" http://127.0.0.1/ 2>/dev/null)
    [[ -z "$CODE" ]] && CODE="000"
    echo "GET http://${HOSTNAME_FQDN}/ (via nginx:80)  ->  HTTP ${CODE}"
  fi
  if [[ "$CODE" == "200" ]]; then
    echo "OK: ${NAME} is being served."
  else
    echo "NOT 200. Check:"
    [[ "$MODE" == "proxy" ]] && echo "  journalctl -u example-${NAME} -n 30 --no-pager"
    echo "  tail -20 /var/log/nginx/error.log"
  fi
  echo
  echo "Edge URL (the real test — open it in a browser):"
  echo "  https://${HOSTNAME_FQDN}/"
fi

echo
echo "done: ${NAME}"
