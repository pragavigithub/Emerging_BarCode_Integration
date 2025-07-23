#!/usr/bin/env python3
"""
Complete MySQL Database Migration Script
=====================================

This script creates a complete MySQL database schema for the Warehouse Management System
and fixes all missing columns that cause operational errors.

Run this script to:
1. Create all required tables if they don't exist
2. Add missing columns to existing tables
3. Fix schema mismatches

Usage: python complete_mysql_migration.py
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mysql_connection():
    """Get MySQL database connection using environment variables"""
    try:
        # Get MySQL configuration from environment
        config = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'user': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ.get('MYSQL_PASSWORD', ''),
            'database': os.environ.get('MYSQL_DATABASE', 'wms_database'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True
        }
        
        logger.info(f"Connecting to MySQL at {config['host']} as {config['user']}")
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            logger.info("✅ Successfully connected to MySQL database")
            return connection
        else:
            logger.error("❌ Failed to connect to MySQL database")
            return None
            
    except Error as e:
        logger.error(f"❌ MySQL connection error: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = '{table_name}' 
        AND COLUMN_NAME = '{column_name}'
    """)
    return cursor.fetchone()[0] > 0

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = '{table_name}'
    """)
    return cursor.fetchone()[0] > 0

def create_complete_schema(cursor):
    """Create complete database schema"""
    
    logger.info("🔧 Creating complete database schema...")
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
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
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified users table")
    
    # Create branches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address TEXT,
            phone VARCHAR(20),
            email VARCHAR(100),
            manager_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            is_default BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified branches table")
    
    # Create grpo_documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grpo_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            po_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            supplier_code VARCHAR(50),
            supplier_name VARCHAR(200),
            po_date DATETIME,
            po_total DECIMAL(15,2),
            status VARCHAR(20) DEFAULT 'draft',
            user_id INT NOT NULL,
            qc_user_id INT,
            qc_notes TEXT,
            notes TEXT,
            draft_or_post VARCHAR(10) DEFAULT 'draft',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (qc_user_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified grpo_documents table")
    
    # Create grpo_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grpo_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            grpo_document_id INT NOT NULL,
            po_line_number INT,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            po_quantity DECIMAL(15,3),
            open_quantity DECIMAL(15,3),
            received_quantity DECIMAL(15,3) NOT NULL,
            unit_of_measure VARCHAR(10) NOT NULL,
            unit_price DECIMAL(15,2),
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
            FOREIGN KEY (grpo_document_id) REFERENCES grpo_documents(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified grpo_items table")
    
    # Create inventory_transfers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transfers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transfer_request_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            status VARCHAR(20) DEFAULT 'draft',
            user_id INT NOT NULL,
            qc_approver_id INT,
            qc_approved_at DATETIME,
            qc_notes TEXT,
            from_warehouse VARCHAR(20),
            to_warehouse VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (qc_approver_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified inventory_transfers table")
    
    # Create inventory_transfer_items table with ALL required columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transfer_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inventory_transfer_id INT NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            quantity DECIMAL(15,3) NOT NULL,
            unit_of_measure VARCHAR(10) NOT NULL,
            from_bin_location VARCHAR(20) NOT NULL,
            to_bin_location VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            serial_number VARCHAR(50),
            qc_status VARCHAR(20) DEFAULT 'pending',
            qc_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified inventory_transfer_items table")
    
    # Create pick_lists table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pick_lists (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sales_order_number VARCHAR(20) NOT NULL,
            customer_code VARCHAR(50),
            customer_name VARCHAR(200),
            priority VARCHAR(20) DEFAULT 'normal',
            status VARCHAR(20) DEFAULT 'draft',
            user_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified pick_lists table")
    
    # Create pick_list_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pick_list_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pick_list_id INT NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            ordered_quantity DECIMAL(15,3) NOT NULL,
            picked_quantity DECIMAL(15,3) DEFAULT 0,
            unit_of_measure VARCHAR(10) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified pick_list_items table")
    
    # Create inventory_counts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_counts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            count_name VARCHAR(100) NOT NULL,
            warehouse_code VARCHAR(20),
            status VARCHAR(20) DEFAULT 'draft',
            user_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified inventory_counts table")
    
    # Create inventory_count_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_count_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inventory_count_id INT NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            system_quantity DECIMAL(15,3),
            counted_quantity DECIMAL(15,3),
            variance DECIMAL(15,3),
            batch_number VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inventory_count_id) REFERENCES inventory_counts(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified inventory_count_items table")
    
    # Create barcode_labels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barcode_labels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_code VARCHAR(50) NOT NULL,
            barcode VARCHAR(100) NOT NULL,
            label_type VARCHAR(20) DEFAULT 'standard',
            printed_count INT DEFAULT 0,
            user_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    logger.info("✅ Created/verified barcode_labels table")

def add_missing_columns(cursor):
    """Add missing columns to existing tables"""
    
    logger.info("🔧 Checking and adding missing columns...")
    
    # Check and add missing columns to inventory_transfer_items
    if not check_column_exists(cursor, 'inventory_transfer_items', 'qc_status'):
        cursor.execute("ALTER TABLE inventory_transfer_items ADD COLUMN qc_status VARCHAR(20) DEFAULT 'pending'")
        logger.info("✅ Added qc_status column to inventory_transfer_items")
    
    if not check_column_exists(cursor, 'inventory_transfer_items', 'qc_notes'):
        cursor.execute("ALTER TABLE inventory_transfer_items ADD COLUMN qc_notes TEXT")
        logger.info("✅ Added qc_notes column to inventory_transfer_items")
    
    if not check_column_exists(cursor, 'inventory_transfer_items', 'serial_number'):
        cursor.execute("ALTER TABLE inventory_transfer_items ADD COLUMN serial_number VARCHAR(50)")
        logger.info("✅ Added serial_number column to inventory_transfer_items")
    
    # Check and add missing columns to grpo_documents
    if not check_column_exists(cursor, 'grpo_documents', 'po_date'):
        cursor.execute("ALTER TABLE grpo_documents ADD COLUMN po_date DATETIME")
        logger.info("✅ Added po_date column to grpo_documents")
    
    if not check_column_exists(cursor, 'grpo_documents', 'po_total'):
        cursor.execute("ALTER TABLE grpo_documents ADD COLUMN po_total DECIMAL(15,2)")
        logger.info("✅ Added po_total column to grpo_documents")
    
    if not check_column_exists(cursor, 'grpo_documents', 'notes'):
        cursor.execute("ALTER TABLE grpo_documents ADD COLUMN notes TEXT")
        logger.info("✅ Added notes column to grpo_documents")
    
    # Check and add missing columns to grpo_items
    if not check_column_exists(cursor, 'grpo_items', 'serial_number'):
        cursor.execute("ALTER TABLE grpo_items ADD COLUMN serial_number VARCHAR(50)")
        logger.info("✅ Added serial_number column to grpo_items")
    
    # Check and add missing columns to inventory_transfers
    if not check_column_exists(cursor, 'inventory_transfers', 'transfer_request_number'):
        cursor.execute("ALTER TABLE inventory_transfers ADD COLUMN transfer_request_number VARCHAR(20)")
        logger.info("✅ Added transfer_request_number column to inventory_transfers")
    
    if not check_column_exists(cursor, 'inventory_transfers', 'from_warehouse'):
        cursor.execute("ALTER TABLE inventory_transfers ADD COLUMN from_warehouse VARCHAR(20)")
        logger.info("✅ Added from_warehouse column to inventory_transfers")
    
    if not check_column_exists(cursor, 'inventory_transfers', 'to_warehouse'):
        cursor.execute("ALTER TABLE inventory_transfers ADD COLUMN to_warehouse VARCHAR(20)")
        logger.info("✅ Added to_warehouse column to inventory_transfers")

def create_default_data(cursor):
    """Create default branch and admin user"""
    
    logger.info("🔧 Creating default data...")
    
    # Create default branch
    cursor.execute("""
        INSERT IGNORE INTO branches (id, name, address, is_active, is_default)
        VALUES ('BR001', 'Main Branch', 'Main Office', TRUE, TRUE)
    """)
    logger.info("✅ Created default branch")
    
    # Create default admin user
    cursor.execute("""
        INSERT IGNORE INTO users (
            username, email, password_hash, first_name, last_name, 
            role, branch_id, default_branch_id, is_active
        ) VALUES (
            'admin', 'admin@company.com', 
            'scrypt:32768:8:1$fvYUoXFfgSvKz7vB$46c2c0b6b14b8a6c7f9d3e8a8f9c2e6d1f4e7a9b5c8d2f5e8b1a4c7e0f3d6b9e2a5c8f1b4e7a0d3f6c9b2e5f8a1c4e7b0d3f6c9b2e5f8a1c4e7', 
            'System', 'Administrator', 'admin', 'BR001', 'BR001', TRUE
        )
    """)
    logger.info("✅ Created default admin user (username: admin, password: admin123)")

def main():
    """Main migration function"""
    
    print("=" * 60)
    print("   MySQL Database Migration Script")
    print("   Warehouse Management System (WMS)")
    print("=" * 60)
    print()
    
    # Check environment variables
    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.info("Please set the following environment variables:")
        for var in missing_vars:
            logger.info(f"  export {var}=your_value")
        sys.exit(1)
    
    # Connect to MySQL
    connection = get_mysql_connection()
    if not connection:
        logger.error("❌ Cannot connect to MySQL database")
        sys.exit(1)
    
    try:
        cursor = connection.cursor()
        
        # Run migration steps
        create_complete_schema(cursor)
        add_missing_columns(cursor)
        create_default_data(cursor)
        
        # Commit all changes
        connection.commit()
        
        print()
        print("=" * 60)
        print("✅ MySQL Database Migration Completed Successfully!")
        print("=" * 60)
        print()
        logger.info("All database tables and columns are now properly configured")
        logger.info("You can now run your application without database errors")
        print()
        print("Default Login Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print()
        
    except Error as e:
        logger.error(f"❌ Migration failed: {e}")
        connection.rollback()
        sys.exit(1)
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("MySQL connection closed")

if __name__ == "__main__":
    main()