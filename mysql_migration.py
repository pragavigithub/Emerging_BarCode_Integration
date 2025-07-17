
#!/usr/bin/env python3
"""
MySQL Migration Script for WMS Application
This script creates the complete database schema for MySQL and adds all required tables and columns.
"""

import os
import sys
import logging
from datetime import datetime

# Try to import MySQL connectors
try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_CONNECTOR_AVAILABLE = True
except ImportError:
    MYSQL_CONNECTOR_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mysql_connection():
    """Get MySQL connection using environment variables"""
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_user = os.getenv('MYSQL_USER','root')
    mysql_password = os.getenv('MYSQL_PASSWORD','root@123')
    mysql_database = os.getenv('MYSQL_DATABASE','wms_db_dev')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    
    if not all([mysql_user, mysql_password, mysql_database]):
        logger.error("❌ Missing MySQL environment variables!")
        logger.error("Required: MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
        logger.error("Optional: MYSQL_HOST (default: localhost), MYSQL_PORT (default: 3306)")
        return None
    
    # Try PyMySQL first
    if PYMYSQL_AVAILABLE:
        try:
            connection = pymysql.connect(
                host=mysql_host,
                port=mysql_port,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                charset='utf8mb4',
                autocommit=False
            )
            logger.info("✅ Connected to MySQL using PyMySQL")
            return connection
        except Exception as e:
            logger.error(f"PyMySQL connection failed: {e}")
    
    # Try MySQL Connector as fallback
    if MYSQL_CONNECTOR_AVAILABLE:
        try:
            connection = mysql.connector.connect(
                host=mysql_host,
                port=mysql_port,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                autocommit=False
            )
            logger.info("✅ Connected to MySQL using MySQL Connector")
            return connection
        except Exception as e:
            logger.error(f"MySQL Connector also failed: {e}")
    
    logger.error("❌ No MySQL connectors available or connection failed")
    return None

def create_database_schema(connection):
    """Create complete database schema"""
    cursor = connection.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            branch VARCHAR(50) DEFAULT 'Main',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    logger.info("✅ Created users table")
    
    # Create branches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            branch_code VARCHAR(10) UNIQUE NOT NULL,
            branch_name VARCHAR(100) NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("✅ Created branches table")
    
    # Create warehouses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            warehouse_code VARCHAR(10) UNIQUE NOT NULL,
            warehouse_name VARCHAR(100) NOT NULL,
            branch_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
    """)
    logger.info("✅ Created warehouses table")
    
    # Create bin_locations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bin_locations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bin_code VARCHAR(20) UNIQUE NOT NULL,
            warehouse_code VARCHAR(10) NOT NULL,
            bin_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    logger.info("✅ Created bin_locations table")
    
    # Create grpo_documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grpo_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            po_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            status VARCHAR(20) DEFAULT 'draft',
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    logger.info("✅ Created grpo_documents table")
    
    # Create grpo_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grpo_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            grpo_document_id INT NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            ordered_quantity DECIMAL(10,2) NOT NULL,
            received_quantity DECIMAL(10,2) NOT NULL,
            unit_of_measure VARCHAR(10) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            expiration_date DATE,
            serial_number VARCHAR(50),
            barcode VARCHAR(50),
            po_line_number INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grpo_document_id) REFERENCES grpo_documents(id)
        )
    """)
    logger.info("✅ Created grpo_items table")
    
    # Create inventory_transfers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transfers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transfer_request_number VARCHAR(20) NOT NULL,
            sap_document_number VARCHAR(20),
            status VARCHAR(20) DEFAULT 'draft',
            user_id INT NOT NULL,
            qc_approver_id INT,
            qc_approved_at TIMESTAMP,
            qc_notes TEXT,
            from_warehouse VARCHAR(20),
            to_warehouse VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (qc_approver_id) REFERENCES users(id)
        )
    """)
    logger.info("✅ Created inventory_transfers table")
    
    # Create inventory_transfer_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transfer_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inventory_transfer_id INT NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            quantity DECIMAL(10,2) NOT NULL,
            unit_of_measure VARCHAR(10) NOT NULL,
            from_bin VARCHAR(20) NOT NULL,
            to_bin VARCHAR(20) NOT NULL,
            batch_number VARCHAR(50),
            qc_status VARCHAR(20) DEFAULT 'pending',
            qc_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id)
        )
    """)
    logger.info("✅ Created inventory_transfer_items table")
    
    # Create barcode_labels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barcode_labels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_code VARCHAR(50) NOT NULL,
            barcode VARCHAR(50) UNIQUE NOT NULL,
            label_type VARCHAR(20) DEFAULT 'standard',
            generated_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (generated_by) REFERENCES users(id)
        )
    """)
    logger.info("✅ Created barcode_labels table")
    
    # Create pick_lists table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pick_lists (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sales_order_number VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    logger.info("✅ Created pick_lists table")
    
    # Create pick_list_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pick_list_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pick_list_id INT NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(200) NOT NULL,
            quantity DECIMAL(10,2) NOT NULL,
            picked_quantity DECIMAL(10,2) DEFAULT 0,
            unit_of_measure VARCHAR(10) NOT NULL,
            bin_location VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id)
        )
    """)
    logger.info("✅ Created pick_list_items table")
    
    connection.commit()
    logger.info("✅ All tables created successfully!")

def create_default_data(connection):
    """Create default data for testing"""
    cursor = connection.cursor()
    
    # Create default branch
    cursor.execute("""
        INSERT IGNORE INTO branches (branch_code, branch_name, address)
        VALUES ('MAIN', 'Main Branch', 'Head Office')
    """)
    
    # Create default warehouse
    cursor.execute("""
        INSERT IGNORE INTO warehouses (warehouse_code, warehouse_name, branch_id)
        VALUES ('WH01', 'Main Warehouse', 1)
    """)
    
    # Create default admin user
    cursor.execute("""
        INSERT IGNORE INTO users (username, email, password_hash, role, branch)
        VALUES ('admin', 'admin@company.com', 'pbkdf2:sha256:600000$YourHashHere', 'admin', 'Main')
    """)
    
    connection.commit()
    logger.info("✅ Default data created")

def main():
    """Main migration function"""
    logger.info("🚀 Starting MySQL Migration for WMS Application")
    logger.info("=" * 60)
    
    # Check if MySQL packages are available
    if not PYMYSQL_AVAILABLE and not MYSQL_CONNECTOR_AVAILABLE:
        logger.error("❌ No MySQL packages available!")
        logger.error("Please install: pip install pymysql mysql-connector-python")
        sys.exit(1)
    
    # Get MySQL connection
    connection = get_mysql_connection()
    if not connection:
        logger.error("❌ Failed to connect to MySQL database")
        sys.exit(1)
    
    try:
        # Create database schema
        create_database_schema(connection)
        
        # Create default data
        create_default_data(connection)
        
        logger.info("=" * 60)
        logger.info("✅ MySQL Migration completed successfully!")
        logger.info("🎉 WMS Application is ready to use with MySQL!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        connection.rollback()
        sys.exit(1)
    finally:
        connection.close()

if __name__ == "__main__":
    main()