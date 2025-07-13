#!/usr/bin/env python3
"""
Local MySQL Setup for WMS
Installs required Python packages and creates MySQL configuration
"""

import os
import sys
import subprocess
import platform

def print_header(title):
    """Print formatted header"""
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def install_package(package):
    """Install a package using pip"""
    try:
        print(f"Installing {package}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def install_mysql_packages():
    """Install MySQL Python packages"""
    packages_to_install = [
        "pymysql",
        "mysql-connector-python", 
        "python-dotenv"
    ]
    
    success_count = 0
    for package in packages_to_install:
        if install_package(package):
            success_count += 1
    
    return success_count == len(packages_to_install)

def create_mysql_env():
    """Create MySQL environment configuration"""
    computer_name = platform.node()
    
    env_content = f"""# WMS MySQL Development Environment
# Computer: {computer_name}
# Generated on: {platform.system()}

# MySQL Configuration (Primary Database)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=wms_db
MYSQL_USERNAME=root
MYSQL_PASSWORD=your_mysql_password_here

# Flask Configuration
SESSION_SECRET=mysql-dev-{computer_name}-key

# SAP B1 Configuration (optional - for offline development)
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=password
SAP_B1_COMPANY_DB=Test_DB

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=1

# Notes:
# 1. Update MYSQL_PASSWORD with your actual MySQL root password
# 2. Make sure MySQL server is running
# 3. Create database 'wms_db' before running the application
"""

    try:
        # Backup existing .env if it exists
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

def create_simple_mysql_test():
    """Create a simple MySQL test script that handles missing packages"""
    
    test_script = '''#!/usr/bin/env python3
"""
Simple MySQL Connection Test
This script tests MySQL connectivity for the WMS application
"""

import os
import sys

def load_env():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return True
    except ImportError:
        print("python-dotenv not installed. Using system environment variables.")
        return False

def test_pymysql():
    """Test PyMySQL connection"""
    try:
        import pymysql
        
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
            print(f"✅ SUCCESS: MySQL connection established!")
            print(f"   MySQL version: {result[0]}")
            print(f"   Host: {os.environ.get('MYSQL_HOST', 'localhost')}")
            print(f"   Database: {os.environ.get('MYSQL_DATABASE', 'wms_db')}")
        
        connection.close()
        return True
        
    except ImportError:
        print("❌ PyMySQL not installed. Run: pip install pymysql")
        return False
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        print("\\nTroubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Check your MySQL credentials in .env file")
        print("3. Ensure database 'wms_db' exists")
        print("4. Verify MySQL is listening on port 3306")
        return False

def main():
    print("Testing MySQL Connection for WMS...")
    print("")
    
    # Load environment
    load_env()
    
    # Test connection
    if test_pymysql():
        print("\\n🎉 MySQL setup is working! You can now run:")
        print("   python main.py")
        print("   Then open: http://localhost:5000")
    else:
        print("\\n❌ MySQL connection failed. Please check the troubleshooting steps above.")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open('test_mysql_simple.py', 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        print("Created test_mysql_simple.py")
        return True
        
    except Exception as e:
        print(f"Error creating test script: {e}")
        return False

def create_mysql_batch_file():
    """Create batch file for easy MySQL setup on Windows"""
    
    if platform.system() == "Windows":
        batch_content = '''@echo off
echo Installing MySQL packages for WMS...
echo.

python -m pip install --upgrade pip
python -m pip install pymysql
python -m pip install mysql-connector-python
python -m pip install python-dotenv

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Make sure MySQL server is running
echo 2. Update .env file with your MySQL password
echo 3. Create database: CREATE DATABASE wms_db;
echo 4. Test connection: python test_mysql_simple.py
echo 5. Run application: python main.py
echo.
pause
'''
        
        try:
            with open('install_mysql_packages.bat', 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            print("Created install_mysql_packages.bat")
            return True
            
        except Exception as e:
            print(f"Error creating batch file: {e}")
            return False
    
    return True

def show_setup_instructions():
    """Show comprehensive setup instructions"""
    print("")
    print_header("MySQL Setup Instructions")
    print("")
    print("STEP 1: Install MySQL Server (if not already installed)")
    print("   • Download from: https://dev.mysql.com/downloads/mysql/")
    print("   • During installation, remember your root password!")
    print("")
    print("STEP 2: Start MySQL Service")
    print("   • Windows: Services → MySQL → Start")
    print("   • Or from Command Prompt: net start mysql")
    print("")
    print("STEP 3: Create Database")
    print("   • Open MySQL Command Line Client")
    print("   • Run: CREATE DATABASE wms_db;")
    print("   • Or use MySQL Workbench/phpMyAdmin")
    print("")
    print("STEP 4: Update Configuration")
    print("   • Edit .env file")
    print("   • Set MYSQL_PASSWORD to your MySQL root password")
    print("")
    print("STEP 5: Test Connection")
    print("   • Run: python test_mysql_simple.py")
    print("")
    print("STEP 6: Start WMS Application")
    print("   • Run: python main.py")
    print("   • Open browser: http://localhost:5000")
    print("   • Login: admin / admin")

def main():
    """Main installation process"""
    print_header("WMS MySQL Local Installation")
    
    print("This script will install MySQL packages and create configuration files.")
    print("")
    
    success_steps = 0
    total_steps = 4
    
    # Step 1: Install MySQL packages
    print("Step 1: Installing MySQL Python packages...")
    if install_mysql_packages():
        success_steps += 1
        print("✅ MySQL packages installed successfully")
    else:
        print("⚠️ Some packages failed to install. You may need to install manually:")
        print("   pip install pymysql mysql-connector-python python-dotenv")
    
    print("")
    
    # Step 2: Create .env file
    print("Step 2: Creating MySQL configuration...")
    if create_mysql_env():
        success_steps += 1
        print("✅ MySQL .env file created")
    
    print("")
    
    # Step 3: Create test script
    print("Step 3: Creating MySQL test script...")
    if create_simple_mysql_test():
        success_steps += 1
        print("✅ MySQL test script created")
    
    print("")
    
    # Step 4: Create batch file (Windows)
    print("Step 4: Creating helper scripts...")
    if create_mysql_batch_file():
        success_steps += 1
        print("✅ Helper scripts created")
    
    print("")
    print_header("Installation Summary")
    print(f"Completed {success_steps}/{total_steps} setup steps")
    
    if success_steps >= 3:
        print("✅ MySQL setup files created successfully!")
        show_setup_instructions()
    else:
        print("⚠️ Setup had some issues. Manual installation may be required.")

if __name__ == "__main__":
    main()