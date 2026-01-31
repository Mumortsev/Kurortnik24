"""
Import products from Excel files.
Reads all .xlsx files from the specified directory and imports them into the database.
"""
import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

try:
    import pandas as pd
except ImportError:
    print("Installing pandas...")
    os.system("pip install pandas openpyxl")
    import pandas as pd

from dotenv import load_dotenv
load_dotenv()

# Log file
LOG_FILE = "import_log.txt"


def log(message: str):
    """Log message to console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def parse_excel_file(file_path: str) -> dict:
    """
    Parse Excel file and extract products.
    Returns dict with category name and list of products.
    """
    log(f"Parsing file: {file_path}")
    
    df = pd.read_excel(file_path)
    
    # Get category name from filename
    filename = Path(file_path).stem  # Remove extension
    # Clean up category name (remove numbers at the end)
    category_name = ''.join([c for c in filename if not c.isdigit()]).strip()
    
    products = []
    
    # Detect column structure by finding the header row
    # Usually first row contains column names like "Наименование", "Артикул", etc.
    columns = list(df.columns)
    
    # Map columns to standard names
    col_mapping = {
        "name": None,
        "article": None,
        "pieces_per_pack": None,
        "price": None
    }
    
    # Check first row if it contains headers
    first_row = df.iloc[0] if len(df) > 0 else {}
    
    # Find columns by checking both column names and first row values
    for idx, col in enumerate(columns):
        col_lower = str(col).lower()
        first_val = str(first_row.get(col, "")).lower() if len(df) > 0 else ""
        
        # Name column
        if any(x in col_lower or x in first_val for x in ["наименование", "название"]):
            col_mapping["name"] = col
        # Article column  
        if any(x in col_lower or x in first_val for x in ["артикул"]):
            col_mapping["article"] = col
        # Pieces per pack
        if any(x in col_lower or x in first_val for x in ["количество", "кол в", "корл шт"]):
            col_mapping["pieces_per_pack"] = col
        # Price
        if any(x in col_lower or x in first_val for x in ["цена"]):
            col_mapping["price"] = col
    
    log(f"  Column mapping: {col_mapping}")
    
    # Determine start row (skip header row if first row contains text headers)
    start_row = 0
    if col_mapping["name"] is not None:
        first_val = str(first_row.get(col_mapping["name"], "")).lower()
        if "наименование" in first_val or "название" in first_val:
            start_row = 1
    
    # Parse rows
    for idx in range(start_row, len(df)):
        row = df.iloc[idx]
        
        # Get name
        name = None
        if col_mapping["name"]:
            name = row.get(col_mapping["name"])
        else:
            # Try to find name in any column (usually second column)
            for col in columns[1:4]:
                val = row.get(col)
                if pd.notna(val) and isinstance(val, str) and len(val) > 5:
                    name = val
                    break
        
        if not name or pd.isna(name) or not str(name).strip():
            continue
        
        name = str(name).strip()
        
        # Get article
        article = ""
        if col_mapping["article"]:
            val = row.get(col_mapping["article"])
            if pd.notna(val):
                article = str(val).strip()
        
        # Get pieces per pack
        pieces_per_pack = 1
        if col_mapping["pieces_per_pack"]:
            val = row.get(col_mapping["pieces_per_pack"])
            if pd.notna(val):
                try:
                    # Handle values like "100 Mix"
                    val_str = str(val).split()[0]
                    pieces_per_pack = int(float(val_str))
                except (ValueError, IndexError):
                    pieces_per_pack = 1
        
        # Get price
        price = 0
        if col_mapping["price"]:
            val = row.get(col_mapping["price"])
            if pd.notna(val):
                try:
                    price = float(val)
                except ValueError:
                    price = 0
        else:
            # Try to find price in numeric columns
            for col in columns:
                val = row.get(col)
                if pd.notna(val):
                    try:
                        num = float(val)
                        if 0 < num < 10000 and num not in [pieces_per_pack]:
                            price = num
                            break
                    except (ValueError, TypeError):
                        pass
        
        # Skip if no name
        if not name:
            continue
            
        # Build product description with article if exists
        description = ""
        if article:
            description = f"Артикул: {article}"
        
        products.append({
            "name": name,
            "description": description,
            "price_per_unit": price if price > 0 else 100,  # Default price
            "pieces_per_pack": pieces_per_pack if pieces_per_pack > 0 else 1,
            "article": article
        })
    
    log(f"  Extracted {len(products)} products")
    
    return {
        "category": category_name,
        "products": products
    }


async def import_to_database(data: list):
    """Import parsed data to database."""
    from api.database import init_db, AsyncSessionLocal
    from api.models import Category, Subcategory, Product
    from sqlalchemy import select
    
    # Initialize database
    await init_db()
    
    async with AsyncSessionLocal() as session:
        imported = 0
        errors = 0
        
        for file_data in data:
            category_name = file_data["category"]
            products = file_data["products"]
            
            if not products:
                continue
            
            # Find or create category
            result = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            category = result.scalars().first()
            
            if not category:
                # Get max order
                result = await session.execute(
                    select(Category).order_by(Category.order.desc())
                )
                last_cat = result.scalars().first()
                new_order = (last_cat.order if last_cat else 0) + 1
                
                category = Category(name=category_name, order=new_order)
                session.add(category)
                await session.flush()
                log(f"[+] Created category: {category_name}")
            
            # Create default subcategory "Все"
            result = await session.execute(
                select(Subcategory).where(
                    Subcategory.category_id == category.id,
                    Subcategory.name == "Все"
                )
            )
            subcategory = result.scalars().first()
            
            if not subcategory:
                subcategory = Subcategory(
                    category_id=category.id,
                    name="Все",
                    order=1
                )
                session.add(subcategory)
                await session.flush()
            
            # Import products
            for product_data in products:
                try:
                    # Check if product already exists (by name and category)
                    result = await session.execute(
                        select(Product).where(
                            Product.name == product_data["name"],
                            Product.category_id == category.id
                        )
                    )
                    existing = result.scalars().first()
                    
                    if existing:
                        # Update existing product
                        existing.price_per_unit = product_data["price_per_unit"]
                        existing.pieces_per_pack = product_data["pieces_per_pack"]
                        if product_data["description"]:
                            existing.description = product_data["description"]
                        log(f"  [~] Updated: {product_data['name']}")
                    else:
                        # Create new product
                        product = Product(
                            name=product_data["name"],
                            description=product_data["description"] or None,
                            price_per_unit=product_data["price_per_unit"],
                            pieces_per_pack=product_data["pieces_per_pack"],
                            min_order_packs=1,
                            category_id=category.id,
                            subcategory_id=subcategory.id,
                            active=True,
                            in_stock=None  # Unlimited
                        )
                        session.add(product)
                        log(f"  [+] Added: {product_data['name']}")
                    
                    imported += 1
                    
                except Exception as e:
                    log(f"  [X] Error adding {product_data['name']}: {e}")
                    errors += 1
        
        await session.commit()
        
        return imported, errors


async def main():
    """Main import function."""
    # Directory with Excel files
    excel_dir = r"c:\Antigravity"
    
    log("=" * 50)
    log("Import from Excel files")
    log("=" * 50)
    
    # Find all Excel files
    excel_files = list(Path(excel_dir).glob("*.xlsx"))
    
    if not excel_files:
        log("No Excel files found!")
        return
    
    log(f"Found {len(excel_files)} Excel files:")
    for f in excel_files:
        log(f"  - {f.name}")
    
    # Parse all files
    all_data = []
    for file_path in excel_files:
        try:
            data = parse_excel_file(str(file_path))
            all_data.append(data)
        except Exception as e:
            log(f"Error parsing {file_path.name}: {e}")
    
    # Import to database
    log("\nImporting to database...")
    imported, errors = await import_to_database(all_data)
    
    log("\n" + "=" * 50)
    log(f"Import complete!")
    log(f"  [+] Imported: {imported}")
    log(f"  [X] Errors: {errors}")
    log("=" * 50)
    
    log("\n[!] IMPORTANT: Check prices and pack quantities via bot admin!")
    log("    Some products may have default prices (100 RUB)")


if __name__ == "__main__":
    print("\n=== Import products from Excel ===\n")
    asyncio.run(main())
