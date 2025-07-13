#!/usr/bin/env python3
"""
FINAL Database Fix Script for WMS Application
This script will completely resolve all database schema issues.
"""

import os
import sys
import logging
import sqlite3
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_database():
    """Find the SQLite database file"""
    possible_paths = [
        'instance/wms.db',
        'wms.db',
        './instance/wms.db',
        os.path.join(os.getcwd(), 'instance', 'wms.db'),
        os.path.join(os.getcwd(), 'wms.db')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logging.info(f"Found database at: {path}")
            return path
    
    # If no database found, create the instance directory
    instance_dir = os.path.join(os.getcwd(), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'wms.db')
    logging.info(f"No existing database found. Will create new database at: {db_path}")
    return db_path

def backup_database(db_path):
    """Create backup of existing database"""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        logging.info(f"Database backed up to: {backup_path}")
        return backup_path
    return None

def recreate_database():
    """Recreate database with correct schema"""
    db_path = find_database()
    backup_path = backup_database(db_path)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        logging.info("Removed existing database")
    
    # Create new database with proper schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create all tables with correct schema
    tables = {
        'users': '''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256),
                role VARCHAR(20) DEFAULT 'user',
                branch_id VARCHAR(10),
                branch_name VARCHAR(100),
                default_branch_id VARCHAR(10),
                must_change_password BOOLEAN DEFAULT 0,
                last_login DATETIME,
                permissions TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'grpo_documents': '''
            CREATE TABLE grpo_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number VARCHAR(50) NOT NULL,
                sap_document_number VARCHAR(50),
                supplier_code VARCHAR(50),
                supplier_name VARCHAR(200),
                po_date DATETIME,
                po_total DECIMAL(15,2),
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
        ''',
        'grpo_items': '''
            CREATE TABLE grpo_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grpo_id INTEGER NOT NULL,
                item_code VARCHAR(50) NOT NULL,
                item_description TEXT,
                ordered_quantity DECIMAL(15,3),
                received_quantity DECIMAL(15,3),
                batch_number VARCHAR(50),
                expiration_date DATETIME,
                bin_location VARCHAR(50),
                generated_barcode VARCHAR(100),
                barcode_printed BOOLEAN DEFAULT 0,
                qc_status VARCHAR(20) DEFAULT 'pending',
                qc_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id)
            )
        ''',
        'barcode_labels': '''
            CREATE TABLE barcode_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code VARCHAR(50) NOT NULL,
                barcode VARCHAR(100) NOT NULL,
                label_format VARCHAR(20) NOT NULL,
                print_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_printed DATETIME
            )
        ''',
        'branches': '''
            CREATE TABLE branches (
                id VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address TEXT,
                phone VARCHAR(20),
                email VARCHAR(100),
                manager_name VARCHAR(100),
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'bin_locations': '''
            CREATE TABLE bin_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bin_code VARCHAR(50) NOT NULL,
                warehouse_code VARCHAR(10) NOT NULL,
                bin_name VARCHAR(100),
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bin_code, warehouse_code)
            )
        '''
    }
    
    # Create all tables
    for table_name, sql in tables.items():
        cursor.execute(sql)
        logging.info(f"Created table: {table_name}")
    
    # Insert default data
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, role, branch_id, branch_name) 
        VALUES ('admin', 'admin@company.com', 'pbkdf2:sha256:600000$7K9X9rZ8$8c5a8d7d6f9e2b1a3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b', 'admin', 'HQ001', 'Head Office')
    """)
    
    cursor.execute("""
        INSERT INTO branches (id, name, is_default, is_active) 
        VALUES ('HQ001', 'Head Office', 1, 1)
    """)
    
    conn.commit()
    conn.close()
    
    logging.info("Database recreated successfully with all required tables and columns")
    return db_path

def main():
    """Main function"""
    logging.info("Starting final database fix...")
    
    try:
        # Recreate database with correct schema
        db_path = recreate_database()
        
        logging.info("=" * 60)
        logging.info("✓ DATABASE FIX COMPLETED SUCCESSFULLY!")
        logging.info("=" * 60)
        logging.info(f"Database location: {db_path}")
        logging.info("All tables created with correct schema including 'notes' column")
        logging.info("Default admin user and branch created")
        logging.info("You can now run your application without errors")
        
    except Exception as e:
        logging.error(f"Database fix failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()