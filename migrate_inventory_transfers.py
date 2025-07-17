#!/usr/bin/env python3
"""
Database Migration Script: Add QC Approval Columns to Inventory Transfers
This script adds the missing QC approval columns to inventory_transfers table for local development
Supports: SQLite, MySQL, PostgreSQL
"""

import sqlite3
import os
import sys
from datetime import datetime
import logging

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    sqlite_paths = [
        'instance/warehouse.db',
        'warehouse.db',
        'instance/app.db',
        'app.db',
        'database.db'
    ]
    
    for path in sqlite_paths:
        if os.path.exists(path):
            logger.info(f"Found SQLite database at: {path}")
            return sqlite3.connect(path), 'sqlite'
    
    # Create instance directory if it doesn't exist
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # Default to instance/warehouse.db
    return sqlite3.connect('instance/warehouse.db'), 'sqlite'

def check_column_exists(cursor, table_name, column_name, db_type):
    """Check if a column exists in the table"""
    if db_type == 'sqlite':
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return any(column[1] == column_name for column in columns)
    elif db_type == 'mysql':
        cursor.execute(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}' AND COLUMN_NAME = '{column_name}'
        """)
        return cursor.fetchone() is not None
    elif db_type == 'postgresql':
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        """)
        return cursor.fetchone() is not None
    return False

def check_table_exists(cursor, table_name, db_type):
    """Check if table exists"""
    if db_type == 'sqlite':
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
    elif db_type == 'mysql':
        cursor.execute(f"""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = '{table_name}'
        """)
    elif db_type == 'postgresql':
        cursor.execute(f"""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = '{table_name}'
        """)
    return cursor.fetchone() is not None

def add_column_if_not_exists(cursor, table_name, column_name, column_definition, db_type):
    """Add column if it doesn't exist"""
    if not check_column_exists(cursor, table_name, column_name, db_type):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            logger.info(f"✅ Added column {column_name} to {table_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding column {column_name} to {table_name}: {e}")
            return False
    else:
        logger.info(f"⏭️  Column {column_name} already exists in {table_name}")
        return True

def get_create_table_sql(db_type):
    """Get table creation SQL for different database types"""
    if db_type == 'sqlite':
        return {
            'inventory_transfers': """
                CREATE TABLE inventory_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_request_number VARCHAR(20) NOT NULL,
                    sap_document_number VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'draft',
                    user_id INTEGER NOT NULL,
                    qc_approver_id INTEGER,
                    qc_approved_at DATETIME,
                    qc_notes TEXT,
                    from_warehouse VARCHAR(20),
                    to_warehouse VARCHAR(20),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id)
                )
            """,
            'inventory_transfer_items': """
                CREATE TABLE inventory_transfer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inventory_transfer_id INTEGER NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200) NOT NULL,
                    quantity REAL NOT NULL,
                    unit_of_measure VARCHAR(10) NOT NULL,
                    from_bin VARCHAR(20) NOT NULL,
                    to_bin VARCHAR(20) NOT NULL,
                    batch_number VARCHAR(50),
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    qc_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id)
                )
            """
        }
    elif db_type == 'mysql':
        return {
            'inventory_transfers': """
                CREATE TABLE inventory_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_request_number VARCHAR(20) NOT NULL,
                    sap_document_number VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'draft',
                    user_id INT NOT NULL,
                    qc_approver_id INT,
                    qc_approved_at DATETIME,
                    qc_notes TEXT,
                    from_warehouse VARCHAR(20),
                    to_warehouse VARCHAR(20),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id)
                )
            """,
            'inventory_transfer_items': """
                CREATE TABLE inventory_transfer_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    inventory_transfer_id INT NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200) NOT NULL,
                    quantity DECIMAL(10,2) NOT NULL,
                    unit_of_measure VARCHAR(10) NOT NULL,
                    from_bin VARCHAR(20) NOT NULL,
                    to_bin VARCHAR(20) NOT NULL,
                    batch_number VARCHAR(50),
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    qc_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id)
                )
            """
        }
    elif db_type == 'postgresql':
        return {
            'inventory_transfers': """
                CREATE TABLE inventory_transfers (
                    id SERIAL PRIMARY KEY,
                    transfer_request_number VARCHAR(20) NOT NULL,
                    sap_document_number VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'draft',
                    user_id INTEGER NOT NULL,
                    qc_approver_id INTEGER,
                    qc_approved_at TIMESTAMP,
                    qc_notes TEXT,
                    from_warehouse VARCHAR(20),
                    to_warehouse VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id)
                )
            """,
            'inventory_transfer_items': """
                CREATE TABLE inventory_transfer_items (
                    id SERIAL PRIMARY KEY,
                    inventory_transfer_id INTEGER NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200) NOT NULL,
                    quantity DECIMAL(10,2) NOT NULL,
                    unit_of_measure VARCHAR(10) NOT NULL,
                    from_bin VARCHAR(20) NOT NULL,
                    to_bin VARCHAR(20) NOT NULL,
                    batch_number VARCHAR(50),
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    qc_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id)
                )
            """
        }

def main():
    """Main migration function"""
    logger.info("🚀 Starting Inventory Transfer Database Migration")
    logger.info("=" * 60)
    
    try:
        # Get database connection
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        logger.info(f"📊 Using {db_type.upper()} database")
        
        # Check if inventory_transfers table exists
        if not check_table_exists(cursor, 'inventory_transfers', db_type):
            logger.error("❌ inventory_transfers table does not exist!")
            logger.info("Creating inventory_transfers table...")
            
            # Create the table with all required columns
            table_sql = get_create_table_sql(db_type)
            cursor.execute(table_sql['inventory_transfers'])
            logger.info("✅ Created inventory_transfers table")
        else:
            logger.info("📋 inventory_transfers table exists, checking columns...")
            
            # Add missing columns for QC approval workflow
            migrations = [
                ('qc_approver_id', 'INTEGER' if db_type == 'sqlite' else 'INT'),
                ('qc_approved_at', 'DATETIME' if db_type != 'postgresql' else 'TIMESTAMP'),
                ('qc_notes', 'TEXT'),
                ('from_warehouse', 'VARCHAR(20)'),
                ('to_warehouse', 'VARCHAR(20)'),
                ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP' if db_type != 'postgresql' else 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            ]
            
            for column_name, column_definition in migrations:
                add_column_if_not_exists(cursor, 'inventory_transfers', column_name, column_definition, db_type)
        
        # Check if inventory_transfer_items table exists
        if not check_table_exists(cursor, 'inventory_transfer_items', db_type):
            logger.info("Creating inventory_transfer_items table...")
            table_sql = get_create_table_sql(db_type)
            cursor.execute(table_sql['inventory_transfer_items'])
            logger.info("✅ Created inventory_transfer_items table")
        else:
            # Add missing QC columns to items table
            item_migrations = [
                ('qc_status', 'VARCHAR(20) DEFAULT "pending"' if db_type == 'sqlite' else "VARCHAR(20) DEFAULT 'pending'"),
                ('qc_notes', 'TEXT')
            ]
            
            for column_name, column_definition in item_migrations:
                add_column_if_not_exists(cursor, 'inventory_transfer_items', column_name, column_definition, db_type)
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        logger.info("📊 Verifying migration results...")
        if db_type == 'sqlite':
            cursor.execute("PRAGMA table_info(inventory_transfers)")
            columns = cursor.fetchall()
            logger.info(f"inventory_transfers table now has {len(columns)} columns:")
            for column in columns:
                logger.info(f"  - {column[1]} ({column[2]})")
        else:
            logger.info("Migration completed for non-SQLite database")
        
        logger.info("=" * 60)
        logger.info("✅ Migration completed successfully!")
        logger.info("🎉 Inventory Transfer QC approval workflow is now ready!")
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()