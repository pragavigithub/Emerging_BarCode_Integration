#!/usr/bin/env python3
"""
MySQL Environment Setup for WMS
Creates a working MySQL configuration for local development
"""

import os
import platform

def print_header(title):
    """Print formatted header"""
    print("=" * 50)
    print(f" {title}")
    print("=" * 50)

def create_mysql_env():
    """Create a .env file for MySQL configuration"""
    computer_name = platform.node()
    
    # Create .env content optimized for MySQL
    env_content = f"""# WMS MySQL Development Environment
# Computer: {computer_name}
# Database: MySQL

# MySQL Configuration (Primary)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=wms_db
MYSQL_USERNAME=root
MYSQL_PASSWORD=your_mysql_password

# Alternative MySQL configurations:
# For remote MySQL server:
# MYSQL_HOST=192.168.1.100
# For different port:
# MYSQL_PORT=3307
# For specific user:
# MYSQL_USERNAME=wms_user
# MYSQL_PASSWORD=wms_password

# Flask Configuration
SESSION_SECRET=mysql-dev-secret-key-{computer_name}

# SAP B1 Configuration (offline mode - will use mock data)
# Update these when you have actual SAP B1 server
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=Ea@12345
SAP_B1_COMPANY_DB=Test_Hutchinson

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=1

# Database Priority:
# 1. MySQL (if configured above)
# 2. PostgreSQL (if DATABASE_URL exists - for Replit)
# 3. SQLite (automatic fallback)
"""

    try:
        # Backup existing .env
        if os.path.exists('.env'):
            backup_name = '.env.backup.mysql'
            counter = 1
            while os.path.exists(backup_name):
                backup_name = f'.env.backup.mysql.{counter}'
                counter += 1
            
            os.rename('.env', backup_name)
            print(f"Backed up existing .env to {backup_name}")
        
        # Write new .env
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("Created .env file for MySQL development")
        return True
        
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False

def create_mysql_test_script():
    """Create a script to test MySQL connectivity"""
    
    test_script = """#!/usr/bin/env python3
import pymysql
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pymysql():
    try:
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USERNAME', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DATABASE', 'wms_db'),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            result = cursor.fetchone()
            print(f"SUCCESS: PyMySQL connection - MySQL version: {result[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"FAILED: PyMySQL connection - {e}")
        return False

def test_mysql_connector():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USERNAME', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DATABASE', 'wms_db'),
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        result = cursor.fetchone()
        print(f"SUCCESS: MySQL Connector - MySQL version: {result[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"FAILED: MySQL Connector - {e}")
        return False

def main():
    print("Testing MySQL Connection...")
    print("")
    
    # Test both connectors
    pymysql_ok = test_pymysql()
    connector_ok = test_mysql_connector()
    
    if pymysql_ok or connector_ok:
        print("")
        print("MySQL connection successful! You can now run:")
        print("python main.py")
    else:
        print("")
        print("MySQL connection failed. Please check:")
        print("1. MySQL server is running")
        print("2. Database 'wms_db' exists")
        print("3. Username and password are correct")
        print("4. Host and port are accessible")

if __name__ == "__main__":
    main()
"""
    
    try:
        with open('test_mysql_connection.py', 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        print("Created test_mysql_connection.py")
        return True
        
    except Exception as e:
        print(f"Error creating test script: {e}")
        return False

def create_mysql_setup_sql():
    """Create SQL script to set up MySQL database"""
    
    sql_script = """-- MySQL Database Setup for WMS
-- Run this script in MySQL to create the database and user

-- Create database
CREATE DATABASE IF NOT EXISTS wms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (optional - you can use root)
CREATE USER IF NOT EXISTS 'wms_user'@'localhost' IDENTIFIED BY 'wms_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON wms_db.* TO 'wms_user'@'localhost';

-- Grant permissions to root as well
GRANT ALL PRIVILEGES ON wms_db.* TO 'root'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Use the database
USE wms_db;

-- Verify setup
SELECT 'Database setup complete!' as status;
SHOW DATABASES LIKE 'wms_db';
"""
    
    try:
        with open('setup_mysql_database.sql', 'w', encoding='utf-8') as f:
            f.write(sql_script)
        
        print("Created setup_mysql_database.sql")
        return True
        
    except Exception as e:
        print(f"Error creating SQL script: {e}")
        return False

def show_mysql_instructions():
    """Show MySQL setup instructions"""
    print("")
    print("MySQL Setup Instructions:")
    print("")
    print("1. Install MySQL Server (if not already installed)")
    print("   - Download from: https://dev.mysql.com/downloads/mysql/")
    print("   - Or use package manager: brew install mysql (Mac) / apt install mysql-server (Ubuntu)")
    print("")
    print("2. Start MySQL service")
    print("   - Windows: Start MySQL service from Services")
    print("   - Mac: brew services start mysql")
    print("   - Linux: sudo systemctl start mysql")
    print("")
    print("3. Create database and user")
    print("   - Run: mysql -u root -p")
    print("   - Execute: source setup_mysql_database.sql")
    print("   - Or manually create database: CREATE DATABASE wms_db;")
    print("")
    print("4. Update .env file with your MySQL credentials")
    print("   - Set MYSQL_PASSWORD to your actual MySQL password")
    print("   - Adjust MYSQL_USERNAME if needed")
    print("")
    print("5. Test the connection")
    print("   - Run: python test_mysql_connection.py")
    print("")
    print("6. Start WMS application")
    print("   - Run: python main.py")
    print("   - Open browser: http://localhost:5000")

def main():
    """Main setup function"""
    print_header("WMS MySQL Environment Setup")
    
    success_count = 0
    
    # Create .env file
    if create_mysql_env():
        success_count += 1
    
    # Create test script
    if create_mysql_test_script():
        success_count += 1
    
    # Create SQL setup script
    if create_mysql_setup_sql():
        success_count += 1
    
    print("")
    print_header("Setup Complete")
    print(f"Successfully completed {success_count}/3 setup steps")
    
    if success_count == 3:
        print("MySQL environment files created!")
        show_mysql_instructions()
    else:
        print("Setup had some issues. You may need to create files manually.")

if __name__ == "__main__":
    main()