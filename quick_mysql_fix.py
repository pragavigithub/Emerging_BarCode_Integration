#!/usr/bin/env python3
"""
Quick MySQL Database Fix
Direct MySQL connection to fix schema issues
"""

import mysql.connector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_mysql_directly():
    """Fix MySQL database directly using mysql-connector-python"""
    
    try:
        # Connect to MySQL with your credentials
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='root@123',
            database='wms_db_dev'
        )
        
        if connection.is_connected():
            logger.info("✅ Connected to MySQL server")
            cursor = connection.cursor()
            
            # Drop and recreate branches table with correct structure
            logger.info("🔧 Fixing branches table...")
            cursor.execute("DROP TABLE IF EXISTS branches")
            
            create_branches = """
            CREATE TABLE branches (
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
            """
            cursor.execute(create_branches)
            logger.info("✅ Branches table created")
            
            # Insert default branch
            cursor.execute("""
                INSERT INTO branches (id, name, address, is_active, is_default) 
                VALUES ('BR001', 'Main Branch', 'Main Office', TRUE, TRUE)
            """)
            logger.info("✅ Default branch inserted")
            
            # Fix users table - add missing columns
            logger.info("🔧 Fixing users table...")
            
            # Add missing columns one by one
            missing_columns = [
                "ADD COLUMN first_name VARCHAR(50)",
                "ADD COLUMN last_name VARCHAR(50)", 
                "ADD COLUMN role VARCHAR(20) DEFAULT 'user'",
                "ADD COLUMN branch_id VARCHAR(10)",
                "ADD COLUMN branch_name VARCHAR(100)",
                "ADD COLUMN default_branch_id VARCHAR(10)",
                "ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
                "ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE",
                "ADD COLUMN last_login TIMESTAMP NULL",
                "ADD COLUMN permissions TEXT",
                "ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ]
            
            for column in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users {column}")
                    logger.info(f"✅ Added column: {column}")
                except mysql.connector.Error as e:
                    if 'Duplicate column name' in str(e):
                        logger.info(f"✓ Column already exists: {column}")
                    else:
                        logger.warning(f"⚠️ Could not add {column}: {e}")
            
            # Create admin user if not exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO users 
                    (username, email, password_hash, first_name, last_name, role, branch_id, default_branch_id, is_active) 
                    VALUES 
                    ('admin', 'admin@company.com', 
                     'scrypt:32768:8:1$uYz8KQoJOvhXZZ5J$2e3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5', 
                     'System', 'Administrator', 'admin', 'BR001', 'BR001', TRUE)
                """)
                logger.info("✅ Admin user created")
            else:
                logger.info("✓ Admin user already exists")
            
            # Create other essential tables
            logger.info("🔧 Creating other tables...")
            
            # GRPO Documents
            cursor.execute("DROP TABLE IF EXISTS grpo_documents")
            cursor.execute("""
                CREATE TABLE grpo_documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    po_number VARCHAR(50) NOT NULL,
                    supplier_code VARCHAR(50),
                    supplier_name VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'draft',
                    draft_or_post VARCHAR(10) DEFAULT 'draft',
                    notes TEXT,
                    sap_document_number VARCHAR(50),
                    user_id INT,
                    qc_user_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ GRPO documents table created")
            
            # GRPO Items
            cursor.execute("DROP TABLE IF EXISTS grpo_items")
            cursor.execute("""
                CREATE TABLE grpo_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    grpo_document_id INT,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(100),
                    received_quantity DECIMAL(10,3) DEFAULT 0,
                    po_quantity DECIMAL(10,3),
                    open_quantity DECIMAL(10,3),
                    unit_of_measure VARCHAR(10),
                    bin_location VARCHAR(50),
                    batch_number VARCHAR(50),
                    serial_number VARCHAR(50),
                    expiration_date DATE,
                    supplier_barcode VARCHAR(100),
                    generated_barcode VARCHAR(100),
                    barcode_printed BOOLEAN DEFAULT FALSE,
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    po_line_number INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ GRPO items table created")
            
            # Inventory Transfers
            cursor.execute("DROP TABLE IF EXISTS inventory_transfers")
            cursor.execute("""
                CREATE TABLE inventory_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_number VARCHAR(50) NOT NULL,
                    from_warehouse_code VARCHAR(10),
                    to_warehouse_code VARCHAR(10),
                    status VARCHAR(20) DEFAULT 'draft',
                    sap_document_number VARCHAR(50),
                    user_id INT,
                    qc_approver_id INT,
                    qc_approved_at TIMESTAMP NULL,
                    qc_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Inventory transfers table created")
            
            # Inventory Transfer Items
            cursor.execute("DROP TABLE IF EXISTS inventory_transfer_items")
            cursor.execute("""
                CREATE TABLE inventory_transfer_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    inventory_transfer_id INT,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(100),
                    quantity DECIMAL(10,3) NOT NULL,
                    unit_of_measure VARCHAR(10),
                    from_bin VARCHAR(50),
                    to_bin VARCHAR(50),
                    batch_number VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Inventory transfer items table created")
            
            # Commit all changes
            connection.commit()
            logger.info("🎉 All database fixes completed successfully!")
            
            return True
            
    except mysql.connector.Error as e:
        logger.error(f"❌ MySQL Error: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("MySQL connection closed")

if __name__ == "__main__":
    logger.info("🔧 Starting quick MySQL fix...")
    success = fix_mysql_directly()
    if success:
        logger.info("✅ MySQL database fixed! You can now run python main.py")
    else:
        logger.info("❌ Fix failed. Please check MySQL installation and credentials.")