#!/usr/bin/env python3
"""
Database Migration Script for WMS Application
Run this script to update your local database schema to match the latest version.
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_database_path():
    """Get the database path from environment or use default"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    # Default SQLite path for Flask applications
    return 'instance/database.db'

def backup_database(db_path):
    """Create a backup of the current database"""
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        
        # Copy the database file
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path
    return None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in the table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_grpo_documents(cursor):
    """Add missing columns to grpo_documents table"""
    migrations_applied = []
    
    # Check and add supplier_code column
    if not check_column_exists(cursor, 'grpo_documents', 'supplier_code'):
        cursor.execute('ALTER TABLE grpo_documents ADD COLUMN supplier_code VARCHAR(50)')
        migrations_applied.append('Added supplier_code column')
    
    # Check and add supplier_name column
    if not check_column_exists(cursor, 'grpo_documents', 'supplier_name'):
        cursor.execute('ALTER TABLE grpo_documents ADD COLUMN supplier_name VARCHAR(200)')
        migrations_applied.append('Added supplier_name column')
    
    # Check and add po_date column
    if not check_column_exists(cursor, 'grpo_documents', 'po_date'):
        cursor.execute('ALTER TABLE grpo_documents ADD COLUMN po_date DATETIME')
        migrations_applied.append('Added po_date column')
    
    # Check and add po_total column
    if not check_column_exists(cursor, 'grpo_documents', 'po_total'):
        cursor.execute('ALTER TABLE grpo_documents ADD COLUMN po_total FLOAT')
        migrations_applied.append('Added po_total column')
    
    # Check and add qc_user_id column
    if not check_column_exists(cursor, 'grpo_documents', 'qc_user_id'):
        cursor.execute('ALTER TABLE grpo_documents ADD COLUMN qc_user_id INTEGER')
        migrations_applied.append('Added qc_user_id column')
    
    # Check and add qc_notes column
    if not check_column_exists(cursor, 'grpo_documents', 'qc_notes'):
        cursor.execute('ALTER TABLE grpo_documents ADD COLUMN qc_notes TEXT')
        migrations_applied.append('Added qc_notes column')
    
    # Check and add draft_or_post column
    if not check_column_exists(cursor, 'grpo_documents', 'draft_or_post'):
        cursor.execute('ALTER TABLE grpo_documents ADD COLUMN draft_or_post VARCHAR(10) DEFAULT "draft"')
        migrations_applied.append('Added draft_or_post column')
    
    return migrations_applied

def migrate_grpo_items(cursor):
    """Add missing columns to grpo_items table"""
    migrations_applied = []
    
    # Check and add po_line_number column
    if not check_column_exists(cursor, 'grpo_items', 'po_line_number'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN po_line_number INTEGER')
        migrations_applied.append('Added po_line_number column')
    
    # Check and add po_quantity column
    if not check_column_exists(cursor, 'grpo_items', 'po_quantity'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN po_quantity FLOAT')
        migrations_applied.append('Added po_quantity column')
    
    # Check and add open_quantity column
    if not check_column_exists(cursor, 'grpo_items', 'open_quantity'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN open_quantity FLOAT')
        migrations_applied.append('Added open_quantity column')
    
    # Check and add unit_price column
    if not check_column_exists(cursor, 'grpo_items', 'unit_price'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN unit_price FLOAT')
        migrations_applied.append('Added unit_price column')
    
    # Check and add supplier_barcode column
    if not check_column_exists(cursor, 'grpo_items', 'supplier_barcode'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN supplier_barcode VARCHAR(100)')
        migrations_applied.append('Added supplier_barcode column')
    
    # Check and add generated_barcode column
    if not check_column_exists(cursor, 'grpo_items', 'generated_barcode'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN generated_barcode VARCHAR(100)')
        migrations_applied.append('Added generated_barcode column')
    
    # Check and add barcode_printed column
    if not check_column_exists(cursor, 'grpo_items', 'barcode_printed'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN barcode_printed BOOLEAN DEFAULT 0')
        migrations_applied.append('Added barcode_printed column')
    
    # Check and add qc_status column
    if not check_column_exists(cursor, 'grpo_items', 'qc_status'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN qc_status VARCHAR(20) DEFAULT "pending"')
        migrations_applied.append('Added qc_status column')
    
    # Check and add qc_notes column
    if not check_column_exists(cursor, 'grpo_items', 'qc_notes'):
        cursor.execute('ALTER TABLE grpo_items ADD COLUMN qc_notes TEXT')
        migrations_applied.append('Added qc_notes column')
    
    return migrations_applied

def migrate_inventory_transfers(cursor):
    """Add missing warehouse columns to inventory_transfers table"""
    migrations_applied = []
    
    # Check and add from_warehouse column
    if not check_column_exists(cursor, 'inventory_transfers', 'from_warehouse'):
        cursor.execute('ALTER TABLE inventory_transfers ADD COLUMN from_warehouse VARCHAR(20)')
        migrations_applied.append('Added from_warehouse column')
    
    # Check and add to_warehouse column
    if not check_column_exists(cursor, 'inventory_transfers', 'to_warehouse'):
        cursor.execute('ALTER TABLE inventory_transfers ADD COLUMN to_warehouse VARCHAR(20)')
        migrations_applied.append('Added to_warehouse column')
    
    return migrations_applied

def main():
    """Main migration function"""
    print("WMS Database Migration Tool")
    print("=" * 40)
    
    # Get database path
    db_path = get_database_path()
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Please make sure the database exists before running migration.")
        sys.exit(1)
    
    # Create backup
    backup_path = backup_database(db_path)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔄 Running migrations...")
        
        # Run migrations for grpo_documents
        grpo_doc_migrations = migrate_grpo_documents(cursor)
        
        # Run migrations for grpo_items  
        grpo_item_migrations = migrate_grpo_items(cursor)
        
        # Run migrations for inventory_transfers
        inventory_transfer_migrations = migrate_inventory_transfers(cursor)
        
        # Commit changes
        conn.commit()
        
        # Report results
        all_migrations = grpo_doc_migrations + grpo_item_migrations + inventory_transfer_migrations
        
        if all_migrations:
            print("\n✅ Migrations completed successfully!")
            print("\nApplied migrations:")
            for migration in all_migrations:
                print(f"  • {migration}")
        else:
            print("\n✅ Database is already up to date!")
        
        print(f"\n📊 Migration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if backup_path and os.path.exists(backup_path):
            print(f"You can restore from backup: {backup_path}")
        sys.exit(1)
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()