import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "google_oauth.json")

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
]

def get_google_flow():
    return Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )


def credentials_from_token(token_json: str) -> Credentials:
    return Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
