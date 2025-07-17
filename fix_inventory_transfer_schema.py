#!/usr/bin/env python3
"""
Quick Fix Script: Inventory Transfer Schema Issue
This script automatically detects and fixes the missing QC approval columns
"""

import os
import sqlite3
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_inventory_transfer_schema():
    """Fix the inventory transfer schema for local development"""
    
    # Find database file
    db_paths = ['instance/warehouse.db', 'warehouse.db', 'instance/app.db', 'app.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        logger.error("No database file found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add missing columns
        columns_to_add = [
            ('qc_approver_id', 'INTEGER'),
            ('qc_approved_at', 'DATETIME'),
            ('qc_notes', 'TEXT'),
            ('from_warehouse', 'VARCHAR(20)'),
            ('to_warehouse', 'VARCHAR(20)')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE inventory_transfers ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added column {column_name}")
            except sqlite3.Error as e:
                if "duplicate column name" in str(e):
                    logger.info(f"Column {column_name} already exists")
                else:
                    logger.error(f"Error adding {column_name}: {e}")
        
        # Add QC columns to items table
        item_columns = [
            ('qc_status', 'VARCHAR(20) DEFAULT "pending"'),
            ('qc_notes', 'TEXT')
        ]
        
        for column_name, column_type in item_columns:
            try:
                cursor.execute(f"ALTER TABLE inventory_transfer_items ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added column {column_name} to items table")
            except sqlite3.Error as e:
                if "duplicate column name" in str(e):
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