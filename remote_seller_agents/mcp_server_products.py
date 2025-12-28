#!/usr/bin/env python3
"""
MCP Server for Product Price Management
Generic server for managing product prices across different categories (burgers, pizzas, etc.)
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Product Price Manager")

# Database configuration
DB_TYPE = os.getenv("CLOUDSQL_DB_TYPE", "mysql")
DB_NAME = os.getenv("CLOUDSQL_DB_NAME", "agentic-db")
DB_USER = os.getenv("CLOUDSQL_USER", "agentic-db")
DB_PASSWORD = os.getenv("CLOUDSQL_PASSWORD", "")
INSTANCE_CONNECTION_NAME = os.getenv("CLOUDSQL_INSTANCE_CONNECTION_NAME")


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
            raise ImportError("cloud-sql-python-connector not installed")
    else:
        # Direct connection fallback
        if DB_TYPE == "mysql":
            import pymysql
            return pymysql.connect(
                host=os.getenv("CLOUDSQL_HOST", "localhost"),
                port=int(os.getenv("CLOUDSQL_PORT", "3306")),
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
        else:
            import psycopg2
            return psycopg2.connect(
                host=os.getenv("CLOUDSQL_HOST", "localhost"),
                port=os.getenv("CLOUDSQL_PORT", "5432"),
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )


@mcp.tool()
def get_product_menu(table_name: str = "product-list") -> List[Dict[str, str]]:
    """
    Retrieve all products from a specified table.
    
    Args:
        table_name: Name of the product table (default: "product-list")
                   Common tables: "product-list" (burgers), "pizza-list" (pizzas)
    
    Returns:
        List of dictionaries containing:
        - itemId: Unique identifier
        - ItemName: Product name
        - Price: Price in base currency units
        - CurrencyType: Currency code
    
    Example:
        get_product_menu("product-list")  # Get burger menu
        get_product_menu("pizza-list")    # Get pizza menu
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == "postgresql":
            query = f'SELECT "itemId", "ItemName", "Price", "CurrencyType" FROM "{table_name}" ORDER BY "itemId"'
        else:
            query = f'SELECT `itemId`, `ItemName`, `Price`, `CurrencyType` FROM `{table_name}` ORDER BY `itemId`'
        
        cursor.execute(query)
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
        
        return menu
        
    except Exception as e:
        raise Exception(f"Failed to retrieve menu from {table_name}: {str(e)}")


@mcp.tool()
def get_product_price(item_name: str, table_name: str = "product-list") -> Dict[str, Any]:
    """
    Get price and details for a specific product by name.
    
    Args:
        item_name: Name of the product to search for (case-insensitive partial match)
        table_name: Name of the product table (default: "product-list")
    
    Returns:
        Dictionary with item details or error message if not found
    
    Example:
        get_product_price("classic", "product-list")      # Find burger
        get_product_price("pepperoni", "pizza-list")      # Find pizza
    """
    try:
        menu = get_product_menu(table_name)
        item_name_lower = item_name.lower()
        
        for item in menu:
            if item_name_lower in item["ItemName"].lower():
                return item
        
        return {"error": f"Item '{item_name}' not found in {table_name}"}
        
    except Exception as e:
        return {"error": f"Failed to search {table_name}: {str(e)}"}


@mcp.tool()
def update_product_price(item_id: str, new_price: str, table_name: str = "product-list") -> Dict[str, str]:
    """
    Update the price of an existing product.
    
    Args:
        item_id: Unique identifier of the product (e.g., "burger-001", "pizza-001")
        new_price: New price in base currency units (e.g., "90000")
        table_name: Name of the product table (default: "product-list")
    
    Returns:
        Success or error message
    
    Example:
        update_product_price("burger-001", "90000", "product-list")
        update_product_price("pizza-001", "75000", "pizza-list")
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Update the price
        if DB_TYPE == "postgresql":
            query = f'UPDATE "{table_name}" SET "Price" = %s WHERE "itemId" = %s'
        else:
            query = f'UPDATE `{table_name}` SET `Price` = %s WHERE `itemId` = %s'
        
        cursor.execute(query, (new_price, item_id))
        
        # Check if any rows were updated
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"Item '{item_id}' not found in {table_name}"}
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Updated {item_id} in {table_name} to {new_price}"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to update price in {table_name}: {str(e)}"}


@mcp.tool()
def add_product_item(
    item_id: str, 
    item_name: str, 
    price: str, 
    table_name: str = "product-list",
    currency_type: str = "IDR"
) -> Dict[str, str]:
    """
    Add a new product item to a table.
    
    Args:
        item_id: Unique identifier for the new product (e.g., "burger-005", "pizza-010")
        item_name: Name of the product (e.g., "Deluxe Bacon Burger", "Hawaiian Pizza")
        price: Price in base currency units (e.g., "95000")
        table_name: Name of the product table (default: "product-list")
        currency_type: Currency code (default: "IDR")
    
    Returns:
        Success or error message
    
    Example:
        add_product_item("burger-005", "Deluxe Bacon Burger", "95000", "product-list")
        add_product_item("pizza-010", "Hawaiian Pizza", "85000", "pizza-list")
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insert new item
        if DB_TYPE == "postgresql":
            query = f'INSERT INTO "{table_name}" ("itemId", "ItemName", "Price", "CurrencyType") VALUES (%s, %s, %s, %s)'
        else:
            query = f'INSERT INTO `{table_name}` (`itemId`, `ItemName`, `Price`, `CurrencyType`) VALUES (%s, %s, %s, %s)'
        
        cursor.execute(query, (item_id, item_name, price, currency_type))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Added {item_id}: {item_name} to {table_name}"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to add item to {table_name}: {str(e)}"}


@mcp.tool()
def list_product_tables() -> List[str]:
    """
    List all available product tables in the database.
    
    Returns:
        List of table names that match the product pattern
    
    Example:
        ["product-list", "pizza-list"]
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == "postgresql":
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%list'
                ORDER BY table_name
            """)
        else:
            cursor.execute(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{DB_NAME}' 
                AND table_name LIKE '%list'
                ORDER BY table_name
            """)
        
        rows = cursor.fetchall()
        tables = [row[0] for row in rows]
        
        cursor.close()
        conn.close()
        
        return tables
        
    except Exception as e:
        return [f"Error: {str(e)}"]


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
