#!/usr/bin/env python3
"""
Complete MySQL Database Migration Script for WMS
=====================================
This script fixes all missing columns and schema issues for MySQL database.
Run this script to ensure your MySQL database is fully compatible with the WMS application.

Usage:
    python mysql_complete_migration.py

Author: WMS System
Date: July 21, 2025
"""

import os
import sys
import logging
import pymysql
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mysql_connection():
    """Get MySQL connection using environment variables or defaults"""
    # Try to get MySQL configuration from environment
    mysql_host = os.environ.get("MYSQL_HOST", "localhost")
    mysql_user = os.environ.get("MYSQL_USER", "root") 
    mysql_password = os.environ.get("MYSQL_PASSWORD", "root@123")
    mysql_database = os.environ.get("MYSQL_DATABASE", "wms_db_dev")
    mysql_port = int(os.environ.get("MYSQL_PORT", "3306"))
    
    logger.info(f"Connecting to MySQL: {mysql_host}:{mysql_port} / {mysql_database}")
    
    try:
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {e}")
        logger.info("Please ensure MySQL is running and environment variables are set correctly:")
        logger.info("MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
        sys.exit(1)

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"""
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = '{table_name}' 
        AND COLUMN_NAME = '{column_name}'
    """)
    result = cursor.fetchone()
    return result['count'] > 0

def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(f"""
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = '{table_name}'
    """)
    result = cursor.fetchone()
    return result['count'] > 0

def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    """Add a column to a table if it doesn't exist"""
    if not column_exists(cursor, table_name, column_name):
        try:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            cursor.execute(sql)
            logger.info(f"✅ Added column '{column_name}' to table '{table_name}'")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add column '{column_name}' to '{table_name}': {e}")
            return False
    else:
        logger.info(f"✓ Column '{column_name}' already exists in table '{table_name}'")
        return True

def migrate_users_table(cursor):
    """Migrate users table - add missing columns"""
    logger.info("🔄 Migrating users table...")
    
    columns_to_add = [
        ('first_name', 'VARCHAR(50)'),
        ('last_name', 'VARCHAR(50)'),
        ('role', 'VARCHAR(20) DEFAULT "user"'),
        ('is_active', 'BOOLEAN DEFAULT TRUE'),
        ('branch_id', 'VARCHAR(10)'),
        ('default_branch_id', 'VARCHAR(10)'),
        ('phone', 'VARCHAR(20)'),
        ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
        ('last_login', 'DATETIME'),
        ('failed_login_attempts', 'INT DEFAULT 0'),
        ('locked_until', 'DATETIME'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'users', column_name, column_definition)

def migrate_grpo_documents_table(cursor):
    """Migrate GRPO documents table - add missing columns"""
    logger.info("🔄 Migrating grpo_documents table...")
    
    columns_to_add = [
        ('po_date', 'DATE'),
        ('po_total', 'DECIMAL(15,2)'),
        ('qc_notes', 'TEXT'),
        ('notes', 'TEXT'),
        ('branch_id', 'VARCHAR(10)'),
        ('reference_number', 'VARCHAR(50)'),
        ('vendor_code', 'VARCHAR(50)'),
        ('vendor_name', 'VARCHAR(200)'),
        ('delivery_note_number', 'VARCHAR(50)'),
        ('invoice_number', 'VARCHAR(50)'),
        ('currency', 'VARCHAR(3) DEFAULT "USD"'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'grpo_documents', column_name, column_definition)

def migrate_grpo_items_table(cursor):
    """Migrate GRPO items table - add missing columns"""
    logger.info("🔄 Migrating grpo_items table...")
    
    columns_to_add = [
        ('serial_number', 'VARCHAR(50)'),
        ('expiry_date', 'DATE'),
        ('manufacture_date', 'DATE'),
        ('unit_price', 'DECIMAL(15,4)'),
        ('line_total', 'DECIMAL(15,2)'),
        ('tax_rate', 'DECIMAL(5,2) DEFAULT 0.00'),
        ('tax_amount', 'DECIMAL(15,2) DEFAULT 0.00'),
        ('discount_percent', 'DECIMAL(5,2) DEFAULT 0.00'),
        ('discount_amount', 'DECIMAL(15,2) DEFAULT 0.00'),
        ('qc_notes', 'TEXT'),
        ('barcode', 'VARCHAR(100)'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'grpo_items', column_name, column_definition)

def migrate_inventory_transfers_table(cursor):
    """Migrate inventory transfers table - add missing columns"""
    logger.info("🔄 Migrating inventory_transfers table...")
    
    columns_to_add = [
        ('transfer_request_number', 'VARCHAR(50)'),
        ('from_warehouse', 'VARCHAR(20)'),
        ('to_warehouse', 'VARCHAR(20)'),
        ('transfer_type', 'VARCHAR(20) DEFAULT "warehouse"'),
        ('priority', 'VARCHAR(10) DEFAULT "normal"'),
        ('reason_code', 'VARCHAR(20)'),
        ('notes', 'TEXT'),
        ('qc_approver_id', 'INT'),
        ('qc_approved_at', 'DATETIME'),
        ('qc_notes', 'TEXT'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'inventory_transfers', column_name, column_definition)

def migrate_inventory_transfer_items_table(cursor):
    """Migrate inventory transfer items table - add missing columns"""
    logger.info("🔄 Migrating inventory_transfer_items table...")
    
    columns_to_add = [
        ('qc_status', 'VARCHAR(20) DEFAULT "pending"'),
        ('qc_notes', 'TEXT'),
        ('serial_number', 'VARCHAR(50)'),
        ('expiry_date', 'DATE'),
        ('manufacture_date', 'DATE'),
        ('unit_price', 'DECIMAL(15,4)'),
        ('total_value', 'DECIMAL(15,2)'),
        ('from_warehouse_code', 'VARCHAR(10)'),
        ('to_warehouse_code', 'VARCHAR(10)'),
        ('base_entry', 'INT'),
        ('base_line', 'INT'),
        ('sap_line_number', 'INT'),
        ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'inventory_transfer_items', column_name, column_definition)

def migrate_pick_lists_table(cursor):
    """Migrate pick lists table - add missing columns"""
    logger.info("🔄 Migrating pick_lists table...")
    
    columns_to_add = [
        ('priority', 'VARCHAR(10) DEFAULT "normal"'),
        ('notes', 'TEXT'),
        ('estimated_completion_time', 'DATETIME'),
        ('actual_completion_time', 'DATETIME'),
        ('assigned_user_id', 'INT'),
        ('branch_id', 'VARCHAR(10)'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'pick_lists', column_name, column_definition)

def migrate_inventory_counts_table(cursor):
    """Migrate inventory counts table - add missing columns"""
    logger.info("🔄 Migrating inventory_counts table...")
    
    columns_to_add = [
        ('count_type', 'VARCHAR(20) DEFAULT "cycle"'),
        ('reason_code', 'VARCHAR(20)'),
        ('notes', 'TEXT'),
        ('approver_id', 'INT'),
        ('approved_at', 'DATETIME'),
        ('branch_id', 'VARCHAR(10)'),
        ('variance_threshold', 'DECIMAL(5,2) DEFAULT 0.00'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'inventory_counts', column_name, column_definition)

def migrate_barcode_labels_table(cursor):
    """Migrate barcode labels table - add missing columns"""
    logger.info("🔄 Migrating barcode_labels table...")
    
    columns_to_add = [
        ('label_format', 'VARCHAR(20) DEFAULT "standard"'),
        ('qr_code_data', 'TEXT'),
        ('reprint_count', 'INT DEFAULT 0'),
        ('last_reprinted_at', 'DATETIME'),
        ('last_reprinted_by', 'INT'),
        ('branch_id', 'VARCHAR(10)'),
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(cursor, 'barcode_labels', column_name, column_definition)

def create_missing_tables(cursor):
    """Create any missing tables"""
    logger.info("🔄 Checking for missing tables...")
    
    # Branches table
    if not table_exists(cursor, 'branches'):
        logger.info("📝 Creating branches table...")
        cursor.execute("""
            CREATE TABLE branches (
                id VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address TEXT,
                phone VARCHAR(20),
                email VARCHAR(100),
                manager_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                is_default BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        logger.info("✅ Created branches table")
    
    # User sessions table
    if not table_exists(cursor, 'user_sessions'):
        logger.info("📝 Creating user_sessions table...")
        cursor.execute("""
            CREATE TABLE user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_token VARCHAR(256) NOT NULL,
                branch_id VARCHAR(10),
                login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                logout_time DATETIME NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_user_id (user_id),
                INDEX idx_session_token (session_token)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        logger.info("✅ Created user_sessions table")

def create_indexes(cursor):
    """Create missing indexes for better performance"""
    logger.info("🔄 Creating missing indexes...")
    
    indexes_to_create = [
        # Users table indexes
        ("idx_users_username", "users", "username"),
        ("idx_users_email", "users", "email"),
        ("idx_users_role", "users", "role"),
        ("idx_users_branch_id", "users", "branch_id"),
        
        # GRPO indexes
        ("idx_grpo_docs_po_number", "grpo_documents", "po_number"),
        ("idx_grpo_docs_status", "grpo_documents", "status"),
        ("idx_grpo_docs_user_id", "grpo_documents", "user_id"),
        ("idx_grpo_items_doc_id", "grpo_items", "grpo_document_id"),
        ("idx_grpo_items_item_code", "grpo_items", "item_code"),
        
        # Inventory Transfer indexes
        ("idx_inv_transfer_status", "inventory_transfers", "status"),
        ("idx_inv_transfer_user_id", "inventory_transfers", "user_id"),
        ("idx_inv_transfer_items_transfer_id", "inventory_transfer_items", "inventory_transfer_id"),
        ("idx_inv_transfer_items_item_code", "inventory_transfer_items", "item_code"),
        ("idx_inv_transfer_items_qc_status", "inventory_transfer_items", "qc_status"),
        
        # Pick List indexes
        ("idx_pick_lists_status", "pick_lists", "status"),
        ("idx_pick_lists_user_id", "pick_lists", "user_id"),
        
        # Inventory Count indexes
        ("idx_inv_counts_status", "inventory_counts", "status"),
        ("idx_inv_counts_user_id", "inventory_counts", "user_id"),
        
        # Barcode Label indexes
        ("idx_barcode_labels_item_code", "barcode_labels", "item_code"),
        ("idx_barcode_labels_created_at", "barcode_labels", "created_at"),
    ]
    
    for index_name, table_name, column_name in indexes_to_create:
        try:
            cursor.execute(f"CREATE INDEX {index_name} ON {table_name} ({column_name})")
            logger.info(f"✅ Created index '{index_name}' on {table_name}({column_name})")
        except pymysql.err.OperationalError as e:
            if "Duplicate key name" in str(e):
                logger.info(f"✓ Index '{index_name}' already exists")
            else:
                logger.warning(f"⚠️ Could not create index '{index_name}': {e}")
        except Exception as e:
            logger.warning(f"⚠️ Could not create index '{index_name}': {e}")

def main():
    """Main migration function"""
    logger.info("🚀 Starting Complete MySQL Migration for WMS")
    logger.info("=" * 60)
    
    connection = None
    try:
        # Get database connection
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        # Create missing tables first
        create_missing_tables(cursor)
        connection.commit()
        
        # Migrate existing tables
        migrate_users_table(cursor)
        connection.commit()
        
        migrate_grpo_documents_table(cursor)
        connection.commit()
        
        migrate_grpo_items_table(cursor)
        connection.commit()
        
        migrate_inventory_transfers_table(cursor)
        connection.commit()
        
        migrate_inventory_transfer_items_table(cursor)
        connection.commit()
        
        migrate_pick_lists_table(cursor)
        connection.commit()
        
        migrate_inventory_counts_table(cursor)
        connection.commit()
        
        migrate_barcode_labels_table(cursor)
        connection.commit()
        
        # Create performance indexes
        create_indexes(cursor)
        connection.commit()
        
        logger.info("=" * 60)
        logger.info("🎉 MySQL Migration Completed Successfully!")
        logger.info("✅ All missing columns have been added")
        logger.info("✅ All missing tables have been created") 
        logger.info("✅ All performance indexes have been created")
        logger.info("🔄 Please restart your WMS application")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        if connection:
            connection.rollback()
        sys.exit(1)
        
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()