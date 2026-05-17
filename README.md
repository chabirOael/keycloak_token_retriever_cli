# keycloak-token-retriever

Opens a browser for Keycloak login and prints `Bearer <token>` to stdout.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e .
```

Create your `.env`:

```bash
cp .env.example .env
```

Then edit `.env` with your Keycloak details:

```env
KEYCLOAK_BASE_URL=https://your-keycloak-host:port   # base URL of your Keycloak server
KEYCLOAK_REALM=your-realm
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=                              # leave blank for public clients
```

## Usage

```bash
./kc-token.sh

# capture the token
TOKEN=$(./kc-token.sh)
curl -H "Authorization: $TOKEN" https://your-api/endpoint
```
