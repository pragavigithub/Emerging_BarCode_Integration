#!/usr/bin/env python3
"""
Quick Database Fix Script
Automatically detects your database type and adds missing warehouse columns
"""
import os
import sys
import sqlite3
from datetime import datetime

def find_and_fix_database():
    """Find database and add missing columns"""
    print("🔧 WMS Database Quick Fix")
    print("=" * 50)
    
    # Check for SQLite database
    sqlite_paths = [
        'instance/database.db',
        'instance/wms.db', 
        'database.db',
        'wms.db'
    ]
    
    sqlite_db = None
    for path in sqlite_paths:
        if os.path.exists(path):
            sqlite_db = path
            break
    
    if sqlite_db:
        print(f"📁 Found SQLite database: {sqlite_db}")
        fix_sqlite_database(sqlite_db)
        return True
    
    # Check environment for other database types
    if os.environ.get('DATABASE_URL'):
        print("🐘 PostgreSQL database detected from environment")
        print("✅ PostgreSQL database should already have correct schema")
        return True
    
    if os.environ.get('MYSQL_HOST'):
        print("🐬 MySQL database detected from environment")
        print("💡 Run: python migrate_database_mysql.py")
        return True
    
    print("❌ No database found!")
    print("💡 Create database by running: python main.py")
    return False

def fix_sqlite_database(db_path):
    """Fix SQLite database by adding missing columns"""
    try:
        # Create backup
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"💾 Backup created: {backup_path}")
        
        # Connect and fix
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_transfers'")
        if not cursor.fetchone():
            print("❌ Table 'inventory_transfers' doesn't exist")
            print("💡 Run the application first to create tables: python main.py")
            return False
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(inventory_transfers)")
        columns = [row[1] for row in cursor.fetchall()]
        
        changes_made = []
        
        # Add from_warehouse column if missing
        if 'from_warehouse' not in columns:
            cursor.execute("ALTER TABLE inventory_transfers ADD COLUMN from_warehouse VARCHAR(20)")
            changes_made.append("from_warehouse")
            print("✅ Added from_warehouse column")
        else:
            print("✅ from_warehouse column already exists")
        
        # Add to_warehouse column if missing  
        if 'to_warehouse' not in columns:
            cursor.execute("ALTER TABLE inventory_transfers ADD COLUMN to_warehouse VARCHAR(20)")
            changes_made.append("to_warehouse")
            print("✅ Added to_warehouse column")
        else:
            print("✅ to_warehouse column already exists")
        
        if changes_made:
            conn.commit()
            print(f"\n🎉 Successfully added {len(changes_made)} column(s)")
            print("🔄 Please restart your application")
        else:
            print("\n✅ Database is already up to date!")
        
        # Show final schema
        cursor.execute("PRAGMA table_info(inventory_transfers)")
        columns = cursor.fetchall()
        print("\n📋 Current inventory_transfers schema:")
        for col in columns:
            print(f"   • {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        print(f"💾 Restore from backup: {backup_path}")
        return False

if __name__ == "__main__":
    success = find_and_fix_database()
    if success:
        print("\n🚀 Database fix completed!")
        print("🔄 Restart your application to apply changes")
    else:
        print("\n❌ Database fix failed")
        print("💡 Try running: python main.py (to create tables)")
        sys.exit(1)