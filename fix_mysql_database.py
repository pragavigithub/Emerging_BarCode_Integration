#!/usr/bin/env python3
"""
MySQL Database Fix Script
Fixes the missing branches table and other MySQL specific issues
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mysql_connection():
    """Get MySQL connection from environment variables"""
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    mysql_user = os.environ.get('MYSQL_USER', 'root')
    mysql_password = os.environ.get('MYSQL_PASSWORD', 'root@123')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'wms_db_dev')
    
    # Handle password with special characters - URL encode if needed
    from urllib.parse import quote_plus
    encoded_password = quote_plus(mysql_password)
    
    connection_string = f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    logger.info(f"Connecting to MySQL: {mysql_user}@{mysql_host}:{mysql_port}/{mysql_database}")
    return create_engine(connection_string)

def fix_branches_table(engine):
    """Create or fix the branches table"""
    try:
        with engine.connect() as connection:
            # Drop and recreate branches table to ensure proper structure
            logger.info("Creating branches table...")
            
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS branches (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    address TEXT,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    manager_name VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """))
            
            # Insert default branch
            connection.execute(text("""
                INSERT IGNORE INTO branches (id, name, address, is_active, is_default) 
                VALUES ('BR001', 'Main Branch', 'Main Office', TRUE, TRUE)
            """))
            
            connection.commit()
            logger.info("✅ Branches table created successfully")
            
    except Exception as e:
        logger.error(f"❌ Error fixing branches table: {e}")
        raise

def fix_users_table(engine):
    """Ensure users table has all required columns"""
    try:
        with engine.connect() as connection:
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Check and add missing columns
            missing_columns = []
            required_columns = [
                ('branch_id', 'VARCHAR(10)'),
                ('default_branch_id', 'VARCHAR(10)'),
                ('first_name', 'VARCHAR(50)'),
                ('last_name', 'VARCHAR(50)'),
                ('role', 'VARCHAR(20) DEFAULT "user"'),
                ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
            ]
            
            for column_name, column_type in required_columns:
                if column_name not in columns:
                    missing_columns.append((column_name, column_type))
            
            if missing_columns:
                logger.info(f"Adding missing columns to users table: {[col[0] for col in missing_columns]}")
                for column_name, column_type in missing_columns:
                    try:
                        connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                        logger.info(f"✅ Added column: {column_name}")
                    except Exception as e:
                        if 'duplicate' in str(e).lower():
                            logger.info(f"✓ Column {column_name} already exists")
                        else:
                            logger.warning(f"⚠️ Could not add column {column_name}: {e}")
                
                connection.commit()
                
            # Create default admin user if not exists
            connection.execute(text("""
                INSERT IGNORE INTO users 
                (username, email, password_hash, first_name, last_name, role, branch_id, default_branch_id) 
                VALUES 
                ('admin', 'admin@company.com', 'scrypt:32768:8:1$uYz8KQoJOvhXZZ5J$2e3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5', 'System', 'Administrator', 'admin', 'BR001', 'BR001')
            """))
            connection.commit()
            logger.info("✅ Users table fixed successfully")
            
    except Exception as e:
        logger.error(f"❌ Error fixing users table: {e}")
        raise

def fix_grpo_tables(engine):
    """Fix GRPO related tables"""
    try:
        with engine.connect() as connection:
            # Ensure grpo_documents table has all columns
            logger.info("Fixing GRPO tables...")
            
            # Add missing columns to grpo_documents
            grpo_document_columns = [
                ('notes', 'TEXT'),
                ('supplier_name', 'VARCHAR(100)'),
                ('supplier_code', 'VARCHAR(50)'),
                ('draft_or_post', 'VARCHAR(10) DEFAULT "draft"')
            ]
            
            inspector = inspect(engine)
            existing_columns = [col['name'] for col in inspector.get_columns('grpo_documents')]
            
            for column_name, column_type in grpo_document_columns:
                if column_name not in existing_columns:
                    try:
                        connection.execute(text(f"ALTER TABLE grpo_documents ADD COLUMN {column_name} {column_type}"))
                        logger.info(f"✅ Added column {column_name} to grpo_documents")
                    except Exception as e:
                        if 'duplicate' in str(e).lower():
                            logger.info(f"✓ Column {column_name} already exists")
                        else:
                            logger.warning(f"⚠️ Could not add column {column_name}: {e}")
            
            # Add missing columns to grpo_items
            grpo_item_columns = [
                ('serial_number', 'VARCHAR(50)'),
                ('generated_barcode', 'VARCHAR(100)'),
                ('barcode_printed', 'BOOLEAN DEFAULT FALSE'),
                ('qc_status', 'VARCHAR(20) DEFAULT "pending"')
            ]
            
            existing_item_columns = [col['name'] for col in inspector.get_columns('grpo_items')]
            
            for column_name, column_type in grpo_item_columns:
                if column_name not in existing_item_columns:
                    try:
                        connection.execute(text(f"ALTER TABLE grpo_items ADD COLUMN {column_name} {column_type}"))
                        logger.info(f"✅ Added column {column_name} to grpo_items")
                    except Exception as e:
                        if 'duplicate' in str(e).lower():
                            logger.info(f"✓ Column {column_name} already exists")
                        else:
                            logger.warning(f"⚠️ Could not add column {column_name}: {e}")
            
            connection.commit()
            logger.info("✅ GRPO tables fixed successfully")
            
    except Exception as e:
        logger.error(f"❌ Error fixing GRPO tables: {e}")
        raise

def fix_inventory_transfer_tables(engine):
    """Fix inventory transfer tables"""
    try:
        with engine.connect() as connection:
            logger.info("Fixing inventory transfer tables...")
            
            # Add missing columns to inventory_transfers
            transfer_columns = [
                ('qc_approver_id', 'INTEGER'),
                ('qc_approved_at', 'TIMESTAMP NULL'),
                ('qc_notes', 'TEXT'),
                ('from_warehouse_code', 'VARCHAR(10)'),
                ('to_warehouse_code', 'VARCHAR(10)')
            ]
            
            inspector = inspect(engine)
            existing_columns = [col['name'] for col in inspector.get_columns('inventory_transfers')]
            
            for column_name, column_type in transfer_columns:
                if column_name not in existing_columns:
                    try:
                        connection.execute(text(f"ALTER TABLE inventory_transfers ADD COLUMN {column_name} {column_type}"))
                        logger.info(f"✅ Added column {column_name} to inventory_transfers")
                    except Exception as e:
                        if 'duplicate' in str(e).lower():
                            logger.info(f"✓ Column {column_name} already exists")
                        else:
                            logger.warning(f"⚠️ Could not add column {column_name}: {e}")
            
            connection.commit()
            logger.info("✅ Inventory transfer tables fixed successfully")
            
    except Exception as e:
        logger.error(f"❌ Error fixing inventory transfer tables: {e}")
        raise

def main():
    """Main function to fix MySQL database"""
    logger.info("🔧 Starting MySQL database fix...")
    
    try:
        # Get MySQL connection
        engine = get_mysql_connection()
        logger.info("✅ Connected to MySQL database")
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful")
        
        # Fix database tables
        fix_branches_table(engine)
        fix_users_table(engine)
        fix_grpo_tables(engine)
        fix_inventory_transfer_tables(engine)
        
        logger.info("✅ MySQL database fix completed successfully!")
        logger.info("🚀 You can now run the application with MySQL")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        logger.error("Please check your MySQL connection and credentials in the .env file")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)