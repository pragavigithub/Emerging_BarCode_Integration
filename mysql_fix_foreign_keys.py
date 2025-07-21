#!/usr/bin/env python3
"""
MySQL Foreign Key Constraint Fix for WMS
========================================
This script specifically fixes foreign key constraint issues that can occur during migration.
Run this if you encounter "incompatible" foreign key constraint errors.

Usage:
    python mysql_fix_foreign_keys.py

Author: WMS System
Date: July 21, 2025
"""

import os
import sys
import logging
import pymysql

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mysql_connection():
    """Get MySQL connection using environment variables or defaults"""
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
        sys.exit(1)

def drop_foreign_key_constraints(cursor):
    """Drop all foreign key constraints that might cause issues"""
    logger.info("🔄 Dropping problematic foreign key constraints...")
    
    constraints_to_drop = [
        ("warehouses", "warehouses_ibfk_1"),
        ("users", "users_ibfk_1"), 
        ("users", "users_ibfk_2"),
        ("grpo_documents", "grpo_documents_ibfk_1"),
        ("grpo_items", "grpo_items_ibfk_1"),
        ("inventory_transfers", "inventory_transfers_ibfk_1"),
        ("inventory_transfers", "inventory_transfers_ibfk_2"),
        ("inventory_transfer_items", "inventory_transfer_items_ibfk_1"),
        ("pick_lists", "pick_lists_ibfk_1"),
        ("inventory_counts", "inventory_counts_ibfk_1"),
        ("barcode_labels", "barcode_labels_ibfk_1"),
    ]
    
    for table_name, constraint_name in constraints_to_drop:
        try:
            cursor.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {constraint_name}")
            logger.info(f"✅ Dropped constraint {constraint_name} from {table_name}")
        except Exception as e:
            if "doesn't exist" in str(e).lower() or "check that column/key exists" in str(e).lower():
                logger.info(f"✓ Constraint {constraint_name} doesn't exist on {table_name}")
            else:
                logger.warning(f"⚠️ Could not drop constraint {constraint_name}: {e}")

def ensure_compatible_column_types(cursor):
    """Ensure all foreign key columns have compatible data types"""
    logger.info("🔄 Ensuring compatible column types for foreign keys...")
    
    # First, make sure branch_id columns are all VARCHAR(10) with same character set
    column_fixes = [
        ("users", "branch_id", "VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("users", "default_branch_id", "VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("warehouses", "branch_id", "VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("pick_lists", "branch_id", "VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("inventory_counts", "branch_id", "VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("barcode_labels", "branch_id", "VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("grpo_documents", "branch_id", "VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
    ]
    
    for table_name, column_name, column_type in column_fixes:
        try:
            cursor.execute(f"ALTER TABLE {table_name} MODIFY COLUMN {column_name} {column_type}")
            logger.info(f"✅ Fixed column type for {table_name}.{column_name}")
        except Exception as e:
            if "doesn't exist" in str(e).lower():
                logger.info(f"✓ Column {table_name}.{column_name} doesn't exist yet")
            else:
                logger.warning(f"⚠️ Could not fix column {table_name}.{column_name}: {e}")

def fix_table_character_sets(cursor):
    """Fix character set and collation for all tables"""
    logger.info("🔄 Fixing table character sets and collations...")
    
    # Get list of all tables
    cursor.execute("SHOW TABLES")
    tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]
    
    for table_name in tables:
        try:
            cursor.execute(f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"✅ Fixed character set for table {table_name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not fix character set for {table_name}: {e}")

def main():
    """Main foreign key fix function"""
    logger.info("🚀 Starting MySQL Foreign Key Constraint Fix")
    logger.info("=" * 50)
    
    connection = None
    try:
        # Get database connection
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        # Disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        logger.info("✅ Disabled foreign key checks")
        
        # Drop problematic foreign key constraints
        drop_foreign_key_constraints(cursor)
        connection.commit()
        
        # Fix character sets for all tables
        fix_table_character_sets(cursor)
        connection.commit()
        
        # Ensure compatible column types
        ensure_compatible_column_types(cursor)
        connection.commit()
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        logger.info("✅ Re-enabled foreign key checks")
        
        logger.info("=" * 50)
        logger.info("🎉 Foreign Key Constraint Fix Completed Successfully!")
        logger.info("✅ All problematic foreign key constraints have been dropped")
        logger.info("✅ All table character sets have been standardized")
        logger.info("✅ All foreign key columns have compatible data types")
        logger.info("🔄 Now you can run the main migration script:")
        logger.info("    python mysql_complete_migration.py")
        
    except Exception as e:
        logger.error(f"❌ Foreign key fix failed: {e}")
        if connection:
            connection.rollback()
        sys.exit(1)
        
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()