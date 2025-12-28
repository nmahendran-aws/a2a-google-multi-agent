#!/usr/bin/env python3
"""
Cloud SQL Database Seeding Script
Seeds burger menu data into Cloud SQL database.

Supports both MySQL and PostgreSQL.
Configure via environment variables or .env file.
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DB_TYPE = os.getenv("CLOUDSQL_DB_TYPE", "mysql")  # postgresql or mysql
DB_NAME = os.getenv("CLOUDSQL_DB_NAME", "agentic-db")
DB_USER = os.getenv("CLOUDSQL_USER", "agentic-db")
DB_PASSWORD = os.getenv("CLOUDSQL_PASSWORD", "")
DB_HOST = os.getenv("CLOUDSQL_HOST", "localhost")
DB_PORT = os.getenv("CLOUDSQL_PORT", "5432" if DB_TYPE == "postgresql" else "3306")
INSTANCE_CONNECTION_NAME = os.getenv("CLOUDSQL_INSTANCE_CONNECTION_NAME")  # For Cloud SQL Connector

# Data to seed
BURGER_PRODUCTS = [
    ("burger-001", "Classic Cheeseburger", "85000", "IDR"),
    ("burger-002", "Double Cheeseburger", "110000", "IDR"),
    ("burger-003", "Spicy Chicken Burger", "80000", "IDR"),
    ("burger-004", "Spicy Cajun Burger", "85000", "IDR"),
]


def get_connection():
    """Get database connection based on configuration."""
    if INSTANCE_CONNECTION_NAME:
        # Use Cloud SQL Python Connector
        try:
            from google.cloud.sql.connector import Connector
            
            connector = Connector()
            
            def getconn():
                return connector.connect(
                    INSTANCE_CONNECTION_NAME,
                    "pg8000" if DB_TYPE == "postgresql" else "pymysql",
                    user=DB_USER,
                    password=DB_PASSWORD,
                    db=DB_NAME,
                )
            
            return getconn()
        except ImportError:
            print("ERROR: cloud-sql-python-connector not installed.")
            print("Install with: pip install cloud-sql-python-connector")
            if DB_TYPE == "postgresql":
                print("Also install: pip install pg8000")
            else:
                print("Also install: pip install pymysql")
            sys.exit(1)
    else:
        # Use direct connection
        if DB_TYPE == "postgresql":
            try:
                import psycopg2
                return psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                )
            except ImportError:
                print("ERROR: psycopg2 not installed.")
                print("Install with: pip install psycopg2-binary")
                sys.exit(1)
        else:  # mysql
            try:
                import pymysql
                return pymysql.connect(
                    host=DB_HOST,
                    port=int(DB_PORT),
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                )
            except ImportError:
                print("ERROR: pymysql not installed.")
                print("Install with: pip install pymysql")
                sys.exit(1)


def create_database_if_not_exists(cursor):
    """Create database if it doesn't exist (PostgreSQL only handles this differently)."""
    # For Cloud SQL Connector, we need to handle database creation differently
    # We should connect to the default database first, create our database, then reconnect
    pass  # This will be handled in main()


def ensure_database_exists():
    """Ensure the target database exists, creating it if necessary."""
    if INSTANCE_CONNECTION_NAME:
        # Using Cloud SQL Connector - connect to default DB first
        try:
            from google.cloud.sql.connector import Connector
            
            connector = Connector()
            
            # Connect to default database (mysql or postgres)
            default_db = "mysql" if DB_TYPE == "mysql" else "postgres"
            
            def getconn():
                return connector.connect(
                    INSTANCE_CONNECTION_NAME,
                    "pg8000" if DB_TYPE == "postgresql" else "pymysql",
                    user=DB_USER,
                    password=DB_PASSWORD,
                    db=default_db,
                )
            
            conn = getconn()
            cursor = conn.cursor()
            
            # Check if database exists and create if not
            if DB_TYPE == "mysql":
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
                print(f"✓ Database '{DB_NAME}' created/verified")
            else:  # postgresql
                cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
                if not cursor.fetchone():
                    cursor.execute(f"CREATE DATABASE \"{DB_NAME}\"")
                    print(f"✓ Database '{DB_NAME}' created")
                else:
                    print(f"✓ Database '{DB_NAME}' exists")
            
            cursor.close()
            conn.close()
            connector.close()
            
        except Exception as e:
            print(f"Warning: Could not verify/create database: {e}")
            print("Proceeding anyway...")
    else:
        # Direct connection - database creation will happen in main flow
        pass


def create_table(cursor):
    """Create product-list table if it doesn't exist."""
    if DB_TYPE == "postgresql":
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS "product-list" (
            "itemId" VARCHAR(50) PRIMARY KEY,
            "ItemName" VARCHAR(255) NOT NULL,
            "Price" VARCHAR(50) NOT NULL,
            "CurrencyType" VARCHAR(10) NOT NULL
        )
        """
    else:  # mysql
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS `product-list` (
            `itemId` VARCHAR(50) PRIMARY KEY,
            `ItemName` VARCHAR(255) NOT NULL,
            `Price` VARCHAR(50) NOT NULL,
            `CurrencyType` VARCHAR(10) NOT NULL
        )
        """
    
    cursor.execute(create_table_sql)
    print("✓ Table 'product-list' created/verified")


def seed_data(cursor, conn):
    """Insert burger menu data."""
    if DB_TYPE == "postgresql":
        insert_sql = """
        INSERT INTO "product-list" ("itemId", "ItemName", "Price", "CurrencyType")
        VALUES (%s, %s, %s, %s)
        ON CONFLICT ("itemId") DO UPDATE SET
            "ItemName" = EXCLUDED."ItemName",
            "Price" = EXCLUDED."Price",
            "CurrencyType" = EXCLUDED."CurrencyType"
        """
    else:  # mysql
        insert_sql = """
        INSERT INTO `product-list` (`itemId`, `ItemName`, `Price`, `CurrencyType`)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `ItemName` = VALUES(`ItemName`),
            `Price` = VALUES(`Price`),
            `CurrencyType` = VALUES(`CurrencyType`)
        """
    
    for product in BURGER_PRODUCTS:
        cursor.execute(insert_sql, product)
        print(f"✓ Inserted: {product[1]} - {product[3]} {product[2]}")
    
    conn.commit()
    print(f"\n✓ Successfully seeded {len(BURGER_PRODUCTS)} products")


def verify_data(cursor):
    """Verify inserted data."""
    if DB_TYPE == "postgresql":
        cursor.execute('SELECT * FROM "product-list" ORDER BY "itemId"')
    else:
        cursor.execute('SELECT * FROM `product-list` ORDER BY `itemId`')
    
    rows = cursor.fetchall()
    print(f"\n📊 Current data in product-list table:")
    print("-" * 80)
    for row in rows:
        print(f"  {row[0]}: {row[1]} - {row[3]} {row[2]}")
    print("-" * 80)


def main():
    """Main seeding logic."""
    print("=" * 80)
    print("Cloud SQL Database Seeding Script")
    print("=" * 80)
    print(f"Database Type: {DB_TYPE}")
    print(f"Database Name: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    
    if INSTANCE_CONNECTION_NAME:
        print(f"Instance: {INSTANCE_CONNECTION_NAME}")
    
    print("=" * 80)
    print()
    
    try:
        # Ensure database exists (especially important for Cloud SQL Connector)
        ensure_database_exists()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # For MySQL, create database if needed
        if DB_TYPE == "mysql":
            create_database_if_not_exists(cursor)
        
        # Create table
        create_table(cursor)
        
        # Seed data
        seed_data(cursor, conn)
        
        # Verify
        verify_data(cursor)
        
        cursor.close()
        conn.close()
        
        print("\n✅ Seeding completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
