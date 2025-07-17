#!/usr/bin/env python3
"""
Quick Fix Script: Inventory Transfer Schema Issue
This script automatically detects and fixes the missing QC approval columns
Supports: SQLite, MySQL, PostgreSQL
"""

import os
import sqlite3
import logging
from datetime import datetime

# Try to import MySQL and PostgreSQL connectors
try:
    import pymysql
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection based on environment variables"""
    # Check for MySQL configuration
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_user = os.getenv('MYSQL_USER')
    mysql_password = os.getenv('MYSQL_PASSWORD')
    mysql_database = os.getenv('MYSQL_DATABASE')
    
    # Check for PostgreSQL configuration
    database_url = os.getenv('DATABASE_URL')
    
    if mysql_user and mysql_password and mysql_database and MYSQL_AVAILABLE:
        logger.info("Using MySQL database")
        try:
            import pymysql
            connection = pymysql.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                charset='utf8mb4'
            )
            return connection, 'mysql'
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            try:
                import mysql.connector
                connection = mysql.connector.connect(
                    host=mysql_host,
                    user=mysql_user,
                    password=mysql_password,
                    database=mysql_database
                )
                return connection, 'mysql'
            except Exception as e2:
                logger.error(f"MySQL connector also failed: {e2}")
    
    elif database_url and POSTGRESQL_AVAILABLE:
        logger.info("Using PostgreSQL database")
        try:
            import psycopg2
            connection = psycopg2.connect(database_url)
            return connection, 'postgresql'
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
    
    # Fallback to SQLite
    logger.info("Using SQLite database")
    sqlite_paths = ['instance/warehouse.db', 'warehouse.db', 'instance/app.db', 'app.db']
    
    for path in sqlite_paths:
        if os.path.exists(path):
            logger.info(f"Found SQLite database at: {path}")
            return sqlite3.connect(path), 'sqlite'
    
    logger.error("No database file found!")
    return None, None

def fix_inventory_transfer_schema():
    """Fix the inventory transfer schema for local development"""
    
    try:
        conn, db_type = get_database_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        logger.info(f"Using {db_type.upper()} database")
        
        # Add missing columns based on database type
        if db_type == 'mysql':
            columns_to_add = [
                ('qc_approver_id', 'INT'),
                ('qc_approved_at', 'DATETIME'),
                ('qc_notes', 'TEXT'),
                ('from_warehouse', 'VARCHAR(20)'),
                ('to_warehouse', 'VARCHAR(20)')
            ]
            
            item_columns = [
                ('qc_status', "VARCHAR(20) DEFAULT 'pending'"),
                ('qc_notes', 'TEXT')
            ]
            
        elif db_type == 'postgresql':
            columns_to_add = [
                ('qc_approver_id', 'INTEGER'),
                ('qc_approved_at', 'TIMESTAMP'),
                ('qc_notes', 'TEXT'),
                ('from_warehouse', 'VARCHAR(20)'),
                ('to_warehouse', 'VARCHAR(20)')
            ]
            
            item_columns = [
                ('qc_status', "VARCHAR(20) DEFAULT 'pending'"),
                ('qc_notes', 'TEXT')
            ]
        
        else:  # SQLite
            columns_to_add = [
                ('qc_approver_id', 'INTEGER'),
                ('qc_approved_at', 'DATETIME'),
                ('qc_notes', 'TEXT'),
                ('from_warehouse', 'VARCHAR(20)'),
                ('to_warehouse', 'VARCHAR(20)')
            ]
            
            item_columns = [
                ('qc_status', 'VARCHAR(20) DEFAULT "pending"'),
                ('qc_notes', 'TEXT')
            ]
        
        # Add columns to inventory_transfers table
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE inventory_transfers ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added column {column_name}")
            except Exception as e:
                if "duplicate column name" in str(e) or "already exists" in str(e) or "Duplicate column name" in str(e):
                    logger.info(f"Column {column_name} already exists")
                else:
                    logger.error(f"Error adding {column_name}: {e}")
        
        # Add QC columns to items table
        for column_name, column_type in item_columns:
            try:
                cursor.execute(f"ALTER TABLE inventory_transfer_items ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added column {column_name} to items table")
            except Exception as e:
                if "duplicate column name" in str(e) or "already exists" in str(e) or "Duplicate column name" in str(e):
                    logger.info(f"Column {column_name} already exists in items table")
                else:
                    logger.error(f"Error adding {column_name} to items: {e}")
        
        conn.commit()
        conn.close()
        logger.info("✅ Schema fix completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing schema: {e}")
        return False

if __name__ == "__main__":
    fix_inventory_transfer_schema()