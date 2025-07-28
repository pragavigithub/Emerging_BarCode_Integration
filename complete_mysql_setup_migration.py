#!/usr/bin/env python3
"""
Complete MySQL Setup and Migration Script for WMS Application
This single file handles everything: .env creation, database setup, and table creation
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import logging
import secrets
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_session_secret():
    """Generate a secure session secret"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create .env file with MySQL configuration"""
    print("🔧 MySQL Database Configuration")
    print("Please provide your MySQL connection details:")
    
    mysql_host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    mysql_port = input("MySQL Port (default: 3306): ").strip() or "3306"
    mysql_user = input("MySQL Username (default: root): ").strip() or "root"
    mysql_password = input("MySQL Password: ").strip()
    mysql_database = input("MySQL Database Name (default: wms_db_dev): ").strip() or "wms_db_dev"
    
    # Generate session secret
    session_secret = generate_session_secret()
    
    # URL encode password for special characters
    mysql_password_encoded = quote_plus(mysql_password) if mysql_password else mysql_password
    
    # Create DATABASE_URL
    database_url = f"mysql+pymysql://{mysql_user}:{mysql_password_encoded}@{mysql_host}:{mysql_port}/{mysql_database}"
    
    # Create .env file content
    env_content = f"""# Flask Configuration
SESSION_SECRET={session_secret}

# MySQL Database Configuration
MYSQL_HOST={mysql_host}
MYSQL_PORT={mysql_port}
MYSQL_USER={mysql_user}
MYSQL_PASSWORD={mysql_password}
MYSQL_DATABASE={mysql_database}
DATABASE_URL={database_url}

# SAP B1 Integration (Optional - configure if you have SAP B1)
SAP_B1_SERVER=https://192.168.0.194:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=1422
SAP_B1_COMPANY_DB=EINV-TESTDB-LIVE-HUST
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        logger.info("✅ .env file created successfully")
        return {
            'host': mysql_host,
            'port': int(mysql_port),
            'user': mysql_user,
            'password': mysql_password,
            'database': mysql_database
        }
    except Exception as e:
        logger.error(f"❌ Failed to create .env file: {e}")
        return None

def create_database_and_user(config):
    """Create database and user if they don't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        logger.info(f"✅ Database '{config['database']}' created/verified")
        
        # Grant privileges (if needed)
        cursor.execute(f"GRANT ALL PRIVILEGES ON {config['database']}.* TO '{config['user']}'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        logger.error(f"❌ Database creation error: {e}")
        return False

def create_all_tables(config):
    """Create all required tables for WMS application"""
    try:
        # Connect to the specific database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        logger.info("🔧 Creating WMS database tables...")
        
        # 1. Create branches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                id VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Branches table created")
        
        # Insert default branch
        cursor.execute("""
            INSERT IGNORE INTO branches (id, name, address, is_active, is_default) 
            VALUES ('HQ001', 'Head Office', 'Main Branch Office', TRUE, TRUE)
        """)
        
        # 2. Create users table
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
                user_is_active BOOLEAN DEFAULT TRUE,
                must_change_password BOOLEAN DEFAULT FALSE,
                last_login TIMESTAMP NULL,
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (branch_id) REFERENCES branches(id),
                FOREIGN KEY (default_branch_id) REFERENCES branches(id)
            )
        """)
        logger.info("✅ Users table created")
        
        # 3. Create GRPO documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grpo_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                po_number VARCHAR(20) NOT NULL,
                sap_document_number VARCHAR(20),
                supplier_code VARCHAR(50),
                supplier_name VARCHAR(200),
                po_date TIMESTAMP NULL,
                po_total DECIMAL(15,2),
                status VARCHAR(20) DEFAULT 'draft',
                notes TEXT,
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ GRPO documents table created")
        
        # 4. Create GRPO items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grpo_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                grpo_document_id INT NOT NULL,
                item_code VARCHAR(50) NOT NULL,
                item_name VARCHAR(200),
                ordered_quantity DECIMAL(15,3) DEFAULT 0,
                received_quantity DECIMAL(15,3) DEFAULT 0,
                unit_price DECIMAL(15,2) DEFAULT 0,
                uom VARCHAR(10),
                batch_number VARCHAR(50),
                serial_number VARCHAR(50),
                expiration_date DATE,
                bin_location VARCHAR(50),
                warehouse_code VARCHAR(10),
                supplier_barcode VARCHAR(100),
                generated_barcode VARCHAR(100),
                barcode_printed BOOLEAN DEFAULT FALSE,
                qc_status VARCHAR(20) DEFAULT 'pending',
                po_line_number INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grpo_document_id) REFERENCES grpo_documents(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ GRPO items table created")
        
        # 5. Create inventory transfers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_transfers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transfer_number VARCHAR(50) NOT NULL,
                transfer_request_number VARCHAR(50),
                from_warehouse VARCHAR(50),
                to_warehouse VARCHAR(50),
                from_warehouse_code VARCHAR(10),
                to_warehouse_code VARCHAR(10),
                status VARCHAR(20) DEFAULT 'draft',
                sap_document_number VARCHAR(50),
                user_id INT,
                qc_approver_id INT,
                qc_approved_at TIMESTAMP NULL,
                qc_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (qc_approver_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ Inventory transfers table created")
        
        # 6. Create inventory transfer items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_transfer_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transfer_id INT NOT NULL,
                item_code VARCHAR(50) NOT NULL,
                item_name VARCHAR(200),
                requested_quantity DECIMAL(15,3) DEFAULT 0,
                transferred_quantity DECIMAL(15,3) DEFAULT 0,
                remaining_quantity DECIMAL(15,3) DEFAULT 0,
                uom VARCHAR(10),
                from_bin_location VARCHAR(50),
                to_bin_location VARCHAR(50),
                batch_number VARCHAR(50),
                serial_number VARCHAR(50),
                qc_status VARCHAR(20) DEFAULT 'pending',
                qc_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transfer_id) REFERENCES inventory_transfers(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Inventory transfer items table created")
        
        # 7. Create pick lists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pick_lists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pick_list_number VARCHAR(50) NOT NULL,
                sales_order_number VARCHAR(50),
                customer_code VARCHAR(50),
                customer_name VARCHAR(200),
                priority VARCHAR(20) DEFAULT 'normal',
                status VARCHAR(20) DEFAULT 'draft',
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ Pick lists table created")
        
        # 8. Create pick list items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pick_list_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pick_list_id INT NOT NULL,
                item_code VARCHAR(50) NOT NULL,
                item_name VARCHAR(200),
                ordered_quantity DECIMAL(15,3) DEFAULT 0,
                picked_quantity DECIMAL(15,3) DEFAULT 0,
                uom VARCHAR(10),
                bin_location VARCHAR(50),
                batch_number VARCHAR(50),
                serial_number VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Pick list items table created")
        
        # 9. Create inventory counts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_counts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                count_number VARCHAR(50) NOT NULL,
                warehouse_code VARCHAR(10),
                count_date DATE,
                status VARCHAR(20) DEFAULT 'draft',
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ Inventory counts table created")
        
        # 10. Create inventory count items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_count_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                count_id INT NOT NULL,
                item_code VARCHAR(50) NOT NULL,
                item_name VARCHAR(200),
                bin_location VARCHAR(50),
                batch_number VARCHAR(50),
                system_quantity DECIMAL(15,3) DEFAULT 0,
                counted_quantity DECIMAL(15,3) DEFAULT 0,
                variance_quantity DECIMAL(15,3) DEFAULT 0,
                uom VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (count_id) REFERENCES inventory_counts(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Inventory count items table created")
        
        # 11. Create barcode labels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barcode_labels (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_code VARCHAR(50) NOT NULL,
                item_name VARCHAR(200),
                batch_number VARCHAR(50),
                barcode VARCHAR(100) NOT NULL,
                label_format VARCHAR(20) DEFAULT 'standard',
                printed_count INT DEFAULT 0,
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ Barcode labels table created")
        
        # 12. Create bin scanning logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bin_scanning_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bin_code VARCHAR(50) NOT NULL,
                warehouse_code VARCHAR(10),
                items_found INT DEFAULT 0,
                scan_result TEXT,
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ Bin scanning logs table created")
        
        # 13. Create warehouses table (for caching SAP data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warehouses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                warehouse_code VARCHAR(10) UNIQUE NOT NULL,
                warehouse_name VARCHAR(100),
                business_place_id INT,
                default_bin INT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Warehouses table created")
        
        # 14. Create bin locations table (for caching SAP data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bin_locations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                abs_entry INT UNIQUE,
                warehouse_code VARCHAR(10),
                bin_code VARCHAR(50) UNIQUE NOT NULL,
                sublevel1 VARCHAR(50),
                sublevel2 VARCHAR(50),
                sublevel3 VARCHAR(50),
                sublevel4 VARCHAR(50),
                is_system_bin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Bin locations table created")
        
        # Create default admin user
        from werkzeug.security import generate_password_hash
        admin_password_hash = generate_password_hash('admin123')
        
        cursor.execute("""
            INSERT IGNORE INTO users 
            (username, email, password_hash, first_name, last_name, role, branch_id, default_branch_id, user_is_active)
            VALUES ('admin', 'admin@wms.local', %s, 'System', 'Administrator', 'admin', 'HQ001', 'HQ001', TRUE)
        """, (admin_password_hash,))
        logger.info("✅ Default admin user created (username: admin, password: admin123)")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info("🎉 All database tables created successfully!")
        return True
        
    except Error as e:
        logger.error(f"❌ Table creation error: {e}")
        return False

def test_database_connection(config):
    """Test database connection"""
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        logger.info(f"✅ Database connection successful! Found {user_count} users.")
        return True
        
    except Error as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 WMS MySQL Complete Setup and Migration")
    print("=" * 50)
    print("This script will:")
    print("1. Create .env file with MySQL configuration")
    print("2. Create MySQL database if it doesn't exist")
    print("3. Create all required tables and indexes")
    print("4. Create default admin user")
    print("5. Test the database connection")
    print()
    
    if input("Continue with setup? (y/n): ").lower() != 'y':
        print("Setup cancelled.")
        return
    
    # Step 1: Create .env file
    print("\n1. Creating .env file...")
    config = create_env_file()
    if not config:
        print("❌ Failed to create .env file. Exiting.")
        return
    
    # Step 2: Create database
    print("\n2. Creating database...")
    if not create_database_and_user(config):
        print("❌ Failed to create database. Exiting.")
        return
    
    # Step 3: Create tables
    print("\n3. Creating database tables...")
    if not create_all_tables(config):
        print("❌ Failed to create tables. Exiting.")
        return
    
    # Step 4: Test connection
    print("\n4. Testing database connection...")
    if test_database_connection(config):
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Login with username: admin, password: admin123")
        print("3. Change the admin password on first login")
        print("\nYour application is ready to use!")
    else:
        print("❌ Setup completed but connection test failed.")
        print("Please check your MySQL configuration and try again.")

if __name__ == "__main__":
    main()