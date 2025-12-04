from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.google.google_auth import get_google_flow

router = APIRouter(prefix="/auth/google", tags=["google-auth"])

@router.get("/login")
async def google_login():
    flow = get_google_flow()
    authorization_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(authorization_url)

@router.get("/callback")
async def google_callback(request: Request):
    flow = get_google_flow()
    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials
    token_json = credentials.to_json()

    # ⛔ RIGHT NOW WE ONLY RETURN IT
    # Later we will SAVE token in Business table
    return {"google_drive_token": token_json}
