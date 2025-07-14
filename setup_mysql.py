#!/usr/bin/env python3
"""
MySQL Setup Script for WMS Application
This script helps configure MySQL database for the warehouse management system.
"""

import os
import logging
import sys

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def create_mysql_env_file():
    """Create .env file with MySQL configuration"""
    print_header("MySQL Environment Configuration")
    
    print("\nPlease provide your MySQL database details:")
    
    # Get MySQL configuration from user
    mysql_host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    mysql_port = input("MySQL Port (default: 3306): ").strip() or "3306"
    mysql_user = input("MySQL Username (default: root): ").strip() or "root"
    mysql_password = input("MySQL Password: ").strip()
    mysql_database = input("MySQL Database Name (default: wms_db): ").strip() or "wms_db"
    
    # Create .env file content
    env_content = f"""# MySQL Database Configuration
MYSQL_HOST={mysql_host}
MYSQL_PORT={mysql_port}
MYSQL_USER={mysql_user}
MYSQL_PASSWORD={mysql_password}
MYSQL_DATABASE={mysql_database}

# SAP B1 Configuration (optional)
SAP_B1_SERVER=https://your-sap-server:50000
SAP_B1_USERNAME=your_username
SAP_B1_PASSWORD=your_password
SAP_B1_COMPANY_DB=your_company_db

# Session Configuration
SESSION_SECRET=your-secret-key-change-in-production
"""
    
    # Write to .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"✅ Created .env file with MySQL configuration")
        print(f"   Host: {mysql_host}")
        print(f"   Database: {mysql_database}")
        print(f"   User: {mysql_user}")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False
    
    return True

def create_mysql_database_script():
    """Create SQL script to set up MySQL database"""
    sql_content = """-- WMS Database Setup Script for MySQL
-- Run this script in your MySQL server to create the database

-- Create database
CREATE DATABASE IF NOT EXISTS wms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE wms_db;

-- Create user (optional - adjust as needed)
-- CREATE USER 'wms_user'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON wms_db.* TO 'wms_user'@'localhost';
-- FLUSH PRIVILEGES;

-- The application will automatically create tables on first run
SELECT 'Database wms_db created successfully!' as message;
"""
    
    try:
        with open('setup_mysql_database.sql', 'w') as f:
            f.write(sql_content)
        print("✅ Created setup_mysql_database.sql")
        print("   Run this script in your MySQL server to create the database")
    except Exception as e:
        print(f"❌ Error creating SQL script: {e}")
        return False
    
    return True

def test_mysql_connection():
    """Test MySQL connection"""
    print_header("Testing MySQL Connection")
    
    try:
        # Try to import required packages
        import pymysql
        print("✅ PyMySQL package is available")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get MySQL configuration
        mysql_host = os.environ.get("MYSQL_HOST", "localhost")
        mysql_user = os.environ.get("MYSQL_USER", "root")
        mysql_password = os.environ.get("MYSQL_PASSWORD", "")
        mysql_database = os.environ.get("MYSQL_DATABASE", "wms_db")
        
        print(f"📡 Testing connection to {mysql_host}...")
        
        # Test connection
        connection = pymysql.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version")
            result = cursor.fetchone()
            print(f"✅ Connected to MySQL {result['version']}")
            
        connection.close()
        print("✅ MySQL connection test successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("   Run: pip install pymysql python-dotenv")
        return False
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if MySQL server is running")
        print("2. Verify database credentials in .env file")
        print("3. Ensure the database exists (run setup_mysql_database.sql)")
        print("4. Check firewall settings")
        return False

def show_setup_instructions():
    """Show comprehensive setup instructions"""
    print_header("MySQL Setup Instructions")
    
    instructions = """
📋 Complete MySQL Setup Guide:

1. Install MySQL Server:
   - Download from https://dev.mysql.com/downloads/mysql/
   - Or use package manager: apt install mysql-server (Ubuntu/Debian)
   - Or use Homebrew: brew install mysql (macOS)

2. Create Database:
   - Run: mysql -u root -p
   - Execute: CREATE DATABASE wms_db;
   - Or run the generated setup_mysql_database.sql script

3. Configure Application:
   - Run this script to create .env file
   - Update MySQL credentials in .env file
   - Test connection using this script

4. Start Application:
   - Run: python main.py
   - The app will automatically create tables on first run

5. Access Application:
   - Open browser to http://localhost:5000
   - Login with: admin / admin123

🔧 Environment Variables:
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=wms_db

🚀 The application supports multiple databases:
   - Priority: MySQL > PostgreSQL > SQLite (fallback)
   - Just set the appropriate environment variables
"""
    
    print(instructions)

def main():
    """Main setup function"""
    print_header("WMS MySQL Database Setup")
    
    print("\nChoose an option:")
    print("1. Create .env file with MySQL configuration")
    print("2. Create MySQL database setup script")
    print("3. Test MySQL connection")
    print("4. Show setup instructions")
    print("5. Complete setup (all steps)")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == '1':
        create_mysql_env_file()
    elif choice == '2':
        create_mysql_database_script()
    elif choice == '3':
        test_mysql_connection()
    elif choice == '4':
        show_setup_instructions()
    elif choice == '5':
        print("🚀 Running complete MySQL setup...")
        create_mysql_env_file()
        create_mysql_database_script()
        test_mysql_connection()
        show_setup_instructions()
    else:
        print("❌ Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()