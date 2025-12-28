"""
Cloud SQL Database Query Tool
Provides functions to query product data from Cloud SQL.
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DB_TYPE = os.getenv("CLOUDSQL_DB_TYPE", "mysql")
DB_NAME = os.getenv("CLOUDSQL_DB_NAME", "agentic-db")
DB_USER = os.getenv("CLOUDSQL_USER", "agentic-db")
DB_PASSWORD = os.getenv("CLOUDSQL_PASSWORD", "")
INSTANCE_CONNECTION_NAME = os.getenv("CLOUDSQL_INSTANCE_CONNECTION_NAME")

# Cache for menu data
_menu_cache = None


def get_connection():
    """Get database connection."""
    if INSTANCE_CONNECTION_NAME:
        try:
            from google.cloud.sql.connector import Connector
            
            connector = Connector()
            
            return connector.connect(
                INSTANCE_CONNECTION_NAME,
                "pg8000" if DB_TYPE == "postgresql" else "pymysql",
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
            )
        except ImportError:
            print("ERROR: cloud-sql-python-connector not installed.")
            return None
    else:
        # Direct connection fallback
        if DB_TYPE == "mysql":
            try:
                import pymysql
                return pymysql.connect(
                    host=os.getenv("CLOUDSQL_HOST", "localhost"),
                    port=int(os.getenv("CLOUDSQL_PORT", "3306")),
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                )
            except ImportError:
                print("ERROR: pymysql not installed.")
                return None


def get_burger_menu() -> List[Dict[str, str]]:
    """
    Fetch all burger items from the database.
    
    Returns:
        List of dictionaries containing item data:
        [
            {
                "itemId": "burger-001",
                "ItemName": "Classic Cheeseburger",
                "Price": "85000",
                "CurrencyType": "IDR"
            },
            ...
        ]
    """
    global _menu_cache
    
    # Return cached data if available
    if _menu_cache is not None:
        return _menu_cache
    
    try:
        conn = get_connection()
        if not conn:
            return _get_fallback_menu()
        
        cursor = conn.cursor()
        
        if DB_TYPE == "postgresql":
            cursor.execute('SELECT "itemId", "ItemName", "Price", "CurrencyType" FROM "product-list" ORDER BY "itemId"')
        else:
            cursor.execute('SELECT `itemId`, `ItemName`, `Price`, `CurrencyType` FROM `product-list` ORDER BY `itemId`')
        
        rows = cursor.fetchall()
        
        menu = []
        for row in rows:
            menu.append({
                "itemId": row[0],
                "ItemName": row[1],
                "Price": row[2],
                "CurrencyType": row[3]
            })
        
        cursor.close()
        conn.close()
        
        # Cache the result
        _menu_cache = menu
        return menu
        
    except Exception as e:
        print(f"Error fetching menu from database: {e}")
        return _get_fallback_menu()


def _get_fallback_menu() -> List[Dict[str, str]]:
    """Fallback menu if database is unavailable."""
    return [
        {"itemId": "burger-001", "ItemName": "Classic Cheeseburger", "Price": "85000", "CurrencyType": "IDR"},
        {"itemId": "burger-002", "ItemName": "Double Cheeseburger", "Price": "110000", "CurrencyType": "IDR"},
        {"itemId": "burger-003", "ItemName": "Spicy Chicken Burger", "Price": "80000", "CurrencyType": "IDR"},
        {"itemId": "burger-004", "ItemName": "Spicy Cajun Burger", "Price": "85000", "CurrencyType": "IDR"},
    ]


def format_menu_for_display() -> str:
    """
    Get formatted menu string for display.
    
    Returns:
        Formatted string like:
        - Classic Cheeseburger: IDR 85K
        - Double Cheeseburger: IDR 110K
        ...
    """
    menu = get_burger_menu()
    lines = []
    
    for item in menu:
        # Format price (e.g., "85000" -> "85K")
        price = item["Price"]
        if len(price) >= 3:
            price_formatted = f"{int(price)//1000}K"
        else:
            price_formatted = price
        
        lines.append(f"- {item['ItemName']}: {item['CurrencyType']} {price_formatted}")
    
    return "\n".join(lines)


def get_item_by_name(name: str) -> Optional[Dict[str, str]]:
    """
    Find a burger item by name (case-insensitive partial match).
    
    Args:
        name: Item name to search for
        
    Returns:
        Dictionary with item data or None if not found
    """
    menu = get_burger_menu()
    name_lower = name.lower()
    
    for item in menu:
        if name_lower in item["ItemName"].lower():
            return item
    
    return None


def clear_cache():
    """Clear the menu cache to force fresh database query."""
    global _menu_cache
    _menu_cache = None


if __name__ == "__main__":
    # Test the module
    print("Testing Cloud SQL Query Tool...")
    print("\nFetching menu:")
    print(format_menu_for_display())
    
    print("\nSearching for 'classic':")
    item = get_item_by_name("classic")
    if item:
        print(f"  Found: {item['ItemName']} - {item['CurrencyType']} {item['Price']}")
