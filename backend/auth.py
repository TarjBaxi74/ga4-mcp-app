import os
import json as json_lib
import requests as req_lib
import base64
import hashlib
import secrets
import uuid

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from google.analytics.admin import AnalyticsAdminServiceClient
from google.oauth2.credentials import Credentials

from fastapi.responses import RedirectResponse, JSONResponse
# from google.cloud import firestore

router = APIRouter()

# -----------------------------
# CONFIG (from env)
# -----------------------------
CLIENT_SECRET_FILE = "credentials/oauth-client.json"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]

REDIRECT_URI = os.getenv("REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Firestore client
def get_db():
    from google.cloud import firestore
    return firestore.Client()

# -----------------------------
# STEP 1 — LOGIN (UNCHANGED LOGIC)
# -----------------------------
@router.get("/url")
def get_auth_url():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )

    # store in Firestore instead of memory
    db = get_db()
    db.collection("sessions").document(state).set({
        "status": "pending",
        "code_verifier": code_verifier,
    })

    return {"url": auth_url, "state": state}


# -----------------------------
# STEP 2 — CALLBACK
# -----------------------------

@router.get("/callback")
def auth_callback(code: str, state: str):
    db = get_db()
    try:
        # --- existing logic ---
        doc = db.collection("sessions").document(state).get()
        if not doc.exists:
            return {"error": "Invalid state"}

        session = doc.to_dict()
        code_verifier = session.get("code_verifier")

        # exchange token
        with open(CLIENT_SECRET_FILE) as f:
            client_config = json_lib.load(f)

            client_data = client_config.get("installed") or client_config.get("web")

            client_id = client_data["client_id"]
            client_secret = client_data["client_secret"]
            token_uri = client_data["token_uri"]

        resp = req_lib.post(token_uri, data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        })

        token_data = resp.json()
        print("CALLBACK HIT")
        print("CODE:", code)
        print("STATE:", state)

        if "error" in token_data:
            return {"error": token_data}

        session_id = str(uuid.uuid4())

        print("STORING SESSION...")

        # ✅ STORE FIRST (critical)
        db.collection("sessions").document(session_id).set({
            "status": "authenticated",
            "token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_uri": token_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": SCOPES,
        })

        # ✅ SAFE REDIRECT
        if FRONTEND_URL and FRONTEND_URL != "TEMP":
            return RedirectResponse(url=f"{FRONTEND_URL}/?session_id={session_id}")
        else:
            # fallback for now
            return JSONResponse({"session_id": session_id})

    except Exception as e:
        import traceback
        print("CALLBACK ERROR:", traceback.format_exc())
        return {"error": str(e)}


# -----------------------------
# REQUEST MODEL
# -----------------------------
class SessionRequest(BaseModel):
    session_id: str


# -----------------------------
# PROPERTIES API
# -----------------------------
@router.post("/properties")
def get_properties(req: SessionRequest):
    db = get_db()
    doc = db.collection("sessions").document(req.session_id).get()

    if not doc.exists:
        return {"error": "Invalid session"}

    session = doc.to_dict()

    creds = _creds_from_session(session)

    try:
        admin = AnalyticsAdminServiceClient(credentials=creds)
        accounts = []

        for account in admin.list_account_summaries():
            props = []
            for prop in account.property_summaries:
                props.append({
                    "id": prop.property.replace("properties/", ""),
                    "name": prop.display_name,
                })
            accounts.append({
                "id": account.account.replace("accounts/", ""),
                "name": account.display_name,
                "properties": props,
            })

        return {"accounts": accounts}

    except Exception as e:
        import traceback
        print("PROPERTIES ERROR:", traceback.format_exc())
        return {"error": str(e)}


# -----------------------------
# CREDS HELPERS
# -----------------------------
def _creds_from_session(session: dict) -> Credentials:
    return Credentials(
        token=session["token"],
        refresh_token=session["refresh_token"],
        token_uri=session["token_uri"],
        client_id=session["client_id"],
        client_secret=session["client_secret"],
        scopes=session["scopes"],
    )


def get_session_creds(session_id: str) -> Credentials:
    db = get_db()
    doc = db.collection("sessions").document(session_id).get()

    if not doc.exists:
        raise ValueError("Invalid session")

    return _creds_from_session(doc.to_dict())