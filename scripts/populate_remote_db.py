
import asyncio
import os
import sys
import aiohttp
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# API URL
API_URL = "https://kurortnik24-production.up.railway.app/api"

# Log file
LOG_FILE = "remote_import_log.txt"

def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode('ascii', 'replace').decode('ascii'))
        
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_excel_file(file_path: str) -> list:
    log(f"Parsing file: {file_path}")
    df = pd.read_excel(file_path)
    products = []
    
    for idx, row in df.iterrows():
        try:
            # Column mapping by index based on inspect_excel.py
            # 0: Category, 1: Subcategory, 2: Name, 3: Article, 4: Price, 5: Pieces, 6: Description
            
            category_raw = row.iloc[0]
            subcategory_raw = row.iloc[1]
            name_raw = row.iloc[2]
            article_raw = row.iloc[3]
            price_raw = row.iloc[4]
            pieces_raw = row.iloc[5]
            desc_raw = row.iloc[6] if len(row) > 6 else ""
            
            if pd.isna(name_raw): continue
            
            name = str(name_raw).strip()
            category = str(category_raw).strip() if not pd.isna(category_raw) else "Каталог"
            subcategory = str(subcategory_raw).strip() if not pd.isna(subcategory_raw) else None
            
            description = ""
            if not pd.isna(desc_raw): description = str(desc_raw).strip()
            if not pd.isna(article_raw): 
                article = str(article_raw).strip()
                description = f"Артикул: {article}\n{description}".strip()
                
            try: price = float(price_raw)
            except: price = 100.0
            
            try: pieces = int(pieces_raw)
            except: pieces = 1
            
            products.append({
                "name": name,
                "description": description,
                "price_per_unit": price if price > 0 else 100.0,
                "pieces_per_pack": pieces if pieces > 0 else 1,
                "min_order_packs": 1,
                "category_name": category,
                "subcategory_name": subcategory,
                "image_url": None
            })
        except Exception as e:
            log(f"Error row {idx}: {e}")
            
    log(f"Extracted {len(products)} products")
    return products

async def get_or_create_category(session, category_name):
    # Get all categories
    async with session.get(f"{API_URL}/categories") as resp:
        if resp.status == 200:
            data = await resp.json()
            cats = data.get("categories", [])
            for cat in cats:
                if cat["name"].lower() == category_name.lower():
                    return cat["id"], cat.get("subcategories", [])
    
    # Create
    log(f"Creating category: {category_name}")
    async with session.post(f"{API_URL}/categories", json={"name": category_name, "order": 0}) as resp:
        if resp.status in [200, 201]:
            data = await resp.json()
            return data["id"], []
        else:
            log(f"Error creating category {category_name}: {await resp.text()}")
            return None, []

async def get_or_create_subcategory(session, category_id, subcategory_name, existing_subcats):
    if not subcategory_name: return None
    
    for sub in existing_subcats:
        if sub["name"].lower() == subcategory_name.lower():
            return sub["id"]
            
    # Create
    log(f"Creating subcategory: {subcategory_name}")
    async with session.post(f"{API_URL}/categories/{category_id}/subcategories", 
                          json={"name": subcategory_name, "order": 0, "category_id": category_id}) as resp:
        if resp.status in [200, 201]:
            data = await resp.json()
            # Update cache locally ideally, but simple return is enough
            existing_subcats.append(data) 
            return data["id"]
        else:
            log(f"Error creating subcategory {subcategory_name}: {await resp.text()}")
            return None

async def upload_products(products):
    async with aiohttp.ClientSession() as session:
        # Cache: name -> (id, subcats_list)
        cat_cache = {} 
        
        for p in products:
            p_submit = p.copy()
            cat_name = p_submit.pop("category_name")
            sub_name = p_submit.pop("subcategory_name")
            
            # 1. Resolve Category
            if cat_name not in cat_cache:
                cat_id, subcats = await get_or_create_category(session, cat_name)
                if not cat_id: 
                    continue
                cat_cache[cat_name] = (cat_id, subcats)
            else:
                cat_id, subcats = cat_cache[cat_name]
                
            p_submit["category_id"] = cat_id
            
            # 2. Resolve Subcategory
            if sub_name:
                sub_id = await get_or_create_subcategory(session, cat_id, sub_name, subcats)
                if sub_id:
                    p_submit["subcategory_id"] = sub_id
            
            # 3. Create Product
            log(f"Uploading: {p_submit['name']}")
            async with session.post(f"{API_URL}/products", json=p_submit) as resp:
                if resp.status not in [200, 201]:
                    txt = await resp.text()
                    log(f"Failed {p_submit['name']}: {txt}")
                else:
                    # dot progress
                    print(".", end="", flush=True)

async def main():
    fpath = r"c:\Antigravity\Project\data\template_for_client.xlsx"
    products = parse_excel_file(fpath)
    if products:
        await upload_products(products)
        print("\nDone")

if __name__ == "__main__":
    asyncio.run(main())
