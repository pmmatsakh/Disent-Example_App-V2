#!/usr/bin/env bash
set -euo pipefail

# systemd/non-login SSH does not load NVM. Use the container's verified Node
# 22 directly; fall back to PATH only for local Mac development.
NODE_BIN="${NODE_BIN:-/root/.nvm/versions/node/v22.22.2/bin/node}"
[[ -x "$NODE_BIN" ]] || NODE_BIN="$(command -v node)"

export N8N_LISTEN_ADDRESS="${N8N_LISTEN_ADDRESS:-0.0.0.0}"
export N8N_PORT="${PORT:-${N8N_PORT:-5678}}"
export N8N_PROXY_HOPS="${N8N_PROXY_HOPS:-1}"

PUBLIC_URL="${N8N_PUBLIC_URL:-https://my-container-5678.example.com}"
export WEBHOOK_URL="${WEBHOOK_URL:-${PUBLIC_URL}/}"
export N8N_EDITOR_BASE_URL="${N8N_EDITOR_BASE_URL:-${PUBLIC_URL}/}"

# Keep n8n's SQLite database, encryption config, and owner account across
# service restarts and code redeploys. Never include this directory in source.
export N8N_USER_FOLDER="${N8N_USER_FOLDER:-${PWD}/data}"
mkdir -p "$N8N_USER_FOLDER"

export N8N_SECURE_COOKIE="${N8N_SECURE_COOKIE:-true}"
export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS="${N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS:-true}"
export N8N_DIAGNOSTICS_ENABLED="${N8N_DIAGNOSTICS_ENABLED:-false}"
export N8N_PERSONALIZATION_ENABLED="${N8N_PERSONALIZATION_ENABLED:-false}"
export DB_SQLITE_POOL_SIZE="${DB_SQLITE_POOL_SIZE:-2}"
export N8N_RUNNERS_ENABLED="${N8N_RUNNERS_ENABLED:-true}"
export N8N_BLOCK_ENV_ACCESS_IN_NODE="${N8N_BLOCK_ENV_ACCESS_IN_NODE:-true}"
export N8N_GIT_NODE_DISABLE_BARE_REPOS="${N8N_GIT_NODE_DISABLE_BARE_REPOS:-true}"

exec "$NODE_BIN" node_modules/n8n/bin/n8n
