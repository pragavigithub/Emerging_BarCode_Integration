#!/usr/bin/env python3
"""
Fix SQLite Schema - Add Missing Notes Column
This script adds the missing 'notes' column to the grpo_documents table in SQLite.
"""
import os
import sqlite3
import logging
from pathlib import Path

def find_sqlite_database():
    """Find the SQLite database file"""
    possible_paths = [
        'instance/database.db',
        'database.db',
        'wms.db',
        'app.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Check if instance directory exists
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    return 'instance/database.db'

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in the table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def add_missing_columns():
    """Add missing columns to SQLite database"""
    db_path = find_sqlite_database()
    print(f"Working with database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check and add notes column to grpo_documents
        if not check_column_exists(cursor, 'grpo_documents', 'notes'):
            print("Adding 'notes' column to grpo_documents table...")
            cursor.execute("ALTER TABLE grpo_documents ADD COLUMN notes TEXT")
            print("✓ Added 'notes' column to grpo_documents")
        else:
            print("✓ 'notes' column already exists in grpo_documents")
        
        # Check and add serial_number column to grpo_items if it doesn't exist
        if not check_column_exists(cursor, 'grpo_items', 'serial_number'):
            print("Adding 'serial_number' column to grpo_items table...")
            cursor.execute("ALTER TABLE grpo_items ADD COLUMN serial_number VARCHAR(50)")
            print("✓ Added 'serial_number' column to grpo_items")
        else:
            print("✓ 'serial_number' column already exists in grpo_items")
        
        conn.commit()
        print("\n✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def main():
    """Main function"""
    print("🔧 SQLite Schema Fix")
    print("=" * 50)
    
    if add_missing_columns():
        print("\n✅ Schema fix completed successfully!")
        print("You can now run your application without database errors.")
    else:
        print("\n❌ Schema fix failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()