import os

from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

load_dotenv()

class TokenRequest(BaseModel):
    token: str

@router.post("/google")
async def google_auth(data: TokenRequest):
    """Login with Google authentication"""
    try:
        id_info = id_token.verify_oauth2_token(
            data.token,
            requests.Request(),
            os.environ["GOOGLE_CLIENT_ID"],
        )
        user = {
            "email": id_info["email"],
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
            "google_id": id_info["sub"]
        }

        return {"status": "success", "user": user}

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")
