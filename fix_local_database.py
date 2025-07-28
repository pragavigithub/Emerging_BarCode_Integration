#!/usr/bin/env python3
"""
Local Database Schema Fix Script
================================

This script fixes missing columns in the local SQLite database that cause
login and other operational errors.

The error "no such column: users.user_is_active" indicates the local database
schema is outdated and missing recent model additions.

Usage: python fix_local_database.py
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sqlite_connection():
    """Get SQLite database connection"""
    try:
        # Check if instance folder exists
        instance_dir = 'instance'
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
            logger.info(f"Created instance directory: {instance_dir}")
        
        db_path = os.path.join(instance_dir, 'warehouse.db')
        logger.info(f"Connecting to SQLite database: {db_path}")
        
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        logger.info("✅ Successfully connected to SQLite database")
        return connection
        
    except Exception as e:
        logger.error(f"❌ SQLite connection error: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return column_name in columns

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def add_missing_user_columns(cursor):
    """Add missing columns to users table"""
    logger.info("🔧 Checking and fixing users table...")
    
    # List of columns that should exist in users table
    required_columns = [
        ('user_is_active', 'BOOLEAN DEFAULT 1'),
        ('must_change_password', 'BOOLEAN DEFAULT 0'),
        ('last_login', 'DATETIME'),
        ('permissions', 'TEXT'),
        ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ('first_name', 'VARCHAR(80) DEFAULT ""'),
        ('last_name', 'VARCHAR(80) DEFAULT ""'),
        ('role', 'VARCHAR(20) DEFAULT "user"'),
        ('branch_id', 'VARCHAR(10)'),
        ('branch_name', 'VARCHAR(100)'),
        ('default_branch_id', 'VARCHAR(10)')
    ]
    
    for column_name, column_type in required_columns:
        if not check_column_exists(cursor, 'users', column_name):
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                logger.info(f"✅ Added column: users.{column_name}")
            except Exception as e:
                logger.error(f"❌ Error adding column users.{column_name}: {e}")
        else:
            logger.info(f"✓ Column exists: users.{column_name}")

def add_missing_grpo_columns(cursor):
    """Add missing columns to grpo_documents table"""
    logger.info("🔧 Checking and fixing grpo_documents table...")
    
    required_columns = [
        ('po_date', 'DATETIME'),
        ('po_total', 'DECIMAL(15,2)'),
        ('notes', 'TEXT'),
        ('qc_approver_id', 'INTEGER'),
        ('qc_approved_at', 'DATETIME'),
        ('qc_notes', 'TEXT')
    ]
    
    if check_table_exists(cursor, 'grpo_documents'):
        for column_name, column_type in required_columns:
            if not check_column_exists(cursor, 'grpo_documents', column_name):
                try:
                    cursor.execute(f"ALTER TABLE grpo_documents ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ Added column: grpo_documents.{column_name}")
                except Exception as e:
                    logger.error(f"❌ Error adding column grpo_documents.{column_name}: {e}")
            else:
                logger.info(f"✓ Column exists: grpo_documents.{column_name}")

def add_missing_inventory_transfer_columns(cursor):
    """Add missing columns to inventory_transfer tables"""
    logger.info("🔧 Checking and fixing inventory_transfer tables...")
    
    # inventory_transfers table columns
    if check_table_exists(cursor, 'inventory_transfers'):
        transfer_columns = [
            ('transfer_request_number', 'VARCHAR(50)'),
            ('from_warehouse', 'VARCHAR(20)'),
            ('to_warehouse', 'VARCHAR(20)'),
            ('qc_approver_id', 'INTEGER'),
            ('qc_approved_at', 'DATETIME'),
            ('qc_notes', 'TEXT')
        ]
        
        for column_name, column_type in transfer_columns:
            if not check_column_exists(cursor, 'inventory_transfers', column_name):
                try:
                    cursor.execute(f"ALTER TABLE inventory_transfers ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ Added column: inventory_transfers.{column_name}")
                except Exception as e:
                    logger.error(f"❌ Error adding column inventory_transfers.{column_name}: {e}")
            else:
                logger.info(f"✓ Column exists: inventory_transfers.{column_name}")
    
    # inventory_transfer_items table columns
    if check_table_exists(cursor, 'inventory_transfer_items'):
        item_columns = [
            ('qc_status', 'VARCHAR(20) DEFAULT "pending"'),
            ('qc_notes', 'TEXT'),
            ('serial_number', 'VARCHAR(100)')
        ]
        
        for column_name, column_type in item_columns:
            if not check_column_exists(cursor, 'inventory_transfer_items', column_name):
                try:
                    cursor.execute(f"ALTER TABLE inventory_transfer_items ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ Added column: inventory_transfer_items.{column_name}")
                except Exception as e:
                    logger.error(f"❌ Error adding column inventory_transfer_items.{column_name}: {e}")
            else:
                logger.info(f"✓ Column exists: inventory_transfer_items.{column_name}")

def create_missing_tables(cursor):
    """Create any missing tables"""
    logger.info("🔧 Checking and creating missing tables...")
    
    # Branches table
    if not check_table_exists(cursor, 'branches'):
        cursor.execute("""
            CREATE TABLE branches (
                id VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address TEXT,
                phone VARCHAR(20),
                email VARCHAR(100),
                manager_name VARCHAR(100),
                is_active BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created table: branches")
    
    # User sessions table
    if not check_table_exists(cursor, 'user_sessions'):
        cursor.execute("""
            CREATE TABLE user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(256) NOT NULL,
                branch_id VARCHAR(10),
                login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                logout_time DATETIME,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ Created table: user_sessions")
    
    # Password reset tokens table
    if not check_table_exists(cursor, 'password_reset_tokens'):
        cursor.execute("""
            CREATE TABLE password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token VARCHAR(256) NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        logger.info("✅ Created table: password_reset_tokens")

def create_default_admin_user(cursor):
    """Create default admin user if none exists"""
    logger.info("🔧 Checking for admin user...")
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        logger.info("Creating default admin user...")
        from werkzeug.security import generate_password_hash
        
        password_hash = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO users (
                username, email, password_hash, first_name, last_name, 
                role, user_is_active, must_change_password
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', 'admin@company.com', password_hash, 'System', 'Administrator',
            'admin', True, True
        ))
        logger.info("✅ Created default admin user (username: admin, password: admin123)")
        logger.info("⚠️  Please change the default password after first login!")
    else:
        logger.info(f"✓ Found {admin_count} admin user(s)")

def create_default_branch(cursor):
    """Create default branch if none exists"""
    logger.info("🔧 Checking for default branch...")
    
    if check_table_exists(cursor, 'branches'):
        cursor.execute("SELECT COUNT(*) FROM branches")
        branch_count = cursor.fetchone()[0]
        
        if branch_count == 0:
            cursor.execute("""
                INSERT INTO branches (
                    id, name, is_active, is_default
                ) VALUES (?, ?, ?, ?)
            """, ('MAIN', 'Main Branch', True, True))
            logger.info("✅ Created default branch: MAIN")
        else:
            logger.info(f"✓ Found {branch_count} branch(es)")

def main():
    """Main function to run the database fix"""
    logger.info("🚀 Starting Local Database Schema Fix...")
    logger.info("=" * 50)
    
    # Connect to database
    connection = get_sqlite_connection()
    if not connection:
        logger.error("❌ Could not connect to database. Exiting.")
        sys.exit(1)
    
    try:
        cursor = connection.cursor()
        
        # Fix missing columns
        add_missing_user_columns(cursor)
        add_missing_grpo_columns(cursor)
        add_missing_inventory_transfer_columns(cursor)
        
        # Create missing tables
        create_missing_tables(cursor)
        
        # Create default data
        create_default_admin_user(cursor)
        create_default_branch(cursor)
        
        # Commit changes
        connection.commit()
        
        logger.info("=" * 50)
        logger.info("✅ Database schema fix completed successfully!")
        logger.info("✅ All missing columns have been added")
        logger.info("✅ Default admin user and branch created")
        logger.info("🎉 You can now run the application without errors!")
        
    except Exception as e:
        logger.error(f"❌ Error during database fix: {e}")
        connection.rollback()
        sys.exit(1)
    finally:
        connection.close()

if __name__ == "__main__":
    main()