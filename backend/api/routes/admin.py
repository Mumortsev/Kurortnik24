"""
Admin API routes.
"""
import os
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io

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

@router.get("/template")
async def get_excel_template():
    """Generate and return sample Excel template."""
    columns = [
        "Категория", "Подкатегория", "Наименование", 
        "Артикул", "Цена (за 1 шт/₽)", "Кол-во в пачке (шт)", "Описание"
    ]
    # Create empty dataframe with these columns
    df = pd.DataFrame(columns=columns)
    
    # Optional: Add example row
    example_row = {
        "Категория": "Пример категории",
        "Подкатегория": "Пример подкатегории",
        "Наименование": "Название товара",
        "Артикул": "ART-123",
        "Цена (за 1 шт/₽)": 100,
        "Кол-во в пачке (шт)": 1,
        "Описание": "Описание товара"
    }
    df = pd.concat([df, pd.DataFrame([example_row])], ignore_index=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="import_template.xlsx"'
    }
    return Response(content=output.getvalue(), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers=headers)
