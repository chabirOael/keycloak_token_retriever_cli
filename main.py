#!/usr/bin/env python3
"""Keycloak Standard Flow (Authorization Code + PKCE) token retriever for dev use."""

import base64
import hashlib
import os
import secrets
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "").rstrip("/")
REALM = os.getenv("KEYCLOAK_REALM", "")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")

_raw_redirect = os.getenv("KEYCLOAK_REDIRECT_URI", "")
if _raw_redirect:
    _parsed = urlparse(_raw_redirect)
    REDIRECT_URI = _raw_redirect
    REDIRECT_PORT = _parsed.port or 80
    REDIRECT_PATH = _parsed.path or "/callback"
else:
    REDIRECT_PORT = int(os.getenv("KEYCLOAK_REDIRECT_PORT", "8765"))
    REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
    REDIRECT_PATH = "/callback"

_callback_result: dict = {}


def _validate_config() -> None:
    missing = [
        name
        for name, val in {
            "KEYCLOAK_BASE_URL": BASE_URL,
            "KEYCLOAK_REALM": REALM,
            "KEYCLOAK_CLIENT_ID": CLIENT_ID,
        }.items()
        if not val
    ]
    if missing:
        print(f"[error] Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        print("Copy .env.example to .env and fill in the values.", file=sys.stderr)
        sys.exit(1)


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


def _build_auth_url(state: str, code_challenge: str) -> str:
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return (
        f"{BASE_URL}/realms/{REALM}/protocol/openid-connect/auth"
        f"?{urllib.parse.urlencode(params)}"
    )


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path != REDIRECT_PATH:
            self.send_response(404)
            self.end_headers()
            return

        if "code" in query:
            _callback_result["code"] = query["code"][0]
            _callback_result["state"] = query.get("state", [None])[0]
            body = b"<h2>Authentication successful &#x2714; You can close this tab.</h2>"
            self.send_response(200)
        else:
            error = query.get("error_description", query.get("error", ["unknown"]))[0]
            _callback_result["error"] = error
            body = f"<h2>Authentication failed: {error}</h2>".encode()
            self.send_response(400)

        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_) -> None:  # silence access logs
        pass


def _wait_for_callback(expected_state: str) -> str:
    server = HTTPServer(("127.0.0.1", REDIRECT_PORT), _CallbackHandler)
    server.timeout = 120  # 2 min before giving up

    print(
        f"[info] Listening on {REDIRECT_URI} (timeout: 120 s)",
        file=sys.stderr,
    )
    server.handle_request()
    server.server_close()

    if "error" in _callback_result:
        print(f"[error] Keycloak returned an error: {_callback_result['error']}", file=sys.stderr)
        sys.exit(1)

    if "code" not in _callback_result:
        print("[error] Timed out waiting for the browser callback.", file=sys.stderr)
        sys.exit(1)

    if _callback_result.get("state") != expected_state:
        print("[error] State mismatch — possible CSRF attack.", file=sys.stderr)
        sys.exit(1)

    return _callback_result["code"]


def _exchange_code(code: str, code_verifier: str) -> str:
    token_url = f"{BASE_URL}/realms/{REALM}/protocol/openid-connect/token"
    data: dict = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "code_verifier": code_verifier,
    }
    if CLIENT_SECRET:
        data["client_secret"] = CLIENT_SECRET

    resp = requests.post(token_url, data=data, timeout=10)
    if not resp.ok:
        print(
            f"[error] Token exchange failed ({resp.status_code}): {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    return resp.json()["access_token"]


def main() -> None:
    _validate_config()

    state = secrets.token_urlsafe(16)
    code_verifier, code_challenge = _pkce_pair()
    auth_url = _build_auth_url(state, code_challenge)

    print("[info] Opening browser for Keycloak login...", file=sys.stderr)
    if not webbrowser.open(auth_url):
        print(f"[info] Could not open browser. Visit this URL manually:\n{auth_url}", file=sys.stderr)

    code = _wait_for_callback(state)
    access_token = _exchange_code(code, code_verifier)

    # Only the token line goes to stdout — easy to capture with $()
    print(f"Bearer {access_token}")


if __name__ == "__main__":
    main()
