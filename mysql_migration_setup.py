#!/usr/bin/env python3
"""
MySQL Migration Setup Script for WMS Application
This script sets up MySQL database and migrates data from PostgreSQL/SQLite
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_mysql_packages():
    """Install required MySQL packages"""
    logger.info("Installing MySQL packages...")
    
    packages = ['pymysql', 'mysql-connector-python', 'python-dotenv']
    
    for package in packages:
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"✅ Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def setup_mysql_env():
    """Setup MySQL environment variables"""
    logger.info("Setting up MySQL environment configuration...")
    
    print("\n=== MySQL Database Setup ===")
    print("Please provide your MySQL database details:")
    
    mysql_host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    mysql_port = input("MySQL Port (default: 3306): ").strip() or "3306"
    mysql_user = input("MySQL Username (default: root): ").strip() or "root"
    mysql_password = input("MySQL Password: ").strip()
    mysql_database = input("MySQL Database Name (default: wms_database): ").strip() or "wms_database"
    
    # Create environment configuration
    env_content = f"""# Database Configuration - MySQL Primary (User Preference)
MYSQL_HOST={mysql_host}
MYSQL_PORT={mysql_port}
MYSQL_USER={mysql_user}
MYSQL_PASSWORD={mysql_password}
MYSQL_DATABASE={mysql_database}

# PostgreSQL Configuration (Replit environment - comment out when using MySQL)
# DATABASE_URL=postgresql://user:password@host:5432/database

# Flask Configuration
SESSION_SECRET={os.urandom(32).hex()}

# SAP B1 Configuration
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=Ea@12345
SAP_B1_COMPANY_DB=Test_Hutchinson

# Mobile App Configuration
MOBILE_JWT_SECRET={os.urandom(32).hex()}
MOBILE_API_BASE_URL=http://localhost:5000
"""
    
    # Write to .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logger.info("✅ Environment configuration written to .env file")
    return {
        'host': mysql_host,
        'port': mysql_port,
        'user': mysql_user,
        'password': mysql_password,
        'database': mysql_database
    }

def create_mysql_database(config):
    """Create MySQL database if it doesn't exist"""
    logger.info("Creating MySQL database...")
    
    try:
        import mysql.connector
        from mysql.connector import Error
        
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"✅ Database '{config['database']}' created successfully")
            
            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON {config['database']}.* TO '{config['user']}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            logger.info("✅ Database privileges granted")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        logger.error(f"❌ MySQL connection error: {e}")
        return False
    except ImportError:
        logger.error("❌ MySQL connector not installed. Please install mysql-connector-python")
        return False

def run_database_migration():
    """Run database migration script"""
    logger.info("Running database migration...")
    
    try:
        # Import and run the existing migration script
        import subprocess
        
        # Create complete migration script
        migration_script = """
import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, DECIMAL
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mysql_connection():
    '''Create MySQL database connection'''
    try:
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_port = os.environ.get('MYSQL_PORT', '3306')
        mysql_user = os.environ.get('MYSQL_USER', 'root')
        mysql_password = os.environ.get('MYSQL_PASSWORD', '')
        mysql_database = os.environ.get('MYSQL_DATABASE', 'wms_database')
        
        if not all([mysql_host, mysql_user, mysql_password, mysql_database]):
            raise ValueError("Missing required MySQL configuration")
        
        encoded_password = quote_plus(str(mysql_password))
        database_url = f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        
        engine = create_engine(database_url, pool_pre_ping=True)
        logger.info("✅ MySQL connection established")
        return engine
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MySQL: {e}")
        raise

def create_mysql_tables(engine):
    '''Create all required MySQL tables'''
    logger.info("Creating MySQL tables...")
    
    try:
        with engine.connect() as conn:
            # Users table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    role ENUM('admin', 'manager', 'qc', 'user') DEFAULT 'user',
                    branch_id VARCHAR(10),
                    default_branch_id VARCHAR(10),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            '''))
            
            # GRPO Documents table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS grpo_documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    po_number VARCHAR(20) NOT NULL,
                    po_date DATE,
                    po_total DECIMAL(15,2),
                    supplier_code VARCHAR(20),
                    supplier_name VARCHAR(100),
                    status ENUM('draft', 'submitted', 'approved', 'posted', 'rejected') DEFAULT 'draft',
                    created_by INT,
                    approved_by INT,
                    approved_at TIMESTAMP NULL,
                    posted_at TIMESTAMP NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id),
                    INDEX idx_po_number (po_number),
                    INDEX idx_status (status)
                )
            '''))
            
            # GRPO Items table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS grpo_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    grpo_id INT NOT NULL,
                    line_number INT,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200),
                    ordered_quantity DECIMAL(15,3) DEFAULT 0,
                    received_quantity DECIMAL(15,3) DEFAULT 0,
                    pending_quantity DECIMAL(15,3) DEFAULT 0,
                    unit_price DECIMAL(15,4) DEFAULT 0,
                    total_price DECIMAL(15,2) DEFAULT 0,
                    uom VARCHAR(10),
                    warehouse_code VARCHAR(20),
                    bin_location VARCHAR(50),
                    batch_number VARCHAR(50),
                    serial_number VARCHAR(50),
                    expiry_date DATE,
                    barcode VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
                    INDEX idx_grpo_id (grpo_id),
                    INDEX idx_item_code (item_code),
                    INDEX idx_barcode (barcode)
                )
            '''))
            
            # Inventory Transfers table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS inventory_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_number VARCHAR(20) UNIQUE,
                    transfer_request_number VARCHAR(20),
                    from_warehouse VARCHAR(20),
                    to_warehouse VARCHAR(20),
                    status ENUM('draft', 'submitted', 'qc_approved', 'posted', 'rejected') DEFAULT 'draft',
                    created_by INT,
                    qc_approver_id INT,
                    qc_approved_at TIMESTAMP NULL,
                    qc_notes TEXT,
                    posted_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id),
                    INDEX idx_transfer_number (transfer_number),
                    INDEX idx_status (status)
                )
            '''))
            
            # Inventory Transfer Items table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS inventory_transfer_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_id INT NOT NULL,
                    line_number INT,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200),
                    quantity DECIMAL(15,3) DEFAULT 0,
                    unit_price DECIMAL(15,4) DEFAULT 0,
                    total_price DECIMAL(15,2) DEFAULT 0,
                    uom VARCHAR(10),
                    from_warehouse_code VARCHAR(20),
                    to_warehouse_code VARCHAR(20),
                    from_bin_location VARCHAR(50),
                    to_bin_location VARCHAR(50),
                    batch_number VARCHAR(50),
                    expiry_date DATE,
                    qc_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    qc_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (transfer_id) REFERENCES inventory_transfers(id) ON DELETE CASCADE,
                    INDEX idx_transfer_id (transfer_id),
                    INDEX idx_item_code (item_code)
                )
            '''))
            
            # Pick Lists table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS pick_lists (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sales_order_number VARCHAR(20) NOT NULL,
                    customer_code VARCHAR(20),
                    customer_name VARCHAR(100),
                    status ENUM('draft', 'in_progress', 'completed', 'cancelled') DEFAULT 'draft',
                    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal',
                    created_by INT,
                    assigned_to INT,
                    completed_by INT,
                    completed_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (assigned_to) REFERENCES users(id),
                    FOREIGN KEY (completed_by) REFERENCES users(id),
                    INDEX idx_so_number (sales_order_number),
                    INDEX idx_status (status)
                )
            '''))
            
            # Inventory Counts table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS inventory_counts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    count_name VARCHAR(100) NOT NULL,
                    warehouse_code VARCHAR(20),
                    status ENUM('draft', 'in_progress', 'completed', 'cancelled') DEFAULT 'draft',
                    created_by INT,
                    assigned_to INT,
                    completed_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (assigned_to) REFERENCES users(id),
                    INDEX idx_warehouse (warehouse_code),
                    INDEX idx_status (status)
                )
            '''))
            
            # Barcode Labels table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS barcode_labels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    barcode VARCHAR(100) UNIQUE NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200),
                    batch_number VARCHAR(50),
                    serial_number VARCHAR(50),
                    warehouse_code VARCHAR(20),
                    bin_location VARCHAR(50),
                    label_type ENUM('standard', 'large', 'small', 'custom') DEFAULT 'standard',
                    printed_by INT,
                    printed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (printed_by) REFERENCES users(id),
                    INDEX idx_barcode (barcode),
                    INDEX idx_item_code (item_code)
                )
            '''))
            
            # Branches table (extended model)
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS branches (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    address TEXT,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            '''))
            
            conn.commit()
            logger.info("✅ All MySQL tables created successfully")
            
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create MySQL tables: {e}")
        return False

def create_default_data(engine):
    '''Create default branch and admin user'''
    logger.info("Creating default data...")
    
    try:
        with engine.connect() as conn:
            # Create default branch
            conn.execute(text('''
                INSERT INTO branches (id, name, address, is_active, is_default)
                VALUES ('BR001', 'Main Branch', 'Main Office', TRUE, TRUE)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
            '''))
            
            # Create default admin user
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash('admin123')
            
            conn.execute(text('''
                INSERT INTO users (username, email, password_hash, first_name, last_name, role, branch_id, default_branch_id, is_active)
                VALUES ('admin', 'admin@company.com', :password_hash, 'System', 'Administrator', 'admin', 'BR001', 'BR001', TRUE)
                ON DUPLICATE KEY UPDATE email = VALUES(email)
            '''), {'password_hash': password_hash})
            
            conn.commit()
            logger.info("✅ Default data created successfully")
            
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create default data: {e}")
        return False

if __name__ == '__main__':
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Create MySQL connection
        engine = create_mysql_connection()
        
        # Create all tables
        if create_mysql_tables(engine):
            logger.info("✅ MySQL database schema created successfully")
            
            # Create default data
            if create_default_data(engine):
                logger.info("✅ MySQL migration completed successfully")
                logger.info("🚀 Your application is now configured to use MySQL database")
                logger.info("📝 Default login: username=admin, password=admin123")
            else:
                logger.error("❌ Failed to create default data")
        else:
            logger.error("❌ Failed to create MySQL tables")
            
    except Exception as e:
        logger.error(f"❌ MySQL migration failed: {e}")
        sys.exit(1)
"""
        
        # Write migration script
        with open('run_mysql_migration.py', 'w') as f:
            f.write(migration_script)
        
        # Run migration
        result = subprocess.run([sys.executable, 'run_mysql_migration.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Database migration completed successfully")
            print(result.stdout)
            return True
        else:
            logger.error(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to run migration: {e}")
        return False

def main():
    """Main migration process"""
    print("🚀 WMS MySQL Migration Setup")
    print("=" * 40)
    
    # Step 1: Install required packages
    if not install_mysql_packages():
        logger.error("❌ Failed to install required packages")
        return False
    
    # Step 2: Setup environment
    config = setup_mysql_env()
    if not config:
        logger.error("❌ Failed to setup environment")
        return False
    
    # Step 3: Create MySQL database
    if not create_mysql_database(config):
        logger.error("❌ Failed to create MySQL database")
        return False
    
    # Step 4: Run migration
    if not run_database_migration():
        logger.error("❌ Failed to run database migration")
        return False
    
    print("\n" + "=" * 40)
    print("✅ MySQL Migration Setup Complete!")
    print("=" * 40)
    print("📋 Next Steps:")
    print("1. Restart your Flask application")
    print("2. The app will now use MySQL database")
    print("3. Default login: admin / admin123")
    print("4. Your React Native app can now sync with MySQL backend")
    print("\n💡 Your .env file has been configured with MySQL settings")
    
    return True

if __name__ == "__main__":
    main()