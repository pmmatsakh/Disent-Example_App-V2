#!/usr/bin/env bash
#
# deploy-all.sh — install + deploy the staged example apps on the container.
#
# Runs ON THE BOX. Copies each app from the uploaded bundle into /srv/apps/,
# installs its dependencies, then hands off to deploy.sh (which writes the
# systemd unit + nginx conf, restarts, and verifies the bind).
#
# Usage:
#   ./deploy-all.sh                # deploy every app in the table
#   ./deploy-all.sh fastapi flask  # deploy only the named apps
#   DRY=1 ./deploy-all.sh fastapi  # pass --dry-run through to deploy.sh
#
set -uo pipefail

DEPLOY=/root/projects/deploy/deploy.sh
SRC="$(cd "$(dirname "$0")" && pwd)/apps"
DEST=/srv/apps
DRYFLAG=""; [[ "${DRY:-0}" == "1" ]] && DRYFLAG="--dry-run"

# uv manages the Python environments. The container has no pip and no working
# ensurepip, so stdlib `python3 -m venv` cannot build a usable env — uv ships
# its own installer and does not need either.
# It installs to ~/.local/bin, which a non-interactive SSH shell usually does
# NOT have on PATH, so resolve it explicitly.
UV="$(command -v uv 2>/dev/null || true)"
[[ -z "$UV" && -x /root/.local/bin/uv ]] && UV=/root/.local/bin/uv
[[ -z "$UV" && -x "$HOME/.local/bin/uv" ]] && UV="$HOME/.local/bin/uv"
[[ -z "$UV" && -x /usr/local/bin/uv ]] && UV=/usr/local/bin/uv

# Non-interactive SSH/systemd does not load NVM. Pin both Node and npm so an
# install cannot silently use the container's EOL /usr/bin/node (v18).
NODE22=/root/.nvm/versions/node/v22.22.2/bin/node
NODE22_BIN=/root/.nvm/versions/node/v22.22.2/bin
NPM22_CLI=/root/.nvm/versions/node/v22.22.2/lib/node_modules/npm/bin/npm-cli.js
COREPACK22=/root/.nvm/versions/node/v22.22.2/lib/node_modules/corepack/dist/corepack.js

# name | port | mode | prep | subdir | exec-binary + args
#   prep: pyvenv (requirements.txt in that dir) | npm | make | none
APPS=(
  "fastapi|8000|proxy|pyvenv|.|.venv/bin/python main.py"
  "flask|8001|proxy|pyvenv|.|.venv/bin/python app.py"
  "django|3005|proxy|pyvenv|.|.venv/bin/python app.py"
  "expressjs|3006|proxy|npm|.|/root/.nvm/versions/node/v22.22.2/bin/node server.js"
  "nextjs|3000|proxy|npm-build|.|/root/.nvm/versions/node/v22.22.2/bin/node node_modules/next/dist/bin/next start -p 3000"
  "n8n|5678|proxy|npm|.|/bin/bash start.sh"
  "c-cpp|3007|proxy|make|.|SELFDIR/server"
  "fastapi-react|8002|proxy|pyvenv|backend|.venv/bin/python main.py"
  "fastapi-react-sqlite|8003|proxy|pyvenv|backend|.venv/bin/python main.py"
  "django-react|8004|proxy|pyvenv|backend|.venv/bin/python app.py"
  "tailwind|3003|static|none|.|"
  "typescript|3004|static|none|.|"
  "docs|8081|static|none|.|"
  "html-css-js|8080|static|none|.|"
  "langchain|3401|proxy|pyvenv|.|.venv/bin/python main.py"
  "python|3008|proxy|none|.|/usr/bin/python3 server.py"
  "go|3009|proxy|gobuild|.|SELFDIR/server"
  "sqlite|8005|proxy|pyvenv|.|.venv/bin/python main.py"
  "crewai|3404|proxy|pyvenv|.|.venv/bin/python main.py"
  "autogen|3405|proxy|pyvenv|.|.venv/bin/python main.py"
  "mcp-server|3406|proxy|pyvenv|.|.venv/bin/python main.py"
  "claude-agent-sdk|3407|proxy|pyvenv|.|.venv/bin/python main.py"
  "openai-agent-sdk|3408|proxy|pyvenv|.|.venv/bin/python main.py"
  "redis|8006|proxy|pyvenv|.|.venv/bin/python main.py"
  "postgres|8007|proxy|pyvenv|.|.venv/bin/python main.py"
  "mysql|8008|proxy|pyvenv|.|.venv/bin/python main.py"
  "claude-code|3402|proxy|pyvenv|.|.venv/bin/python main.py"
  "openai-codex|3403|proxy|pyvenv|.|.venv/bin/python main.py"
)

WANTED=("$@")
want() { [[ ${#WANTED[@]} -eq 0 ]] && return 0
         for w in "${WANTED[@]}"; do [[ "$w" == "$1" ]] && return 0; done; return 1; }

# --- PREFLIGHT --------------------------------------------------------------
# Check the toolchains the selected apps actually need, BEFORE copying anything
# into /srv/apps. Test capabilities by USING them, not by asking --help:
# `python3 -m venv --help` succeeds on a box where venv cannot create an env
# (missing ensurepip), which is exactly how this bit us on 2026-08-10.
NEED_PY=0; NEED_NPM=0; NEED_MAKE=0; NEED_GO=0
for row in "${APPS[@]}"; do
  IFS='|' read -r NAME _ _ PREP _ _ <<< "$row"
  want "$NAME" || continue
  case "$PREP" in pyvenv) NEED_PY=1 ;; npm|npm-build) NEED_NPM=1 ;; make) NEED_MAKE=1 ;; gobuild) NEED_GO=1 ;; esac
done

PREFLIGHT_FAIL=0
echo "--- preflight ---"
if [[ $NEED_PY -eq 1 ]]; then
  if [[ -z "$UV" ]]; then
    echo "  ✗ uv not found (looked on PATH, /root/.local/bin, /usr/local/bin)"
    echo "    FIX — install it (no apt, no system packages touched):"
    echo "      curl -LsSf https://astral.sh/uv/install.sh | sh"
    PREFLIGHT_FAIL=1
  else
    # Prove uv can actually BUILD an env and install into it — don't just
    # check that the binary answers --version. (Checking for existence rather
    # than capability is exactly what bit us with `python3 -m venv --help`.)
    rm -rf /tmp/_preflight_venv
    if "$UV" venv /tmp/_preflight_venv >/tmp/_preflight_err 2>&1 \
       && [[ -x /tmp/_preflight_venv/bin/python ]]; then
      echo "  ✓ uv $("$UV" --version 2>/dev/null | awk '{print $2}') at $UV — can create envs"
    else
      echo "  ✗ uv found at $UV but cannot create an env:"
      head -3 /tmp/_preflight_err 2>/dev/null | sed 's/^/      /'
      PREFLIGHT_FAIL=1
    fi
    rm -rf /tmp/_preflight_venv
  fi
fi
if [[ $NEED_NPM -eq 1 ]]; then
  if [[ -x "$NODE22" && -f "$NPM22_CLI" ]]; then
    echo "  ✓ Node $($NODE22 --version) + npm $($NODE22 "$NPM22_CLI" --version)"
  else
    echo "  ✗ pinned Node 22/npm missing at /root/.nvm/versions/node/v22.22.2"
    PREFLIGHT_FAIL=1
  fi
fi
if [[ $NEED_MAKE -eq 1 ]]; then
  make --version >/dev/null 2>&1 && command -v gcc >/dev/null \
    && echo "  ✓ make + gcc present" \
    || { echo "  ✗ make/gcc missing (apt install build-essential)"; PREFLIGHT_FAIL=1; }
fi
if [[ $NEED_GO -eq 1 ]]; then
  # Prove the toolchain can BUILD, not merely that `go` answers --version.
  if go version >/dev/null 2>&1; then
    echo "  ✓ $(go version)"
  else
    echo "  ✗ go not installed (apt-get install -y golang-go)"
    PREFLIGHT_FAIL=1
  fi
fi
if [[ $PREFLIGHT_FAIL -eq 1 ]]; then
  echo
  echo "PREFLIGHT FAILED — nothing was copied or changed. Fix the above first."
  exit 1
fi
echo "  preflight OK"

OK=(); FAILED=()

for row in "${APPS[@]}"; do
  IFS='|' read -r NAME PORT MODE PREP SUB EXECLINE <<< "$row"
  want "$NAME" || continue

  echo
  echo "############################################################"
  echo "# ${NAME}  (:${PORT}, ${MODE})"
  echo "############################################################"

  # 1. copy into place
  mkdir -p "${DEST}/${NAME}"
  cp -R "${SRC}/${NAME}/." "${DEST}/${NAME}/" || { FAILED+=("$NAME: copy"); continue; }
  WORKDIR="${DEST}/${NAME}"
  [[ "$SUB" != "." ]] && WORKDIR="${DEST}/${NAME}/${SUB}"

  # 2. dependencies
  case "$PREP" in
    pyvenv)
      echo "--- uv venv + deps ---"
      # Remove any half-built venv from a previous failed run so retries are
      # clean and idempotent.
      rm -rf "${WORKDIR}/.venv"
      # `uv venv` builds the env; `uv pip install --python <venv>/bin/python`
      # installs into it. The venv deliberately has no pip of its own — uv is
      # the installer — but .venv/bin/python is a real interpreter with the
      # packages on its path, which is all systemd's ExecStart needs.
      ( cd "$WORKDIR" \
        && "$UV" venv .venv \
        && "$UV" pip install --quiet --python "${WORKDIR}/.venv/bin/python" \
                 -r requirements.txt ) \
        || { FAILED+=("$NAME: uv pip"); continue; }
      echo "deps installed"
      ;;
    npm|npm-build)
      if [[ "$NAME" == "n8n" ]]; then
        echo "--- Node 22 pnpm clean install (lower-memory n8n path) ---"
        rm -rf "${WORKDIR}/node_modules"
        ( cd "$WORKDIR" \
          && PATH="${NODE22_BIN}:${PATH}" \
             NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=768}" \
             "$NODE22" "$COREPACK22" pnpm install \
               --prod --frozen-lockfile --reporter=append-only ) \
          || { FAILED+=("$NAME: pnpm"); continue; }
      else
        echo "--- Node 22 npm clean install ---"
        # npm lifecycle scripts and package binaries commonly use
        # `#!/usr/bin/env node`. Put Node 22 first in PATH as well as invoking
        # npm with Node 22, or `npm run build` silently falls back to
        # /usr/bin/node v18 in non-login SSH/systemd environments.
        ( cd "$WORKDIR" \
          && PATH="${NODE22_BIN}:${PATH}" \
             NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=768}" \
             npm_config_jobs="${npm_config_jobs:-1}" \
             npm_config_maxsockets="${npm_config_maxsockets:-2}" \
             npm_config_audit=false \
             npm_config_fund=false \
             "$NODE22" "$NPM22_CLI" ci --omit=dev --silent ) \
          || { FAILED+=("$NAME: npm"); continue; }
      fi
      echo "deps installed"
      if [[ "$PREP" == "npm-build" ]]; then
        echo "--- production build ---"
        ( cd "$WORKDIR" \
          && PATH="${NODE22_BIN}:${PATH}" \
             "$NODE22" "$NPM22_CLI" run build ) \
          || { FAILED+=("$NAME: npm build"); continue; }
      fi
      ;;
    gobuild)
      echo "--- go build ---"
      # Compile ON the container: a macOS binary will not run on Linux.
      # GOCACHE/GOPATH are explicit because systemd/ssh may have no HOME.
      ( cd "$WORKDIR" \
        && GOCACHE="${WORKDIR}/.gocache" GOPATH="${WORKDIR}/.gopath" GOFLAGS=-mod=mod \
           go build -o server main.go ) \
        || { FAILED+=("$NAME: go build"); continue; }
      [[ -x "${WORKDIR}/server" ]] \
        || { echo "go build reported success but ${WORKDIR}/server is missing" >&2
             FAILED+=("$NAME: go build produced no binary"); continue; }
      echo "built $(stat -c%s "${WORKDIR}/server" 2>/dev/null || echo '?') bytes"
      ;;
    make)
      echo "--- compiling ---"
      ( cd "$WORKDIR" && make clean >/dev/null 2>&1; cd "$WORKDIR" && make ) \
        || { FAILED+=("$NAME: make"); continue; }
      ;;
    none) : ;;
    *)
      # A prep type with no branch previously fell through silently, deploying
      # an app whose dependencies/binary were never built (observed with
      # `gobuild` on 2026-08-20 → systemd 203/EXEC, no binary on disk).
      echo "unknown prep type '$PREP' for $NAME — no build step ran" >&2
      FAILED+=("$NAME: unknown prep '$PREP'"); continue ;;
  esac

  # 3. permissions — nginx (www-data) must be able to read static files
  chmod -R a+rX "${DEST}/${NAME}"
  [[ "$MODE" == "static" ]] && chown -R www-data:www-data "${DEST}/${NAME}"
  if [[ "$NAME" == "n8n" ]]; then
    # n8n stores its SQLite DB, encryption config, credentials, and owner data
    # here. A broad a+rX above is useful for ordinary app source but unsafe for
    # this state directory, especially on a redeploy where it already exists.
    mkdir -p "${DEST}/${NAME}/data"
    chmod -R go-rwx "${DEST}/${NAME}/data"
    chmod -R u+rwX "${DEST}/${NAME}/data"
  fi

  # 4. hand off to deploy.sh
  if [[ "$MODE" == "static" ]]; then
    "$DEPLOY" --name "$NAME" --mode static --port "$PORT" \
              --dir "$WORKDIR" $DRYFLAG || { FAILED+=("$NAME: deploy"); continue; }
  else
    EXEC="${EXECLINE/SELFDIR/$WORKDIR}"
    # make the binary path absolute (systemd requires it); args stay relative
    [[ "$EXEC" != /* ]] && EXEC="${WORKDIR}/${EXEC}"
    "$DEPLOY" --name "$NAME" --mode proxy --port "$PORT" \
              --dir "$WORKDIR" --exec "$EXEC" $DRYFLAG || { FAILED+=("$NAME: deploy"); continue; }
  fi
  OK+=("$NAME")
done

echo
echo "============================================================"
echo " SUMMARY"
echo "============================================================"
printf '  deployed: %s\n' "${OK[*]:-none}"
if [[ ${#FAILED[@]} -gt 0 ]]; then
  printf '  FAILED:   %s\n' "${FAILED[*]}"
  echo
  echo "  For a failed app:  journalctl -u example-<name> -n 30 --no-pager"
  exit 1
fi
echo
echo "  Edge URLs to check in a browser:"
for row in "${APPS[@]}"; do
  IFS='|' read -r NAME PORT _ _ _ _ <<< "$row"
  want "$NAME" && printf '    https://my-container-%s.example.com/   (%s)\n' "$PORT" "$NAME"
done
