"""
Admin API routes.
"""
import os
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

class AdminCheckRequest(BaseModel):
    user_id: int

@router.post("/check")
async def check_admin(data: AdminCheckRequest):
    """Check if user is admin."""
    if data.user_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"status": "ok", "is_admin": True}
