# n8n-example

n8n is a native server — unlike the CLI-shaped AI rows it needs no wrapper.
Self-hosted n8n requires NO external account; on first boot it shows a setup
wizard that creates a LOCAL owner login (stored in its own database).

## Run locally
```bash
npm install        # installs n8n into this folder (large, ~5 min first time)
npm start          # serves http://localhost:5678
```

## Container notes
- Port 5678 is n8n's native port (matches CLAUDE.md §6).
- systemd/startup must use Node 22 deterministically. Prefer an Infra-managed stable
  path; on the current root-run container the verified canary path is
  `/root/.nvm/versions/node/v22.22.2/bin/node`. Do not rely on the login shell's
  NVM setup or `/usr/bin/node` (which is still Node 18.19.1).
- `start.sh` stores n8n state under `data/` and configures the public editor
  and webhook URL for `https://my-container-5678.example.com`.
- The first browser visit shows n8n's local owner-account setup. Philip creates
  that account directly; credentials are never stored in this repository.
- n8n stores data in ~/.n8n by default (N8N_USER_FOLDER to relocate).
- ⚠ DISK: the n8n install is large — deploy only after Niels expands the quota.
- Set N8N_SECURE_COOKIE=false only if serving plain http behind the proxy edge.
