#!/usr/bin/env python3
"""
Simple Local Environment Setup for WMS
Creates a working environment configuration for local development
"""

import os
import platform

def print_header(title):
    """Print formatted header"""
    print("=" * 50)
    print(f" {title}")
    print("=" * 50)

def create_working_env():
    """Create a working .env file for local development"""
    computer_name = platform.node()
    
    # Create .env content optimized for your environment
    env_content = f"""# WMS Local Development Environment
# Computer: {computer_name}
# SQL Server: {computer_name}\\SQLEXPRESS

# Local SQL Server Configuration (Primary)
MSSQL_SERVER={computer_name}\\SQLEXPRESS
MSSQL_DATABASE=WMS_DB
MSSQL_USERNAME=sa
MSSQL_PASSWORD=Ea@12345

# Flask Configuration
SESSION_SECRET=local-dev-secret-key-{computer_name}

# SAP B1 Configuration (offline mode - will use mock data)
# Update these when you have actual SAP B1 server
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=Ea@12345
SAP_B1_COMPANY_DB=Test_Hutchinson

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=1

# Alternative configurations for testing:
# If SQL Server doesn't work, comment out MSSQL_ variables above
# The app will automatically fall back to SQLite database
"""

    try:
        # Backup existing .env
        if os.path.exists('.env'):
            backup_name = '.env.backup'
            counter = 1
            while os.path.exists(backup_name):
                backup_name = f'.env.backup.{counter}'
                counter += 1
            
            os.rename('.env', backup_name)
            print(f"Backed up existing .env to {backup_name}")
        
        # Write new .env
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("Created .env file for local development")
        return True
        
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False

def create_run_script():
    """Create a simple run script for local development"""
    
    if platform.system() == 'Windows':
        script_content = """@echo off
echo Starting WMS Local Development Server...
echo.
echo Computer: %COMPUTERNAME%
echo Database: Will try SQL Server, fallback to SQLite
echo.
python main.py
pause
"""
        script_name = 'run_local.bat'
    else:
        script_content = """#!/bin/bash
echo "Starting WMS Local Development Server..."
echo ""
echo "Computer: $(hostname)"
echo "Database: Will try SQL Server, fallback to SQLite"
echo ""
python main.py
"""
        script_name = 'run_local.sh'
    
    try:
        with open(script_name, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if platform.system() != 'Windows':
            os.chmod(script_name, 0o755)
        
        print(f"Created {script_name} for easy startup")
        return True
        
    except Exception as e:
        print(f"Error creating run script: {e}")
        return False

def show_next_steps():
    """Show next steps for setup"""
    computer_name = platform.node()
    
    print("\nNext Steps:")
    print("1. Configure SQL Server (if you want to use it):")
    print("   a. Run as Administrator: python enable_sql_server_tcp.py")
    print("   b. Or manually enable TCP/IP in SQL Server Configuration Manager")
    print("")
    print("2. Test your setup:")
    print("   - Run: python main.py")
    print("   - Open browser: http://localhost:5000")
    print("   - Default login: admin / admin")
    print("")
    print("3. Database options:")
    print("   - SQL Server: Requires configuration above")
    print("   - SQLite: Works automatically (no setup needed)")
    print("")
    print("4. If SQL Server doesn't work:")
    print("   - Comment out MSSQL_ lines in .env file")
    print("   - App will use SQLite automatically")
    print("")
    print(f"Your computer name: {computer_name}")
    print(f"SQL Server instance: {computer_name}\\SQLEXPRESS")

def main():
    """Main setup function"""
    print_header("WMS Local Environment Setup")
    
    success_count = 0
    
    # Create .env file
    if create_working_env():
        success_count += 1
    
    # Create run script
    if create_run_script():
        success_count += 1
    
    print("")
    print_header("Setup Complete")
    print(f"Successfully completed {success_count}/2 setup steps")
    
    if success_count == 2:
        print("Local environment is ready!")
        show_next_steps()
    else:
        print("Setup had some issues. You may need to create files manually.")

if __name__ == "__main__":
    main()