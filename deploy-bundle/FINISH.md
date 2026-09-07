# Finish the project — remaining deploys (2026-08-12)

Already live: nextjs :3000, n8n :5678, and 20 other rows.
This covers the last 5: redis, postgres, mysql, claude_code, openai_codex.

## STEP 1 — Install PostgreSQL (on its own)

~170 MB, 12 packages. Do NOT bundle mariadb into the same command — mariadb is
a much larger install, and separating them means a failure is attributable.

```bash
ssh my-container-host '
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y postgresql
  systemctl enable --now postgresql
  systemctl is-active postgresql'
```

Expect `active`. Ubuntu's postgres defaults to listen_addresses='localhost',
so it binds loopback with no extra configuration — which is what we want.

(MariaDB, when you get to it, is the same shape: `apt-get install -y
mariadb-server && systemctl enable --now mariadb`.)

## STEP 2 — Create the demo user + database in each

A fresh Postgres/MariaDB install has no *application* account and no database
for our data — only its own admin account. The tiles connect as `disent` to a
database called `disent`, so both must exist first. Without this the tiles still
render, but say "database not reachable".

Run it as one block (heredoc — avoids SSH quote-mangling):

```bash
ssh my-container-host 'bash -s' <<'SETUP'
set -e

# --- PostgreSQL ---------------------------------------------------------
# Postgres trusts the OS user `postgres` as its admin, so we run psql as them.
# Each step is guarded so re-running is harmless.

sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='disent'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE ROLE disent LOGIN PASSWORD 'disent';"

sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='disent'" | grep -q 1 \
  || sudo -u postgres createdb -O disent disent

# --- MariaDB (the MySQL-compatible server Ubuntu ships) -----------------
# root can log in without a password over the local socket. IF NOT EXISTS
# makes every statement safely repeatable.

mariadb -e "CREATE DATABASE IF NOT EXISTS disent;
CREATE USER IF NOT EXISTS 'disent'@'localhost' IDENTIFIED BY 'disent';
GRANT ALL PRIVILEGES ON disent.* TO 'disent'@'localhost';
FLUSH PRIVILEGES;"

echo SETUP_OK
SETUP
```

**Note the quoting:** SQL string literals must be in SINGLE quotes. In Postgres
double quotes mean an *identifier* (a column name), so `rolname="disent"` fails
with `column "disent" does not exist`. The heredoc (`<<'SETUP'`, delimiter
quoted) passes the text through untouched, so the single quotes survive.

### Verify it worked

```bash
ssh my-container-host '
  PGPASSWORD=disent psql -h 127.0.0.1 -U disent -d disent -tAc "SELECT current_user, version()" | head -1
  mariadb -u disent -pdisent disent -e "SELECT CURRENT_USER(), VERSION();"'
```

Each should print a user/version line. That is exactly the connection the tiles
make, so if this works the tiles will too.

### About the credentials

`disent` / `disent` is deliberately trivial. That is acceptable ONLY because
both servers listen on 127.0.0.1 and hold nothing but demo rows — nothing can
reach them from outside the container. If either is ever bound beyond loopback,
change the password first.

## STEP 3 — Install the two CLIs under Node 22

`/usr/bin/node` is v18 and too old for both. Use the nvm prefix.

```bash
ssh my-container-host '
  export PATH=/root/.nvm/versions/node/v22.22.2/bin:$PATH
  npm install -g @anthropic-ai/claude-code @openai/codex
  claude --version; codex --version'
```

The tiles resolve these by absolute nvm path, so systemd's PATH does not matter.

## STEP 4 — Upload + deploy the 5 rows

```bash
cd ~/Desktop/sandbox
scp -r deploy-bundle my-container-host:/root/projects/sandbox/
ssh my-container-host '/root/projects/sandbox/deploy-bundle/deploy-all.sh \
  redis postgres mysql claude-code openai-codex'
```

Each should report `bind on :PORT -> 0.0.0.0:PORT`.

## STEP 5 — API keys for the two CLI tiles (optional)

Both work BYOK (paste a key in the UI). For a server key:

```bash
scp claude-code-example/app/.env  my-container-host:/srv/apps/claude-code/.env
scp openai-codex-example/app/.env my-container-host:/srv/apps/openai-codex/.env
ssh my-container-host '
  for a in claude-code openai-codex; do
    grep -q EnvironmentFile /etc/systemd/system/example-$a.service \
      || sed -i "/^Environment=PORT=/a EnvironmentFile=/srv/apps/$a/.env" \
           /etc/systemd/system/example-$a.service
  done
  systemctl daemon-reload && systemctl restart example-claude-code example-openai-codex'
```

NOTE: deploy.sh regenerates the unit on every deploy, so re-apply this after any
redeploy of those two rows.

## STEP 6 — Publish the tiles

```bash
cd ~/Desktop/sandbox/container-fixes
scp manifest.json my-container-host:/srv/apps/homepage/manifest.json
```
