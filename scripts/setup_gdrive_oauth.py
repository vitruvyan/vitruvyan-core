#!/usr/bin/env python3
"""
setup_gdrive_oauth.py — One-shot Google Drive OAuth2 authorization
===================================================================
Genera un file di credenziali OAuth2 (authorized_user) usabile da
GDriveAdapter per uploadare file su Google Drive personale.

Prerequisiti:
  1. Google Cloud Console → API & Services → Credenziali
  2. Crea credenziali OAuth2 → "App desktop" (Desktop application)
  3. Scarica il JSON → salva in infrastructure/secrets/gdrive-oauth-client.json
  4. Esegui: python3 scripts/setup_gdrive_oauth.py

Output: infrastructure/secrets/gdrive-repo-user-creds.json
        (da impostare come GDRIVE_REPO_CREDENTIALS_FILE nel .env)
"""

import json
import os
import sys

# ── paths ──
SECRETS_DIR = os.path.join(os.path.dirname(__file__), "..", "infrastructure", "secrets")
CLIENT_SECRETS = os.path.join(SECRETS_DIR, "gdrive-oauth-client.json")
OUTPUT_CREDS   = os.path.join(SECRETS_DIR, "gdrive-repo-user-creds.json")

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",   # files created by this app (upload + read)
]


def main():
    # ── check dependencies ──
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import google.oauth2.credentials
    except ImportError:
        print("Missing dependencies. Install with:")
        print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    # ── check client secrets ──
    if not os.path.exists(CLIENT_SECRETS):
        print(f"ERROR: Client secrets not found at {CLIENT_SECRETS}")
        print()
        print("Steps:")
        print("  1. https://console.cloud.google.com/ → your project → API & Services → Credentials")
        print("  2. Click 'Create Credentials' → 'OAuth client ID' → 'Desktop app'")
        print("  3. Download JSON → save as: infrastructure/secrets/gdrive-oauth-client.json")
        print("  4. Re-run this script")
        sys.exit(1)

    print(f"Using client secrets: {CLIENT_SECRETS}")
    print(f"Output credentials: {OUTPUT_CREDS}")
    print()

    # ── run OAuth flow via local server + SSH tunnel ──
    PORT = 8765
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)

    print("=" * 60)
    print("STEP 1 — Sul tuo PC/Mac apri un terminale e lancia:")
    print(f"  ssh -L {PORT}:localhost:{PORT} vitruvyan@aicomsec.vitruvyan.com")
    print()
    print("STEP 2 — Appena connesso, premi INVIO qui sotto per continuare")
    print("=" * 60)
    input("Premi INVIO quando il tunnel SSH è attivo...")

    creds = flow.run_local_server(port=PORT, open_browser=False, fetch_params={"include_granted_scopes": "true"})

    # ── save as authorized_user JSON ──
    creds_data = {
        "type": "authorized_user",
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
    }
    os.makedirs(SECRETS_DIR, exist_ok=True)
    with open(OUTPUT_CREDS, "w") as f:
        json.dump(creds_data, f, indent=2)

    print(f"\n✅ Credentials saved to: {OUTPUT_CREDS}")
    print()
    print("Next steps:")
    print(f"  1. Edit infrastructure/docker/.env:")
    print(f"     GDRIVE_REPO_CREDENTIALS_FILE=/app/secrets/gdrive-repo-user-creds.json")
    print(f"  2. Restart Oculus Prime:")
    print(f"     cd infrastructure/docker && docker compose up -d --no-deps --force-recreate edge_oculus_prime")


if __name__ == "__main__":
    main()
