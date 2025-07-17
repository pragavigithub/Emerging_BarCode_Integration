#!/usr/bin/env python3
"""
MySQL Local Setup Script
This script helps you set up MySQL database for local development
"""

import os
import sys
import getpass
import logging

# Try to import MySQL connectors
try:
    import pymysql
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_mysql_packages():
    """Install required MySQL packages"""
    logger.info("Installing MySQL packages...")
    
    packages = ['pymysql', 'mysql-connector-python']
    
    for package in packages:
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Installed {package}")
            else:
                logger.error(f"❌ Failed to install {package}: {result.stderr}")
        except Exception as e:
            logger.error(f"Error installing {package}: {e}")

def test_mysql_connection(host, user, password, database):
    """Test MySQL connection"""
    try:
        # Try PyMySQL first
        import pymysql
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        connection.close()
        logger.info("✅ PyMySQL connection successful")
        return True
    except Exception as e:
        logger.error(f"PyMySQL connection failed: {e}")
        
        try:
            # Try MySQL Connector
            import mysql.connector
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            connection.close()
            logger.info("✅ MySQL Connector connection successful")
            return True
        except Exception as e2:
            logger.error(f"MySQL Connector also failed: {e2}")
            return False

def create_env_file(host, user, password, database):
    """Create .env file with MySQL configuration"""
    env_content = f"""# MySQL Database Configuration
MYSQL_HOST={host}
MYSQL_USER={user}
MYSQL_PASSWORD={password}
MYSQL_DATABASE={database}

# Optional: Session secret for Flask
SESSION_SECRET=your-secret-key-here

# Optional: SAP B1 Configuration
SAP_B1_SERVER=https://your-sap-server:50000
SAP_B1_USERNAME=your-sap-username
SAP_B1_PASSWORD=your-sap-password
SAP_B1_COMPANY_DB=your-company-database
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logger.info("✅ Created .env file with MySQL configuration")

def main():
    """Main setup function"""
    logger.info("🚀 MySQL Local Setup for Warehouse Management System")
    logger.info("=" * 60)
    
    # Check if MySQL packages are available
    if not MYSQL_AVAILABLE:
        logger.warning("MySQL packages not found. Installing...")
        install_mysql_packages()
        
        # Re-check after installation
        try:
            import pymysql
            import mysql.connector
            logger.info("✅ MySQL packages installed successfully")
        except ImportError:
            logger.error("❌ Failed to install MySQL packages. Please install manually:")
            logger.error("pip install pymysql mysql-connector-python")
            sys.exit(1)
    
    # Get MySQL connection details
    print("\n📋 MySQL Connection Details:")
    host = input("MySQL Host (default: localhost): ").strip() or 'localhost'
    user = input("MySQL Username: ").strip()
    password = getpass.getpass("MySQL Password: ")
    database = input("Database Name (default: warehouse_wms): ").strip() or 'warehouse_wms'
    
    # Test connection
    logger.info("🔍 Testing MySQL connection...")
    if test_mysql_connection(host, user, password, database):
        logger.info("✅ MySQL connection successful!")
        
        # Create .env file
        create_env_file(host, user, password, database)
        
        # Set environment variables for current session
        os.environ['MYSQL_HOST'] = host
        os.environ['MYSQL_USER'] = user
        os.environ['MYSQL_PASSWORD'] = password
        os.environ['MYSQL_DATABASE'] = database
        
        logger.info("🎉 MySQL setup completed successfully!")
        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("1. Run the migration script: python migrate_inventory_transfers.py")
        logger.info("2. Start your Flask application: python app.py")
        logger.info("3. The application will now use MySQL database")
        
    else:
        logger.error("❌ MySQL connection failed!")
        logger.error("Please check your MySQL server and credentials")
        sys.exit(1)

if __name__ == "__main__":
    main()