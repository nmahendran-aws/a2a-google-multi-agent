# Cloud SQL Seeding Guide

## Overview
The `seed_cloudsql.py` script creates a database schema and populates it with burger menu data.

## Prerequisites

### 1. Install Dependencies

**For PostgreSQL:**
```bash
pip install psycopg2-binary python-dotenv
```

**For MySQL:**
```bash
pip install pymysql python-dotenv
```

**For Cloud SQL Connector (recommended for production):**
```bash
pip install cloud-sql-python-connector pg8000  # For PostgreSQL
# OR
pip install cloud-sql-python-connector pymysql  # For MySQL
```

### 2. Configure Environment

Copy the example configuration:
```bash
cp .env.cloudsql.example .env
```

Edit `.env` with your Cloud SQL details.

## Usage

### Local Development (Direct Connection)
```bash
# Set up .env with CLOUDSQL_HOST=localhost
python seed_cloudsql.py
```

### Production (Cloud SQL Connector)
```bash
# Set up .env with CLOUDSQL_INSTANCE_CONNECTION_NAME
python seed_cloudsql.py
```

## Database Schema

### Table: product-list
| Column | Type | Constraints |
|--------|------|-------------|
| itemId | VARCHAR(50) | PRIMARY KEY |
| ItemName | VARCHAR(255) | NOT NULL |
| Price | VARCHAR(50) | NOT NULL |
| CurrencyType | VARCHAR(10) | NOT NULL |

### Sample Data
```
burger-001: Classic Cheeseburger - IDR 85000
burger-002: Double Cheeseburger - IDR 110000
burger-003: Spicy Chicken Burger - IDR 80000
burger-004: Spicy Cajun Burger - IDR 85000
```

## Features
- ✅ Supports both MySQL and PostgreSQL
- ✅ Upsert logic (updates existing records)
- ✅ Environment-based configuration
- ✅ Cloud SQL Connector support
- ✅ Data verification after seeding

## Troubleshooting

**Connection Error:**
- Verify your Cloud SQL instance is running
- Check firewall rules allow your IP
- Ensure credentials are correct

**Module Not Found:**
- Install the required database driver (see Prerequisites)

**Permission Denied:**
- Verify database user has CREATE and INSERT permissions
