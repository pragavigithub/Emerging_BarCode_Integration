#!/usr/bin/env python3
"""
MySQL Database Migration and Setup Script
==========================================

This script provides comprehensive MySQL database setup, migration, and repair
functionality for the Warehouse Management System.

Features:
- MySQL database connection setup
- Complete schema creation
- Missing column detection and addition
- Data migration from SQLite/PostgreSQL
- Environment configuration

Usage: python mysql_migration_fix.py
"""

import os
import sys
import logging
import pymysql
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MySQLMigrationManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def setup_mysql_environment(self):
        """Interactive MySQL environment setup"""
        logger.info("🔧 MySQL Environment Setup")
        logger.info("=" * 50)
        
        # Get MySQL connection details
        mysql_config = {}
        
        mysql_config['host'] = input("MySQL Host (default: localhost): ").strip() or 'localhost'
        mysql_config['port'] = int(input("MySQL Port (default: 3306): ").strip() or '3306')
        mysql_config['user'] = input("MySQL Username (default: root): ").strip() or 'root'
        mysql_config['password'] = input("MySQL Password(default: root@123): ").strip() or 'root@123'
        mysql_config['database'] = input("Database Name (default: wms_db_dev): ").strip() or 'wms_db_dev'
        
        # Test connection
        logger.info("🔍 Testing MySQL connection...")
        if self.test_mysql_connection(mysql_config):
            logger.info("✅ MySQL connection successful!")
            self.save_mysql_environment(mysql_config)
            return mysql_config
        else:
            logger.error("❌ MySQL connection failed!")
            return None
    
    def test_mysql_connection(self, config):
        """Test MySQL connection"""
        try:
            connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                charset='utf8mb4',
                autocommit=True
            )
            
            # Create database if it doesn't exist
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            connection.close()
            
            # Test connection to the database
            connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset='utf8mb4',
                autocommit=True
            )
            connection.close()
            return True
            
        except Exception as e:
            logger.error(f"MySQL connection error: {e}")
            return False
    
    def save_mysql_environment(self, config):
        """Save MySQL configuration to .env file"""
        env_content = f"""# MySQL Database Configuration
MYSQL_HOST={config['host']}
MYSQL_PORT={config['port']}
MYSQL_USER={config['user']}
MYSQL_PASSWORD={config['password']}
MYSQL_DATABASE={config['database']}

# Database URL for SQLAlchemy
DATABASE_URL=mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}

# Flask Configuration
SESSION_SECRET=your-secret-key-here

# SAP B1 Configuration (Optional)
SAP_B1_SERVER=https://192.168.0.194:50000/b1s/v1
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=1422
SAP_B1_COMPANY_DB=EINV-TESTDB-LIVE-HUST
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        logger.info("✅ MySQL configuration saved to .env file")
    
    def connect_mysql(self):
        """Connect to MySQL database"""
        try:
            # Try to get config from environment
            config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', 'root@123'),
                'database': os.getenv('MYSQL_DATABASE', 'wms_db_dev')
            }
            
            self.connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset='utf8mb4',
                autocommit=False
            )
            
            self.cursor = self.connection.cursor()
            logger.info(f"✅ Connected to MySQL database: {config['database']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ MySQL connection failed: {e}")
            return False
    
    def check_table_exists(self, table_name):
        """Check if table exists"""
        try:
            self.cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking table {table_name}: {e}")
            return False
    
    def check_column_exists(self, table_name, column_name):
        """Check if column exists in table"""
        try:
            self.cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking column {table_name}.{column_name}: {e}")
            return False
    
    def create_users_table(self):
        """Create users table with all required columns"""
        logger.info("🔧 Creating users table...")
        
        sql = """
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
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_username` (`username`),
            INDEX `idx_email` (`email`),
            INDEX `idx_role` (`role`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(sql)
            logger.info("✅ Users table created successfully")
        except Exception as e:
            logger.error(f"Error creating users table: {e}")
    
    def create_branches_table(self):
        """Create branches table"""
        logger.info("🔧 Creating branches table...")
        
        sql = """
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
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_name` (`name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(sql)
            logger.info("✅ Branches table created successfully")
        except Exception as e:
            logger.error(f"Error creating branches table: {e}")
    
    def create_grpo_tables(self):
        """Create GRPO related tables"""
        logger.info("🔧 Creating GRPO tables...")
        
        # GRPO Documents table
        grpo_docs_sql = """
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
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_po_number` (`po_number`),
            INDEX `idx_status` (`status`),
            INDEX `idx_user_id` (`user_id`),
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
            FOREIGN KEY (`qc_approver_id`) REFERENCES `users`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # GRPO Items table
        grpo_items_sql = """
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
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_grpo_document_id` (`grpo_document_id`),
            INDEX `idx_item_code` (`item_code`),
            INDEX `idx_qc_status` (`qc_status`),
            FOREIGN KEY (`grpo_document_id`) REFERENCES `grpo_documents`(`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(grpo_docs_sql)
            self.cursor.execute(grpo_items_sql)
            logger.info("✅ GRPO tables created successfully")
        except Exception as e:
            logger.error(f"Error creating GRPO tables: {e}")
    
    def create_inventory_transfer_tables(self):
        """Create inventory transfer tables"""
        logger.info("🔧 Creating inventory transfer tables...")
        
        # Inventory Transfers table
        transfers_sql = """
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
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_transfer_request_number` (`transfer_request_number`),
            INDEX `idx_status` (`status`),
            INDEX `idx_user_id` (`user_id`),
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
            FOREIGN KEY (`qc_approver_id`) REFERENCES `users`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # Inventory Transfer Items table
        transfer_items_sql = """
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
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_inventory_transfer_id` (`inventory_transfer_id`),
            INDEX `idx_item_code` (`item_code`),
            INDEX `idx_qc_status` (`qc_status`),
            FOREIGN KEY (`inventory_transfer_id`) REFERENCES `inventory_transfers`(`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(transfers_sql)
            self.cursor.execute(transfer_items_sql)
            logger.info("✅ Inventory transfer tables created successfully")
        except Exception as e:
            logger.error(f"Error creating inventory transfer tables: {e}")
    
    def create_additional_tables(self):
        """Create additional system tables"""
        logger.info("🔧 Creating additional system tables...")
        
        # Pick Lists table
        pick_lists_sql = """
        CREATE TABLE IF NOT EXISTS `pick_lists` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `sales_order_number` VARCHAR(50) NOT NULL,
            `pick_list_number` VARCHAR(50) NOT NULL,
            `status` VARCHAR(20) DEFAULT 'pending',
            `user_id` INT NOT NULL,
            `approver_id` INT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_sales_order_number` (`sales_order_number`),
            INDEX `idx_status` (`status`),
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # Inventory Counts table
        inventory_counts_sql = """
        CREATE TABLE IF NOT EXISTS `inventory_counts` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `count_name` VARCHAR(100) NOT NULL,
            `warehouse_code` VARCHAR(20) NOT NULL,
            `status` VARCHAR(20) DEFAULT 'pending',
            `user_id` INT NOT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_warehouse_code` (`warehouse_code`),
            INDEX `idx_status` (`status`),
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # Barcode Labels table
        barcode_labels_sql = """
        CREATE TABLE IF NOT EXISTS `barcode_labels` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `barcode` VARCHAR(100) NOT NULL UNIQUE,
            `item_code` VARCHAR(50) NOT NULL,
            `item_name` VARCHAR(200) NOT NULL,
            `batch_number` VARCHAR(100) NULL,
            `print_count` INT DEFAULT 0,
            `last_printed` DATETIME NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_barcode` (`barcode`),
            INDEX `idx_item_code` (`item_code`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(pick_lists_sql)
            self.cursor.execute(inventory_counts_sql)
            self.cursor.execute(barcode_labels_sql)
            logger.info("✅ Additional system tables created successfully")
        except Exception as e:
            logger.error(f"Error creating additional tables: {e}")
    
    def create_default_data(self):
        """Create default admin user and branch"""
        logger.info("🔧 Creating default data...")
        
        # Check if admin user exists
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = self.cursor.fetchone()[0]
        
        if admin_count == 0:
            # Import password hashing
            from werkzeug.security import generate_password_hash
            
            password_hash = generate_password_hash('admin123')
            self.cursor.execute("""
                INSERT INTO users (
                    username, email, password_hash, first_name, last_name, 
                    role, user_is_active, must_change_password
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'admin', 'admin@company.com', password_hash, 'System', 'Administrator',
                'admin', True, True
            ))
            logger.info("✅ Created default admin user (username: admin, password: admin123)")
        
        # Check if default branch exists
        self.cursor.execute("SELECT COUNT(*) FROM branches")
        branch_count = self.cursor.fetchone()[0]
        
        if branch_count == 0:
            self.cursor.execute("""
                INSERT INTO branches (id, name, is_active, is_default)
                VALUES (%s, %s, %s, %s)
            """, ('MAIN', 'Main Branch', True, True))
            logger.info("✅ Created default branch: MAIN")
    
    def add_missing_columns(self):
        """Add any missing columns to existing tables"""
        logger.info("🔧 Checking and adding missing columns...")
        
        # Define required columns for each table
        table_columns = {
            'users': [
                ('user_is_active', 'BOOLEAN DEFAULT TRUE'),
                ('must_change_password', 'BOOLEAN DEFAULT FALSE'),
                ('last_login', 'DATETIME NULL'),
                ('permissions', 'TEXT NULL'),
                ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
                ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                ('first_name', 'VARCHAR(80) DEFAULT ""'),
                ('last_name', 'VARCHAR(80) DEFAULT ""'),
                ('role', 'VARCHAR(20) DEFAULT "user"'),
                ('branch_id', 'VARCHAR(10) NULL'),
                ('branch_name', 'VARCHAR(100) NULL'),
                ('default_branch_id', 'VARCHAR(10) NULL')
            ],
            'grpo_documents': [
                ('po_date', 'DATETIME NULL'),
                ('po_total', 'DECIMAL(15,2) NULL'),
                ('notes', 'TEXT NULL'),
                ('qc_approver_id', 'INT NULL'),
                ('qc_approved_at', 'DATETIME NULL'),
                ('qc_notes', 'TEXT NULL')
            ],
            'inventory_transfers': [
                ('transfer_request_number', 'VARCHAR(50) NULL'),
                ('from_warehouse', 'VARCHAR(20) NULL'),
                ('to_warehouse', 'VARCHAR(20) NULL'),
                ('qc_approver_id', 'INT NULL'),
                ('qc_approved_at', 'DATETIME NULL'),
                ('qc_notes', 'TEXT NULL')
            ],
            'inventory_transfer_items': [
                ('qc_status', 'VARCHAR(20) DEFAULT "pending"'),
                ('qc_notes', 'TEXT NULL'),
                ('serial_number', 'VARCHAR(100) NULL')
            ]
        }
        
        for table_name, columns in table_columns.items():
            if self.check_table_exists(table_name):
                for column_name, column_type in columns:
                    if not self.check_column_exists(table_name, column_name):
                        try:
                            self.cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_type}")
                            logger.info(f"✅ Added column: {table_name}.{column_name}")
                        except Exception as e:
                            logger.error(f"❌ Error adding column {table_name}.{column_name}: {e}")
                    else:
                        logger.info(f"✓ Column exists: {table_name}.{column_name}")
    
    def run_migration(self):
        """Run complete MySQL migration"""
        logger.info("🚀 Starting MySQL Migration...")
        logger.info("=" * 60)
        
        try:
            # Connect to MySQL
            if not self.connect_mysql():
                logger.error("❌ Cannot proceed without MySQL connection")
                return False
            
            # Create all tables
            self.create_users_table()
            self.create_branches_table()
            self.create_grpo_tables()
            self.create_inventory_transfer_tables()
            self.create_additional_tables()
            
            # Add missing columns to existing tables
            self.add_missing_columns()
            
            # Create default data
            self.create_default_data()
            
            # Commit all changes
            self.connection.commit()
            
            logger.info("=" * 60)
            logger.info("✅ MySQL Migration completed successfully!")
            logger.info("✅ All tables created with proper schema")
            logger.info("✅ Default admin user and branch created")
            logger.info("🎉 MySQL database is ready for use!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()

def main():
    """Main function"""
    logger.info("🚀 MySQL Database Migration Tool")
    logger.info("=" * 50)
    
    migration_manager = MySQLMigrationManager()
    
    # Check if we have MySQL configuration
    if not os.getenv('MYSQL_HOST'):
        logger.info("MySQL environment not configured. Setting up...")
        config = migration_manager.setup_mysql_environment()
        if not config:
            logger.error("❌ MySQL setup failed. Exiting.")
            return
    
    # Run migration
    success = migration_manager.run_migration()
    
    if success:
        logger.info("\n" + "=" * 50)
        logger.info("🎉 Migration completed successfully!")
        logger.info("Your MySQL database is now ready.")
        logger.info("Default login: admin / admin123")
        logger.info("=" * 50)
    else:
        logger.error("❌ Migration failed. Please check the errors above.")

if __name__ == "__main__":
    main()