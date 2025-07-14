#!/usr/bin/env python3
"""
Create Local Database with All Tables
This script creates a fresh local database with all required tables and columns
"""
import os
import sqlite3
import logging
from datetime import datetime

def create_local_database():
    """Create a fresh local database with all required tables"""
    print("🚀 Creating Local Database with All Tables")
    print("=" * 60)
    
    # Create instance directory
    instance_dir = "instance"
    os.makedirs(instance_dir, exist_ok=True)
    
    db_path = os.path.join(instance_dir, "database.db")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(db_path, backup_path)
        print(f"📁 Backed up existing database to: {backup_path}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"📁 Creating database: {db_path}")
    
    # Create all tables with proper schema
    tables = [
        # Users table
        """
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
            default_branch_id VARCHAR(10),
            is_active BOOLEAN DEFAULT TRUE,
            must_change_password BOOLEAN DEFAULT FALSE,
            last_login DATETIME,
            permissions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # GRPO Documents table
        """
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
            notes TEXT,
            draft_or_post VARCHAR(10) DEFAULT 'draft',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (qc_user_id) REFERENCES users(id)
        )
        """,
        
        # GRPO Items table
        """
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
            serial_number VARCHAR(50),
            expiration_date DATETIME,
            supplier_barcode VARCHAR(100),
            generated_barcode VARCHAR(100),
            barcode_printed BOOLEAN DEFAULT FALSE,
            qc_status VARCHAR(20) DEFAULT 'pending',
            qc_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grpo_document_id) REFERENCES grpo_documents(id)
        )
        """,
        
        # Inventory Transfers table (WITH WAREHOUSE COLUMNS)
        """
        CREATE TABLE inventory_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transfer_request_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            status VARCHAR(20) DEFAULT 'draft',
            user_id INTEGER NOT NULL,
            from_warehouse VARCHAR(20),
            to_warehouse VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        
        # Inventory Transfer Items table
        """
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
            FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id)
        )
        """,
        
        # Pick Lists table
        """
        CREATE TABLE pick_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pick_list_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            status VARCHAR(20) DEFAULT 'assigned',
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        
        # Pick List Items table
        """
        CREATE TABLE pick_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pick_list_id INTEGER NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            required_quantity FLOAT NOT NULL,
            picked_quantity FLOAT DEFAULT 0,
            unit_of_measure VARCHAR(10) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id)
        )
        """,
        
        # Inventory Counts table
        """
        CREATE TABLE inventory_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count_number VARCHAR(20) NOT NULL,
            warehouse_code VARCHAR(10) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'assigned',
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        
        # Inventory Count Items table
        """
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
            FOREIGN KEY (inventory_count_id) REFERENCES inventory_counts(id)
        )
        """,
        
        # Barcode Labels table
        """
        CREATE TABLE barcode_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code VARCHAR(50) NOT NULL,
            barcode VARCHAR(100) NOT NULL,
            label_format VARCHAR(20) NOT NULL,
            print_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_printed DATETIME
        )
        """
    ]
    
    # Create tables
    for i, table_sql in enumerate(tables):
        table_name = table_sql.split('(')[0].split()[-1]
        try:
            cursor.execute(table_sql)
            print(f"✅ Created table: {table_name}")
        except Exception as e:
            print(f"❌ Failed to create table {table_name}: {e}")
    
    # Create default admin user
    try:
        from werkzeug.security import generate_password_hash
        admin_password = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, role)
            VALUES ('admin', 'admin@example.com', ?, 'Admin', 'User', 'admin')
        """, (admin_password,))
        print("✅ Created default admin user (admin/admin123)")
    except Exception as e:
        print(f"⚠️ Warning: Could not create admin user: {e}")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Database created successfully at: {db_path}")
    print("🔍 Verifying table structure...")
    
    # Verify inventory_transfers table structure
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(inventory_transfers)")
    columns = cursor.fetchall()
    
    print("\n📋 inventory_transfers table structure:")
    for col in columns:
        print(f"   • {col[1]} ({col[2]})")
    
    # Check if warehouse columns exist
    column_names = [col[1] for col in columns]
    if 'from_warehouse' in column_names and 'to_warehouse' in column_names:
        print("\n✅ Warehouse columns are present!")
    else:
        print("\n❌ Warehouse columns missing!")
    
    conn.close()
    
    print("\n🚀 Database setup complete!")
    print("💡 You can now run your application without column errors")

if __name__ == "__main__":
    create_local_database()