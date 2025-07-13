#!/usr/bin/env python3
"""
Quick Environment Setup for Local Development
This script sets up environment variables for MSSQL connection.
"""

import os
import sys

def create_env_file():
    """Create .env file with MSSQL configuration"""
    print("🔧 Setting up environment variables for local development")
    print()
    
    # Default values for your setup
    default_values = {
        'MSSQL_SERVER': '192.168.1.5\\SQLEXPRESS',
        'MSSQL_DATABASE': 'WMS_DB',
        'MSSQL_USERNAME': 'sa',
        'MSSQL_PASSWORD': 'Ea@12345'
    }
    
    print("💡 Connection Options:")
    print("1. Local SQL Server (recommended for development)")
    print("2. Remote SQL Server (requires network access)")
    print("3. Skip MSSQL (use SQLite for development)")
    print()
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == '3':
        # Skip MSSQL configuration
        env_vars = {
            'MSSQL_SERVER': '',
            'MSSQL_DATABASE': '',
            'MSSQL_USERNAME': '',
            'MSSQL_PASSWORD': ''
        }
        print("✅ MSSQL disabled. Application will use SQLite for development.")
    elif choice == '2':
        print("⚠️  Remote SQL Server requires proper network configuration")
        print("Make sure SQL Server is configured for remote connections")
        print()
    
    env_vars = {}
    
    for key, default in default_values.items():
        if key == 'MSSQL_SERVER':
            print("Server name options:")
            print("1. 192.168.1.5\\SQLEXPRESS")
            print("2. .\\SQLEXPRESS")
            print("3. DESKTOP-PLFK2B5\\SQLEXPRESS")
            print("4. Custom")
            
            choice = input(f"Choose server (1-4) or press Enter for default [{default}]: ").strip()
            if choice == '1':
                env_vars[key] = '192.168.1.5\\SQLEXPRESS'
            elif choice == '2':
                env_vars[key] = '.\\SQLEXPRESS'
            elif choice == '3':
                env_vars[key] = 'DESKTOP-PLFK2B5\\SQLEXPRESS'
            elif choice == '4':
                env_vars[key] = input("Enter custom server name: ").strip()
            else:
                env_vars[key] = default
        else:
            value = input(f"Enter {key} [{default}]: ").strip()
            env_vars[key] = value if value else default
    
    # Create .env file
    env_content = f"""# MSSQL Database Configuration
MSSQL_SERVER={env_vars['MSSQL_SERVER']}
MSSQL_DATABASE={env_vars['MSSQL_DATABASE']}
MSSQL_USERNAME={env_vars['MSSQL_USERNAME']}
MSSQL_PASSWORD={env_vars['MSSQL_PASSWORD']}

# Session Secret
SESSION_SECRET=your-secret-key-change-in-production

# SAP B1 Configuration
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=Ea@12345
SAP_B1_COMPANY_DB=Test_Hutchinson
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Environment variables saved to .env file")
    print(f"Server: {env_vars['MSSQL_SERVER']}")
    print(f"Database: {env_vars['MSSQL_DATABASE']}")
    print(f"Username: {env_vars['MSSQL_USERNAME']}")
    print()
    
    # Show how to load .env file
    print("📋 To use the .env file, install python-dotenv:")
    print("pip install python-dotenv")
    print()
    print("Then add this to your main.py:")
    print("from dotenv import load_dotenv")
    print("load_dotenv()")
    print()
    print("Or set system environment variables manually.")
    
    return env_vars

def main():
    """Main setup function"""
    print("=== WMS Local Environment Setup ===")
    print()
    
    # Check if .env already exists
    if os.path.exists('.env'):
        overwrite = input(".env file already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    try:
        create_env_file()
        print("\n🎉 Setup complete!")
        print()
        print("Next steps:")
        print("1. Make sure SQL Server is running")
        print("2. Create WMS_DB database")
        print("3. Run: python fix_mssql_connection.py (to test connection)")
        print("4. Run: python main.py (to start the app)")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()