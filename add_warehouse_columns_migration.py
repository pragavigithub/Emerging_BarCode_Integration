#!/usr/bin/env python
"""
Database Migration: Add warehouse columns to inventory_transfers table
"""
import os
import sqlite3
import logging
from datetime import datetime

def find_database_file():
    """Find the SQLite database file"""
    possible_locations = [
        'instance/database.db',
        'instance/wms.db',
        'database.db',
        'wms.db'
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            print(f"Found database at: {location}")
            return location
    
    print("No database file found!")
    return None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in the table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def main():
    """Main migration function"""
    print("=" * 60)
    print("DATABASE MIGRATION: Adding warehouse columns")
    print("=" * 60)
    
    # Find database file
    db_path = find_database_file()
    if not db_path:
        print("❌ No database file found. Creating fresh database...")
        return
    
    # Create backup
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📁 Creating backup: {backup_path}")
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("✅ Backup created successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not create backup: {e}")
    
    # Connect to database
    print(f"🔗 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_transfers'")
        if not cursor.fetchone():
            print("❌ Table 'inventory_transfers' does not exist!")
            return
        
        print("✅ Table 'inventory_transfers' found")
        
        # Check and add from_warehouse column
        if not check_column_exists(cursor, 'inventory_transfers', 'from_warehouse'):
            print("➕ Adding 'from_warehouse' column...")
            cursor.execute("ALTER TABLE inventory_transfers ADD COLUMN from_warehouse VARCHAR(20)")
            print("✅ Column 'from_warehouse' added successfully")
        else:
            print("✅ Column 'from_warehouse' already exists")
        
        # Check and add to_warehouse column
        if not check_column_exists(cursor, 'inventory_transfers', 'to_warehouse'):
            print("➕ Adding 'to_warehouse' column...")
            cursor.execute("ALTER TABLE inventory_transfers ADD COLUMN to_warehouse VARCHAR(20)")
            print("✅ Column 'to_warehouse' added successfully")
        else:
            print("✅ Column 'to_warehouse' already exists")
        
        # Commit changes
        conn.commit()
        print("💾 Changes committed successfully")
        
        # Verify the columns were added
        cursor.execute("PRAGMA table_info(inventory_transfers)")
        columns = cursor.fetchall()
        print("\n📋 Current table schema:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        print("\n🎉 Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        print(f"📁 Database backup available at: {backup_path}")
        raise
        
    finally:
        conn.close()
        print("🔐 Database connection closed")

if __name__ == "__main__":
    main()