# keycloak-token-retriever

Opens a browser for Keycloak login and prints `Bearer <token>` to stdout.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate.ps1
pip install -e .
cp .env.example .env        # fill in your values
```

## Configuration

| Variable | Required | Description |
|---|---|---|
| `KEYCLOAK_BASE_URL` | yes | e.g. `http://localhost:8080` |
| `KEYCLOAK_REALM` | yes | realm name |
| `KEYCLOAK_CLIENT_ID` | yes | client ID |
| `KEYCLOAK_CLIENT_SECRET` | no | confidential clients only |
| `KEYCLOAK_REDIRECT_URI` | no | must match Keycloak's Valid Redirect URI (default: `http://localhost:8765/callback`) |

## Usage

```bash
kc-token

# capture it
TOKEN=$(kc-token)
curl -H "Authorization: $TOKEN" https://your-api/endpoint
```
