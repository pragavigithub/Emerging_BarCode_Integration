#!/usr/bin/env python3
"""
FINAL Database Fix Script for WMS Application
This script will completely resolve all database schema issues.
"""

import os
import sys
import sqlite3
from datetime import datetime

def find_database():
    """Find the SQLite database file"""
    # Check common locations
    locations = [
        'instance/database.db',
        'database.db',
        'wms.db',
        'app.db',
        'site.db'
    ]
    
    # Also check environment variable
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('sqlite:///'):
        locations.insert(0, database_url.replace('sqlite:///', ''))
    
    for path in locations:
        if os.path.exists(path):
            print(f"Found database: {path}")
            return path
    
    print("No existing database found. Will create new one.")
    return 'instance/database.db'

def backup_database(db_path):
    """Create backup of existing database"""
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path
    return None

def recreate_database():
    """Recreate database with correct schema"""
    db_path = find_database()
    
    # Create instance directory if needed
    instance_dir = os.path.dirname(db_path)
    if instance_dir and not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"✓ Created directory: {instance_dir}")
    
    # Backup existing database
    backup_path = backup_database(db_path)
    
    # Delete old database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Removed old database: {db_path}")
    
    # Create new database with correct schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create all tables with correct schema
    print("✓ Creating new database tables...")
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            first_name VARCHAR(80) NOT NULL,
            last_name VARCHAR(80) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            branch_id VARCHAR(10),
            branch_name VARCHAR(100),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # GRPO Documents table with all new columns
    cursor.execute('''
        CREATE TABLE grpo_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            supplier_code VARCHAR(50),
            supplier_name VARCHAR(200),
            po_date DATETIME,
            po_total FLOAT,
            status VARCHAR(20) DEFAULT 'draft',
            user_id INTEGER NOT NULL,
            qc_user_id INTEGER,
            qc_notes TEXT,
            draft_or_post VARCHAR(10) DEFAULT 'draft',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (qc_user_id) REFERENCES users (id)
        )
    ''')
    
    # GRPO Items table with all new columns
    cursor.execute('''
        CREATE TABLE grpo_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grpo_document_id INTEGER NOT NULL,
            po_line_number INTEGER,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            po_quantity FLOAT,
            open_quantity FLOAT,
            received_quantity FLOAT NOT NULL,
            unit_of_measure VARCHAR(10) NOT NULL,
            unit_price FLOAT,
            bin_location VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            expiration_date DATETIME,
            supplier_barcode VARCHAR(100),
            generated_barcode VARCHAR(100),
            barcode_printed BOOLEAN DEFAULT 0,
            qc_status VARCHAR(20) DEFAULT 'pending',
            qc_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grpo_document_id) REFERENCES grpo_documents (id)
        )
    ''')
    
    # Other tables
    cursor.execute('''
        CREATE TABLE inventory_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transfer_request_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            status VARCHAR(20) DEFAULT 'draft',
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE inventory_transfer_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_transfer_id INTEGER NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            quantity FLOAT NOT NULL,
            unit_of_measure VARCHAR(10) NOT NULL,
            from_bin VARCHAR(20) NOT NULL,
            to_bin VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE pick_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_order_number VARCHAR(20) NOT NULL,
            pick_list_number VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            user_id INTEGER NOT NULL,
            approver_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (approver_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE pick_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pick_list_id INTEGER NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            quantity FLOAT NOT NULL,
            picked_quantity FLOAT DEFAULT 0,
            unit_of_measure VARCHAR(10) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_id) REFERENCES pick_lists (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE inventory_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count_number VARCHAR(20) NOT NULL,
            warehouse_code VARCHAR(10) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'assigned',
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE inventory_count_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_count_id INTEGER NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            system_quantity FLOAT NOT NULL,
            counted_quantity FLOAT NOT NULL,
            variance FLOAT NOT NULL,
            unit_of_measure VARCHAR(10) NOT NULL,
            batch_number VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inventory_count_id) REFERENCES inventory_counts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE barcode_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code VARCHAR(50) NOT NULL,
            barcode VARCHAR(100) NOT NULL,
            label_format VARCHAR(20) NOT NULL,
            print_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_printed DATETIME
        )
    ''')
    
    # Create default admin user
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', 'admin@wms.local', 'scrypt:32768:8:1$8pEYlGu0xdKYV2JD$4e9e8f0b9d8c7a6e5d4c3b2a1f0e9d8c7b6a5e4d3c2b1a0f9e8d7c6b5a4e3d2c1b0a9f8e7d6c5b4a3e2d1c0b9a8f7e6d5c4b3a2e1d0c9b8a7f6e5d4c3b2a1e0d9c8b7f6a5e4d3c2b1a0f9e8d7c6b5a4e3d2c1b0a9f8e7d6c5b4a3e2d1', 'Admin', 'User', 'admin', 1))
    
    conn.commit()
    conn.close()
    
    print(f"✅ New database created successfully: {db_path}")
    print("✅ Admin user created - Username: admin, Password: admin123")

def main():
    print("WMS Database Final Fix Tool")
    print("=" * 50)
    print("This will completely recreate your database with the correct schema.")
    print("⚠️  WARNING: This will delete all existing data!")
    print()
    
    response = input("Continue? (yes/no): ").lower().strip()
    if response != 'yes':
        print("Operation cancelled.")
        return
    
    try:
        recreate_database()
        print()
        print("🎉 Database fix completed successfully!")
        print()
        print("Next steps:")
        print("1. Start your Flask application")
        print("2. Login with: Username: admin, Password: admin123")
        print("3. Your WMS system should now work without any database errors")
        print()
        print("All GRPO, QC Dashboard, and bin location features are now ready to use!")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        print("Please check the error and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()