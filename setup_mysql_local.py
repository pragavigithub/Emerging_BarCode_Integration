#!/usr/bin/env python3
"""
MySQL Local Setup Script for WMS
Run this script after installing MySQL locally to set up the database
"""

import os
import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mysql_database():
    """Set up MySQL database for local development"""
    
    # Default MySQL connection settings
    mysql_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': input("Enter MySQL root password: "),
        'database': 'wms_db_dev'
    }
    
    try:
        # Connect to MySQL server (without specifying database first)
        connection = mysql.connector.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['user'],
            password=mysql_config['password']
        )
        
        if connection.is_connected():
            logger.info("✅ Connected to MySQL server")
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_config['database']}")
            logger.info(f"✅ Database '{mysql_config['database']}' created/verified")
            
            # Select the database
            cursor.execute(f"USE {mysql_config['database']}")
            
            # Create branches table
            create_branches_table = """
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
            """
            cursor.execute(create_branches_table)
            logger.info("✅ Branches table created")
            
            # Insert default branch
            insert_default_branch = """
            INSERT IGNORE INTO branches (id, name, address, is_active, is_default) 
            VALUES ('BR001', 'Main Branch', 'Main Office', TRUE, TRUE)
            """
            cursor.execute(insert_default_branch)
            
            # Create users table (basic structure)
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256),
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                role VARCHAR(20) DEFAULT 'user',
                branch_id VARCHAR(10),
                default_branch_id VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_users_table)
            logger.info("✅ Users table created")
            
            # Create other essential tables
            create_grpo_documents_table = """
            CREATE TABLE IF NOT EXISTS grpo_documents (
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
            """
            cursor.execute(create_grpo_documents_table)
            logger.info("✅ GRPO documents table created")
            
            create_grpo_items_table = """
            CREATE TABLE IF NOT EXISTS grpo_items (
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
            """
            cursor.execute(create_grpo_items_table)
            logger.info("✅ GRPO items table created")
            
            create_inventory_transfers_table = """
            CREATE TABLE IF NOT EXISTS inventory_transfers (
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
            """
            cursor.execute(create_inventory_transfers_table)
            logger.info("✅ Inventory transfers table created")
            
            create_inventory_transfer_items_table = """
            CREATE TABLE IF NOT EXISTS inventory_transfer_items (
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
            """
            cursor.execute(create_inventory_transfer_items_table)
            logger.info("✅ Inventory transfer items table created")
            
            # Commit changes
            connection.commit()
            logger.info("✅ All tables created successfully!")
            
            # Update .env file
            update_env_file(mysql_config)
            
            logger.info("🎉 MySQL database setup completed!")
            logger.info("📝 Updated .env file with MySQL configuration")
            logger.info("🚀 You can now run your application with MySQL")
            
    except Error as e:
        logger.error(f"❌ MySQL Error: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("MySQL connection closed")
    
    return True

def update_env_file(mysql_config):
    """Update .env file with MySQL configuration"""
    try:
        # Read current .env file
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update MySQL configuration lines
        updated_lines = []
        mysql_configured = False
        
        for line in lines:
            if line.strip().startswith('# MYSQL_HOST=') or line.strip().startswith('MYSQL_HOST='):
                updated_lines.append(f"MYSQL_HOST={mysql_config['host']}\n")
                mysql_configured = True
            elif line.strip().startswith('# MYSQL_USER=') or line.strip().startswith('MYSQL_USER='):
                updated_lines.append(f"MYSQL_USER={mysql_config['user']}\n")
            elif line.strip().startswith('# MYSQL_PASSWORD=') or line.strip().startswith('MYSQL_PASSWORD='):
                updated_lines.append(f"MYSQL_PASSWORD={mysql_config['password']}\n")
            elif line.strip().startswith('# MYSQL_DATABASE=') or line.strip().startswith('MYSQL_DATABASE='):
                updated_lines.append(f"MYSQL_DATABASE={mysql_config['database']}\n")
            else:
                updated_lines.append(line)
        
        # If MySQL config wasn't found, add it
        if not mysql_configured:
            updated_lines.extend([
                f"\n# MySQL Configuration (Local Development)\n",
                f"MYSQL_HOST={mysql_config['host']}\n",
                f"MYSQL_USER={mysql_config['user']}\n",
                f"MYSQL_PASSWORD={mysql_config['password']}\n",
                f"MYSQL_DATABASE={mysql_config['database']}\n"
            ])
        
        # Write updated .env file
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        logger.info("✅ .env file updated with MySQL configuration")
        
    except Exception as e:
        logger.error(f"❌ Error updating .env file: {e}")

if __name__ == "__main__":
    print("🔧 MySQL Local Setup for WMS Application")
    print("This script will create the database and tables for local development")
    print("Make sure MySQL is installed and running on your system")
    print()
    
    if input("Continue with setup? (y/n): ").lower() == 'y':
        success = setup_mysql_database()
        if success:
            print("\n✅ Setup completed! You can now run the WMS application.")
        else:
            print("\n❌ Setup failed. Please check MySQL installation and try again.")
    else:
        print("Setup cancelled.")