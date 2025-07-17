#!/usr/bin/env python3
"""
Database Migration Script: Add QC Approval Columns to Inventory Transfers
This script adds the missing QC approval columns to inventory_transfers table for local development
"""

import sqlite3
import os
import sys
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_database_file():
    """Find the SQLite database file"""
    possible_paths = [
        'instance/warehouse.db',
        'warehouse.db',
        'instance/app.db',
        'app.db',
        'database.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found database at: {path}")
            return path
    
    # Create instance directory if it doesn't exist
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # Default to instance/warehouse.db
    return 'instance/warehouse.db'

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in the table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(column[1] == column_name for column in columns)

def check_table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    """Add column if it doesn't exist"""
    if not check_column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            logger.info(f"✅ Added column {column_name} to {table_name}")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ Error adding column {column_name} to {table_name}: {e}")
            return False
    else:
        logger.info(f"⏭️  Column {column_name} already exists in {table_name}")
        return True

def main():
    """Main migration function"""
    logger.info("🚀 Starting Inventory Transfer Database Migration")
    logger.info("=" * 60)
    
    # Find database file
    db_path = find_database_file()
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if inventory_transfers table exists
        if not check_table_exists(cursor, 'inventory_transfers'):
            logger.error("❌ inventory_transfers table does not exist!")
            logger.info("Creating inventory_transfers table...")
            
            # Create the table with all required columns
            cursor.execute("""
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
            """)
            logger.info("✅ Created inventory_transfers table")
        else:
            logger.info("📋 inventory_transfers table exists, checking columns...")
            
            # Add missing columns for QC approval workflow
            migrations = [
                ('qc_approver_id', 'INTEGER'),
                ('qc_approved_at', 'DATETIME'),
                ('qc_notes', 'TEXT'),
                ('from_warehouse', 'VARCHAR(20)'),
                ('to_warehouse', 'VARCHAR(20)'),
                ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]
            
            for column_name, column_definition in migrations:
                add_column_if_not_exists(cursor, 'inventory_transfers', column_name, column_definition)
        
        # Check if inventory_transfer_items table exists
        if not check_table_exists(cursor, 'inventory_transfer_items'):
            logger.info("Creating inventory_transfer_items table...")
            cursor.execute("""
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
            """)
            logger.info("✅ Created inventory_transfer_items table")
        else:
            # Add missing QC columns to items table
            item_migrations = [
                ('qc_status', 'VARCHAR(20) DEFAULT "pending"'),
                ('qc_notes', 'TEXT')
            ]
            
            for column_name, column_definition in item_migrations:
                add_column_if_not_exists(cursor, 'inventory_transfer_items', column_name, column_definition)
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        logger.info("📊 Verifying migration results...")
        cursor.execute("PRAGMA table_info(inventory_transfers)")
        columns = cursor.fetchall()
        logger.info(f"inventory_transfers table now has {len(columns)} columns:")
        for column in columns:
            logger.info(f"  - {column[1]} ({column[2]})")
        
        logger.info("=" * 60)
        logger.info("✅ Migration completed successfully!")
        logger.info("🎉 Inventory Transfer QC approval workflow is now ready!")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()