"""
Image proxy route for serving Telegram images.
"""
import os
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File
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


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Загрузка изображения с автоматическим сжатием и конвертацией в WebP.
    Создаёт основное фото (макс. 1200px) и превью (300px).
    """
    try:
        from pathlib import Path
        from PIL import Image
        import io
        import uuid
        
        # Определяем директорию для сохранения
        is_docker = os.path.exists("/data")
        
        if is_docker:
            upload_dir = Path("/data/uploads")
        else:
            current_file = Path(__file__).resolve()
            backend_root = current_file.parent.parent.parent
            upload_dir = backend_root / "static" / "uploads"
        
        os.makedirs(upload_dir, exist_ok=True)
        
        # Читаем файл в память
        contents = await file.read()
        
        # Открываем через Pillow
        try:
            img = Image.open(io.BytesIO(contents))
        except Exception:
            raise HTTPException(status_code=400, detail="Невозможно открыть файл как изображение")
        
        # Конвертируем RGBA в RGB (WebP не всегда хорошо работает с прозрачностью)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Генерируем уникальное имя
        unique_id = str(uuid.uuid4())
        
        # === Основное фото (максимум 1200px по широкой стороне) ===
        main_img = img.copy()
        max_size = 1200
        if main_img.width > max_size or main_img.height > max_size:
            main_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        main_filename = f"{unique_id}.webp"
        main_path = upload_dir / main_filename
        main_img.save(main_path, "WEBP", quality=85, optimize=True)
        
        # === Превью (300px для каталога) ===
        thumb_img = img.copy()
        thumb_size = 300
        thumb_img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        
        thumb_filename = f"{unique_id}_thumb.webp"
        thumb_path = upload_dir / thumb_filename
        thumb_img.save(thumb_path, "WEBP", quality=80, optimize=True)
        
        # Формируем URL для ответа
        if is_docker:
            url_path = f"/uploads/{main_filename}"
            thumb_url = f"/uploads/{thumb_filename}"
        else:
            url_path = f"/static/uploads/{main_filename}"
            thumb_url = f"/static/uploads/{thumb_filename}"
        
        return {
            "url": url_path,
            "file_id": url_path,
            "thumbnail": thumb_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")
