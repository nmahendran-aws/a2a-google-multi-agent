# MCP Server for Product Prices - User Guide

## Overview

Generic MCP server for managing product prices across **any product category** (burgers, pizzas, etc.) in Cloud SQL.

## Available Tools

### 1. list_product_tables
Discover all available product tables.

**Usage:**
> "What product tables are available?"

**Returns:**
```json
["product-list", "pizza-list"]
```

---

### 2. get_product_menu
Retrieve all products from a table.

**Usage:**
> "Show me the burger menu" → uses table "product-list"
> "Show me the pizza menu" → uses table "pizza-list"

**Parameters:**
- `table_name` (optional): Table to query (default: "product-list")

**Returns:**
```json
[
  {
    "itemId": "burger-001",
    "ItemName": "Classic Cheeseburger",
    "Price": "85000",
    "CurrencyType": "IDR"
  }
]
```

---

### 3. get_product_price
Search for a specific product by name.

**Usage:**
> "What's the price of pepperoni pizza?"

**Parameters:**
- `item_name`: Product name to search
- `table_name` (optional): Table to search (default: "product-list")

---

### 4. update_product_price
Update price of an existing product.

**Usage:**
> "Update burger-001 to 90000"

**Parameters:**
- `item_id`: Product ID
- `new_price`: New price
- `table_name` (optional): Table name (default: "product-list")

---

### 5. add_product_item
Add new product to a table.

**Usage:**
> "Add pizza-010 named 'Hawaiian Pizza' with price 85000 to pizza-list"

**Parameters:**
- `item_id`: Unique ID
- `item_name`: Product name
- `price`: Price
- `table_name` (optional): Table name
- `currency_type` (optional): Currency (default: "IDR")

## Claude Desktop Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "product-prices": {
      "command": "uv",
      "args": ["run", "python", "-m", "remote_seller_agents.mcp_server_products"],
      "cwd": "/Users/mahen/learnings/AI/ai-agent/agent-google/a2a/purchasing-concierge-a2a",
      "env": {
        "CLOUDSQL_DB_TYPE": "mysql",
        "CLOUDSQL_DB_NAME": "agentic-db",
        "CLOUDSQL_USER": "agentic-db",
        "CLOUDSQL_INSTANCE_CONNECTION_NAME": "mahen-projects:us-east4:agentic-db"
      }
    }
  }
}
```

**Update `cwd` to your project path.**

## Examples

### Burgers (product-list table)
```
"Show me the burger menu"
"Update burger-001 price to 95000"
"Add a new burger: ID burger-005, name 'Deluxe Bacon', price 100000"
```

### Pizzas (pizza-list table)  
```
"Show me the pizza menu from pizza-list"
"What's the price of margherita in pizza-list?"
"Update pizza-003 to 80000 in pizza-list"
```

## Testing

```bash
# Test import
uv run python -c "from remote_seller_agents.mcp_server_products import list_product_tables; print(list_product_tables())"

# Run server
uv run python -m remote_seller_agents.mcp_server_products
```
