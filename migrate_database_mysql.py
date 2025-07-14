#!/usr/bin/env python3
"""
MySQL Database Migration Script for WMS Application
Adds missing columns and updates schema to match the current models
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_connection():
    """Get database connection based on environment variables"""
    try:
        # Try MySQL first
        if os.environ.get('MYSQL_HOST'):
            import pymysql
            connection = pymysql.connect(
                host=os.environ.get('MYSQL_HOST', 'localhost'),
                port=int(os.environ.get('MYSQL_PORT', 3306)),
                user=os.environ.get('MYSQL_USER', 'root'),
                password=os.environ.get('MYSQL_PASSWORD', ''),
                database=os.environ.get('MYSQL_DATABASE', 'wms_db'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logging.info("Connected to MySQL database")
            return connection, 'mysql'
        
        # Try PostgreSQL next
        elif os.environ.get('DATABASE_URL'):
            import psycopg2
            import psycopg2.extras
            connection = psycopg2.connect(os.environ.get('DATABASE_URL'))
            logging.info("Connected to PostgreSQL database")
            return connection, 'postgresql'
        
        # Fallback to SQLite
        else:
            import sqlite3
            db_path = os.path.join(os.getcwd(), 'instance', 'wms.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            logging.info(f"Connected to SQLite database at {db_path}")
            return connection, 'sqlite'
            
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None, None

def check_column_exists(cursor, table_name, column_name, db_type):
    """Check if a column exists in a table"""
    try:
        if db_type == 'mysql':
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}' 
                AND COLUMN_NAME = '{column_name}'
            """)
            result = cursor.fetchone()
            return result['count'] > 0
        
        elif db_type == 'postgresql':
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND column_name = '{column_name}'
            """)
            result = cursor.fetchone()
            return result[0] > 0
        
        else:  # sqlite
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            return any(col[1] == column_name for col in columns)
            
    except Exception as e:
        logging.error(f"Error checking column {column_name} in {table_name}: {e}")
        return False

def add_missing_columns(connection, cursor, db_type):
    """Add missing columns to existing tables"""
    migrations = []
    
    # Check and add 'notes' column to grpo_documents table
    if not check_column_exists(cursor, 'grpo_documents', 'notes', db_type):
        if db_type == 'mysql':
            sql = "ALTER TABLE grpo_documents ADD COLUMN notes TEXT NULL"
        elif db_type == 'postgresql':
            sql = "ALTER TABLE grpo_documents ADD COLUMN notes TEXT"
        else:  # sqlite
            sql = "ALTER TABLE grpo_documents ADD COLUMN notes TEXT"
        
        migrations.append(('grpo_documents', 'notes', sql))
    
    # Check and add other potentially missing columns
    missing_columns = [
        ('grpo_documents', 'qc_notes', 'TEXT'),
        ('grpo_documents', 'draft_or_post', "VARCHAR(10) DEFAULT 'draft'"),
        ('grpo_items', 'generated_barcode', 'VARCHAR(100)'),
        ('grpo_items', 'barcode_printed', 'BOOLEAN DEFAULT FALSE'),
        ('grpo_items', 'qc_status', "VARCHAR(20) DEFAULT 'pending'"),
        ('grpo_items', 'qc_notes', 'TEXT'),
        ('inventory_transfers', 'from_warehouse', 'VARCHAR(20)'),
        ('inventory_transfers', 'to_warehouse', 'VARCHAR(20)'),
        ('users', 'branch_id', 'VARCHAR(10)'),
        ('users', 'branch_name', 'VARCHAR(100)'),
        ('users', 'default_branch_id', 'VARCHAR(10)'),
        ('users', 'must_change_password', 'BOOLEAN DEFAULT FALSE'),
        ('users', 'last_login', 'DATETIME'),
        ('users', 'permissions', 'TEXT'),
    ]
    
    for table_name, column_name, column_type in missing_columns:
        if not check_column_exists(cursor, table_name, column_name, db_type):
            if db_type == 'mysql':
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            elif db_type == 'postgresql':
                # Convert MySQL types to PostgreSQL types
                pg_type = column_type.replace('VARCHAR', 'VARCHAR').replace('DATETIME', 'TIMESTAMP').replace('BOOLEAN', 'BOOLEAN')
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {pg_type}"
            else:  # sqlite
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            
            migrations.append((table_name, column_name, sql))
    
    # Execute migrations
    for table_name, column_name, sql in migrations:
        try:
            logging.info(f"Adding column {column_name} to {table_name}")
            cursor.execute(sql)
            connection.commit()
            logging.info(f"✓ Successfully added {column_name} to {table_name}")
        except Exception as e:
            logging.error(f"✗ Failed to add {column_name} to {table_name}: {e}")
            connection.rollback()
    
    return len(migrations)

def create_missing_tables(connection, cursor, db_type):
    """Create any missing tables"""
    tables_created = 0
    
    # Check if barcode_labels table exists
    try:
        if db_type == 'mysql':
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'barcode_labels'
            """)
            table_exists = cursor.fetchone()['count'] > 0
        elif db_type == 'postgresql':
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = 'barcode_labels'
            """)
            table_exists = cursor.fetchone()[0] > 0
        else:  # sqlite
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='barcode_labels'")
            table_exists = len(cursor.fetchall()) > 0
        
        if not table_exists:
            if db_type == 'mysql':
                create_sql = """
                CREATE TABLE barcode_labels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_code VARCHAR(50) NOT NULL,
                    barcode VARCHAR(100) NOT NULL,
                    label_format VARCHAR(20) NOT NULL,
                    print_count INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_printed DATETIME NULL
                )
                """
            elif db_type == 'postgresql':
                create_sql = """
                CREATE TABLE barcode_labels (
                    id SERIAL PRIMARY KEY,
                    item_code VARCHAR(50) NOT NULL,
                    barcode VARCHAR(100) NOT NULL,
                    label_format VARCHAR(20) NOT NULL,
                    print_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_printed TIMESTAMP NULL
                )
                """
            else:  # sqlite
                create_sql = """
                CREATE TABLE barcode_labels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_code VARCHAR(50) NOT NULL,
                    barcode VARCHAR(100) NOT NULL,
                    label_format VARCHAR(20) NOT NULL,
                    print_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_printed DATETIME NULL
                )
                """
            
            cursor.execute(create_sql)
            connection.commit()
            logging.info("✓ Created barcode_labels table")
            tables_created += 1
    
    except Exception as e:
        logging.error(f"Error creating barcode_labels table: {e}")
        connection.rollback()
    
    return tables_created

def create_branches_table(connection, cursor, db_type):
    """Create branches table if it doesn't exist"""
    try:
        if db_type == 'mysql':
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'branches'
            """)
            table_exists = cursor.fetchone()['count'] > 0
        elif db_type == 'postgresql':
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = 'branches'
            """)
            table_exists = cursor.fetchone()[0] > 0
        else:  # sqlite
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='branches'")
            table_exists = len(cursor.fetchall()) > 0
        
        if not table_exists:
            if db_type == 'mysql':
                create_sql = """
                CREATE TABLE branches (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    address TEXT,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    manager_name VARCHAR(100),
                    is_default BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            elif db_type == 'postgresql':
                create_sql = """
                CREATE TABLE branches (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    address TEXT,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    manager_name VARCHAR(100),
                    is_default BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            else:  # sqlite
                create_sql = """
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
                """
            
            cursor.execute(create_sql)
            
            # Insert default branch
            if db_type == 'mysql':
                cursor.execute("""
                    INSERT INTO branches (id, name, is_default, is_active) 
                    VALUES ('HQ001', 'Head Office', TRUE, TRUE)
                """)
            elif db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO branches (id, name, is_default, is_active) 
                    VALUES ('HQ001', 'Head Office', TRUE, TRUE)
                """)
            else:  # sqlite
                cursor.execute("""
                    INSERT INTO branches (id, name, is_default, is_active) 
                    VALUES ('HQ001', 'Head Office', 1, 1)
                """)
            
            connection.commit()
            logging.info("✓ Created branches table with default branch")
            return True
    
    except Exception as e:
        logging.error(f"Error creating branches table: {e}")
        connection.rollback()
        return False
    
    return False

def main():
    """Main migration function"""
    logging.info("Starting database migration...")
    
    # Get database connection
    connection, db_type = get_database_connection()
    if not connection:
        logging.error("Failed to connect to database")
        sys.exit(1)
    
    try:
        cursor = connection.cursor()
        
        # Track changes
        columns_added = 0
        tables_created = 0
        
        # Add missing columns
        columns_added = add_missing_columns(connection, cursor, db_type)
        
        # Create missing tables
        tables_created += create_missing_tables(connection, cursor, db_type)
        
        # Create branches table
        if create_branches_table(connection, cursor, db_type):
            tables_created += 1
        
        # Summary
        logging.info("=" * 50)
        logging.info("MIGRATION SUMMARY")
        logging.info("=" * 50)
        logging.info(f"Database Type: {db_type.upper()}")
        logging.info(f"Columns Added: {columns_added}")
        logging.info(f"Tables Created: {tables_created}")
        
        if columns_added > 0 or tables_created > 0:
            logging.info("✓ Migration completed successfully!")
            logging.info("✓ Database schema is now up to date")
        else:
            logging.info("✓ Database schema is already up to date")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        connection.rollback()
        connection.close()
        sys.exit(1)

if __name__ == "__main__":
    main()