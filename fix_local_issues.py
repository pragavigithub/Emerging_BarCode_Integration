#!/usr/bin/env python3
"""
Fix Local Development Issues Script
This script helps resolve common local development issues for the WMS application.
"""

import os
import sys
import subprocess
import platform
import socket
import time

def print_header(title):
    """Print formatted header"""
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_sql_server_service():
    """Check if SQL Server service is running (Windows only)"""
    if platform.system() != "Windows":
        print("❌ SQL Server is only supported on Windows")
        return False
    
    try:
        # Check SQL Server service status
        result = subprocess.run(['sc', 'query', 'MSSQLSERVER'], 
                              capture_output=True, text=True, shell=True)
        if 'RUNNING' in result.stdout:
            print("✅ SQL Server (MSSQLSERVER) service is running")
            return True
        else:
            print("❌ SQL Server (MSSQLSERVER) service is not running")
            
            # Check SQL Server Express
            result = subprocess.run(['sc', 'query', 'MSSQL$SQLEXPRESS'], 
                                  capture_output=True, text=True, shell=True)
            if 'RUNNING' in result.stdout:
                print("✅ SQL Server Express (MSSQL$SQLEXPRESS) service is running")
                return True
            else:
                print("❌ SQL Server Express (MSSQL$SQLEXPRESS) service is not running")
                return False
    except Exception as e:
        print(f"❌ Error checking SQL Server service: {e}")
        return False

def test_network_connectivity():
    """Test network connectivity to SQL Server"""
    server = "192.168.1.5"
    port = 1433
    
    print(f"🔍 Testing connection to {server}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connection to {server}:{port} successful")
            return True
        else:
            print(f"❌ Cannot connect to {server}:{port}")
            return False
    except Exception as e:
        print(f"❌ Network connection error: {e}")
        return False

def create_working_env_file():
    """Create a working .env file for local development"""
    print("📝 Creating working .env file for local development...")
    
    env_content = """# WMS Local Development Environment
# Database Configuration (Priority: MSSQL > PostgreSQL > SQLite)

# Option 1: Use SQLite for local development (Recommended for testing)
# Comment out MSSQL variables below to use SQLite
# DATABASE_URL=

# Option 2: Local MSSQL Configuration (Uncomment if SQL Server is working)
# MSSQL_SERVER=.\\SQLEXPRESS
# MSSQL_DATABASE=WMS_DB
# MSSQL_USERNAME=sa
# MSSQL_PASSWORD=Ea@12345

# Flask Configuration
SESSION_SECRET=dev-secret-key-change-in-production

# SAP B1 Configuration (Update with your actual SAP server details)
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=Ea@12345
SAP_B1_COMPANY_DB=Test_Hutchinson

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=1
"""

    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file for local development")
        print("\n📋 Configuration:")
        print("   - SQLite database (no SQL Server required)")
        print("   - SAP B1 settings (update with your server details)")
        print("   - Development mode enabled")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def suggest_sap_fixes():
    """Suggest SAP B1 connection fixes"""
    print("🔧 SAP B1 Connection Issues:")
    print("")
    print("The SAP login error (-304: Fail to NONE-SSO login from SLD) indicates:")
    print("1. SAP B1 Service Layer authentication failure")
    print("2. Incorrect username/password combination")
    print("3. SAP B1 server not accessible")
    print("")
    print("💡 Solutions:")
    print("1. Verify SAP B1 Service Layer is running on https://192.168.1.5:50000")
    print("2. Check username/password in .env file")
    print("3. Ensure SAP B1 user has Service Layer access")
    print("4. Test SAP connection manually:")
    print("   curl -X POST https://192.168.1.5:50000/b1s/v1/Login \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"CompanyDB\":\"Test_Hutchinson\",\"UserName\":\"manager\",\"Password\":\"Ea@12345\"}' \\")
    print("        -k")
    print("")
    print("5. The app works in offline mode, so core functionality is available")

def main():
    """Main function to fix local issues"""
    print_header("WMS Local Development Issue Fixer")
    
    print("🔍 Analyzing local development issues...")
    print("")
    
    # Check SQL Server
    print_header("SQL Server Analysis")
    sql_running = check_sql_server_service()
    network_ok = test_network_connectivity()
    
    print("")
    print_header("Recommendations")
    
    if not sql_running or not network_ok:
        print("❌ SQL Server connection issues detected")
        print("")
        print("💡 Recommended Solution: Use SQLite for local development")
        print("   - No SQL Server setup required")
        print("   - Faster development and testing")
        print("   - Same functionality as SQL Server")
        print("")
        
        create_working_env_file()
    else:
        print("✅ SQL Server appears to be accessible")
        print("💡 You can use either SQLite or SQL Server for development")
    
    print("")
    print_header("SAP B1 Integration")
    suggest_sap_fixes()
    
    print("")
    print_header("Next Steps")
    print("1. 📝 Update .env file with correct SAP credentials")
    print("2. 🚀 Run: python main.py")
    print("3. 🌐 Open: http://localhost:5000")
    print("4. 🔑 Login with: admin / admin123")
    print("")
    print("✅ The app will work in offline mode if SAP is not available")
    print("✅ All core WMS functionality is available without SAP")

if __name__ == "__main__":
    main()