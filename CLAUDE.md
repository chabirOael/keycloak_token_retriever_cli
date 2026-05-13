# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install / reinstall
source .venv/bin/activate
pip install -e .

# Run
kc-token          # via installed entry point
./kc-token.sh     # via bash wrapper (activates venv automatically)
python main.py    # directly
```

## Architecture

Single-file app (`main.py`). The flow is:

1. Load `.env` via `python-dotenv`
2. Generate PKCE pair (`code_verifier` / `code_challenge`) and a random `state`
3. Open the browser to Keycloak's authorization endpoint
4. Spin up a one-shot `HTTPServer` on the redirect URI's port/path to catch the callback
5. Validate `state`, exchange the authorization code for tokens via POST to the token endpoint
6. Print `Bearer <access_token>` to **stdout** only — all other output goes to stderr so the token is capturable with `$(kc-token)`

## Key config details

- `KEYCLOAK_REDIRECT_URI` (full URI) takes precedence over `KEYCLOAK_REDIRECT_PORT`; the server derives its listening port and path from whichever is set
- The redirect URI sent to Keycloak must exactly match the Valid Redirect URI registered in the client settings
- `KEYCLOAK_CLIENT_SECRET` is optional — omit it for public clients (PKCE-only)
