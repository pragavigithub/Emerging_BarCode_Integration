#!/usr/bin/env python3
"""
MySQL Database Setup Script
===========================

Simple script to set up MySQL database for the Warehouse Management System.

Usage: python setup_mysql_database.py
"""

import os
import pymysql
import logging
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_mysql():
    """Set up MySQL database with complete schema"""
    
    # Get MySQL configuration
    mysql_config = {
        'host': input("MySQL Host (default: localhost): ").strip() or 'localhost',
        'port': int(input("MySQL Port (default: 3306): ").strip() or '3306'),
        'user': input("MySQL Username (default: root): ").strip() or 'root',
        'password': input("MySQL Password: ").strip(),
        'database': input("Database Name (default: warehouse_db): ").strip() or 'warehouse_db'
    }
    
    try:
        # Connect to MySQL server (without database)
        connection = pymysql.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        logger.info(f"✅ Database '{mysql_config['database']}' created/verified")
        
        # Close connection and reconnect to the database
        cursor.close()
        connection.close()
        
        # Connect to the specific database
        connection = pymysql.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            database=mysql_config['database'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Create tables
        create_tables(cursor)
        
        # Create default data
        create_default_data(cursor)
        
        # Save environment configuration
        save_env_config(mysql_config)
        
        connection.commit()
        logger.info("✅ MySQL database setup completed successfully!")
        logger.info("✅ Default admin user: admin / admin123")
        
    except Exception as e:
        logger.error(f"❌ Error setting up MySQL: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
    
    return True

def create_tables(cursor):
    """Create all required tables"""
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `username` VARCHAR(64) NOT NULL UNIQUE,
            `email` VARCHAR(120) NOT NULL UNIQUE,
            `password_hash` VARCHAR(256) NOT NULL,
            `first_name` VARCHAR(80) DEFAULT '',
            `last_name` VARCHAR(80) DEFAULT '',
            `role` VARCHAR(20) DEFAULT 'user',
            `user_is_active` BOOLEAN DEFAULT TRUE,
            `must_change_password` BOOLEAN DEFAULT FALSE,
            `last_login` DATETIME NULL,
            `permissions` TEXT NULL,
            `branch_id` VARCHAR(10) NULL,
            `branch_name` VARCHAR(100) NULL,
            `default_branch_id` VARCHAR(10) NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Branches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `branches` (
            `id` VARCHAR(10) PRIMARY KEY,
            `name` VARCHAR(100) NOT NULL,
            `address` TEXT NULL,
            `phone` VARCHAR(20) NULL,
            `email` VARCHAR(100) NULL,
            `manager_name` VARCHAR(100) NULL,
            `is_active` BOOLEAN DEFAULT TRUE,
            `is_default` BOOLEAN DEFAULT FALSE,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # GRPO Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `grpo_documents` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `po_number` VARCHAR(50) NOT NULL,
            `supplier_code` VARCHAR(20) NOT NULL,
            `supplier_name` VARCHAR(200) NOT NULL,
            `po_date` DATETIME NULL,
            `po_total` DECIMAL(15,2) NULL,
            `status` VARCHAR(20) DEFAULT 'draft',
            `user_id` INT NOT NULL,
            `notes` TEXT NULL,
            `qc_approver_id` INT NULL,
            `qc_approved_at` DATETIME NULL,
            `qc_notes` TEXT NULL,
            `sap_document_number` VARCHAR(50) NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # GRPO Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `grpo_items` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `grpo_document_id` INT NOT NULL,
            `item_code` VARCHAR(50) NOT NULL,
            `item_name` VARCHAR(200) NOT NULL,
            `quantity_ordered` DECIMAL(15,3) NOT NULL,
            `quantity_received` DECIMAL(15,3) NOT NULL,
            `unit_price` DECIMAL(15,4) DEFAULT 0,
            `warehouse_code` VARCHAR(20) NOT NULL,
            `bin_location` VARCHAR(50) NULL,
            `batch_number` VARCHAR(100) NULL,
            `serial_number` VARCHAR(100) NULL,
            `expiration_date` DATE NULL,
            `qc_status` VARCHAR(20) DEFAULT 'pending',
            `qc_notes` TEXT NULL,
            `generated_barcode` VARCHAR(100) NULL,
            `barcode_printed` BOOLEAN DEFAULT FALSE,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Inventory Transfers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `inventory_transfers` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `transfer_request_number` VARCHAR(50) NULL,
            `from_warehouse` VARCHAR(20) NULL,
            `to_warehouse` VARCHAR(20) NULL,
            `status` VARCHAR(20) DEFAULT 'draft',
            `user_id` INT NOT NULL,
            `qc_approver_id` INT NULL,
            `qc_approved_at` DATETIME NULL,
            `qc_notes` TEXT NULL,
            `sap_document_number` VARCHAR(50) NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Inventory Transfer Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `inventory_transfer_items` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `inventory_transfer_id` INT NOT NULL,
            `item_code` VARCHAR(50) NOT NULL,
            `item_name` VARCHAR(200) NOT NULL,
            `quantity` DECIMAL(15,3) NOT NULL,
            `from_bin` VARCHAR(50) NULL,
            `to_bin` VARCHAR(50) NULL,
            `batch_number` VARCHAR(100) NULL,
            `serial_number` VARCHAR(100) NULL,
            `qc_status` VARCHAR(20) DEFAULT 'pending',
            `qc_notes` TEXT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Pick Lists table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `pick_lists` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `sales_order_number` VARCHAR(50) NOT NULL,
            `pick_list_number` VARCHAR(50) NOT NULL,
            `status` VARCHAR(20) DEFAULT 'pending',
            `user_id` INT NOT NULL,
            `approver_id` INT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Inventory Counts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `inventory_counts` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `count_name` VARCHAR(100) NOT NULL,
            `warehouse_code` VARCHAR(20) NOT NULL,
            `status` VARCHAR(20) DEFAULT 'pending',
            `user_id` INT NOT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Barcode Labels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `barcode_labels` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `barcode` VARCHAR(100) NOT NULL UNIQUE,
            `item_code` VARCHAR(50) NOT NULL,
            `item_name` VARCHAR(200) NOT NULL,
            `batch_number` VARCHAR(100) NULL,
            `print_count` INT DEFAULT 0,
            `last_printed` DATETIME NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    logger.info("✅ All tables created successfully")

def create_default_data(cursor):
    """Create default admin user and branch"""
    
    # Check if admin user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        password_hash = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO users (
                username, email, password_hash, first_name, last_name, 
                role, user_is_active, must_change_password
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'admin', 'admin@company.com', password_hash, 'System', 'Administrator',
            'admin', True, True
        ))
        logger.info("✅ Created default admin user")
    
    # Check if default branch exists
    cursor.execute("SELECT COUNT(*) FROM branches")
    branch_count = cursor.fetchone()[0]
    
    if branch_count == 0:
        cursor.execute("""
            INSERT INTO branches (id, name, is_active, is_default)
            VALUES (%s, %s, %s, %s)
        """, ('MAIN', 'Main Branch', True, True))
        logger.info("✅ Created default branch")

def save_env_config(mysql_config):
    """Save MySQL configuration to .env file"""
    
    env_content = f"""# MySQL Database Configuration
MYSQL_HOST={mysql_config['host']}
MYSQL_PORT={mysql_config['port']}
MYSQL_USER={mysql_config['user']}
MYSQL_PASSWORD={mysql_config['password']}
MYSQL_DATABASE={mysql_config['database']}

# Database URL for SQLAlchemy
DATABASE_URL=mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}

# Flask Configuration
SESSION_SECRET=your-secret-key-here

# SAP B1 Configuration (Optional)
SAP_B1_SERVER=https://192.168.0.194:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=1422
SAP_B1_COMPANY_DB=EINV-TESTDB-LIVE-HUST
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logger.info("✅ Configuration saved to .env file")

if __name__ == "__main__":
    logger.info("🚀 MySQL Database Setup for Warehouse Management System")
    logger.info("=" * 60)
    
    success = setup_mysql()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("🎉 MySQL setup completed successfully!")
        logger.info("Your database is ready for the warehouse management system.")
        logger.info("Default login credentials: admin / admin123")
        logger.info("Please restart the Flask application to use MySQL.")
        logger.info("=" * 60)
    else:
        logger.error("❌ MySQL setup failed. Please check the errors above.")