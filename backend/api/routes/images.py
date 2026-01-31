"""
Image proxy route for serving Telegram images.
"""
import os
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/images", tags=["images"])

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def get_telegram_file_path(file_id: str) -> str:
    """Get file path from Telegram API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
            params={"file_id": file_id}
        )
        data = response.json()
        
        if not data.get("ok"):
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        return data["result"]["file_path"]


@router.get("/{file_id}")
async def get_image(file_id: str):
    """
    Proxy endpoint to serve images from Telegram.
    Uses file_id to fetch and stream the image.
    """
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    try:
        file_path = await get_telegram_file_path(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url)
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Не удалось загрузить изображение")
            
            # Determine content type
            content_type = response.headers.get("content-type", "image/jpeg")
            
            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
                }
            )
    
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Ошибка подключения к Telegram")
