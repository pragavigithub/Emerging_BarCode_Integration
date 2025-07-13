#!/usr/bin/env python3
"""
Local SQL Server Configuration Fix
Specifically for SQL Server Management Studio 20.2.30.0 environment
"""

import os
import platform
import subprocess
import socket
import time

def print_header(title):
    """Print formatted header"""
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_sql_server_services():
    """Check SQL Server services status"""
    print("🔍 Checking SQL Server services...")
    
    services_to_check = [
        'MSSQLSERVER',           # Default instance
        'MSSQL$SQLEXPRESS',      # SQL Express instance
        'SQLBrowser',            # SQL Server Browser
        'SQLSERVERAGENT'         # SQL Server Agent
    ]
    
    running_services = []
    
    for service in services_to_check:
        try:
            result = subprocess.run(['sc', 'query', service], 
                                  capture_output=True, text=True, shell=True)
            if 'RUNNING' in result.stdout:
                print(f"✅ {service} is running")
                running_services.append(service)
            elif 'STOPPED' in result.stdout:
                print(f"❌ {service} is stopped")
            else:
                print(f"❓ {service} status unknown")
        except Exception as e:
            print(f"❓ Could not check {service}: {e}")
    
    return running_services

def get_computer_name():
    """Get the computer name for SQL Server instance"""
    try:
        computer_name = platform.node()
        print(f"💻 Computer name: {computer_name}")
        return computer_name
    except Exception as e:
        print(f"❌ Could not get computer name: {e}")
        return "localhost"

def test_sql_connections():
    """Test various SQL Server connection configurations"""
    computer_name = get_computer_name()
    
    # Connection configurations to test
    connection_configs = [
        {
            'server': f'{computer_name}\\SQLEXPRESS',
            'description': 'Local SQL Express with computer name'
        },
        {
            'server': '.\\SQLEXPRESS',
            'description': 'Local SQL Express with dot notation'
        },
        {
            'server': 'localhost\\SQLEXPRESS',
            'description': 'Local SQL Express with localhost'
        },
        {
            'server': '(local)\\SQLEXPRESS',
            'description': 'Local SQL Express with (local)'
        },
        {
            'server': computer_name,
            'description': 'Default instance on computer name'
        },
        {
            'server': 'localhost',
            'description': 'Default instance on localhost'
        }
    ]
    
    print("\n🔍 Testing SQL Server connections...")
    working_configs = []
    
    for config in connection_configs:
        try:
            # Test port 1433 (default SQL Server port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            # Extract hostname for socket test
            hostname = config['server'].split('\\')[0]
            if hostname in ['.', '(local)']:
                hostname = 'localhost'
            
            result = sock.connect_ex((hostname, 1433))
            sock.close()
            
            if result == 0:
                print(f"✅ {config['description']}: Connection possible")
                working_configs.append(config)
            else:
                print(f"❌ {config['description']}: Port 1433 not accessible")
                
        except Exception as e:
            print(f"❌ {config['description']}: {e}")
    
    return working_configs

def create_local_env_file():
    """Create optimized .env file for local SQL Server"""
    computer_name = get_computer_name()
    
    env_content = f"""# WMS Local Environment - SQL Server {computer_name}
# Generated automatically for your local SQL Server setup

# Local SQL Server Configuration
MSSQL_SERVER={computer_name}\\SQLEXPRESS
MSSQL_DATABASE=WMS_DB
MSSQL_USERNAME=sa
MSSQL_PASSWORD=Ea@12345

# Alternative configurations (uncomment if primary fails)
# MSSQL_SERVER=.\\SQLEXPRESS
# MSSQL_SERVER=localhost\\SQLEXPRESS
# MSSQL_SERVER=(local)\\SQLEXPRESS

# Flask Configuration
SESSION_SECRET=dev-secret-key-local-sql-server

# SAP B1 Configuration (update with your actual server)
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=1422
SAP_B1_COMPANY_DB=EINV-TESTDB-LIVE-HUST

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=1
"""

    try:
        # Backup existing .env if it exists
        if os.path.exists('.env'):
            backup_name = f'.env.backup.{int(time.time())}'
            os.rename('.env', backup_name)
            print(f"📋 Backed up existing .env to {backup_name}")
        
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created optimized .env file for your local SQL Server")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def suggest_sql_server_fixes():
    """Suggest SQL Server configuration fixes"""
    print("\n🔧 SQL Server Configuration Recommendations:")
    print("")
    print("1. Enable TCP/IP Protocol:")
    print("   - Open SQL Server Configuration Manager")
    print("   - Go to SQL Server Network Configuration > Protocols for SQLEXPRESS")
    print("   - Right-click TCP/IP > Enable")
    print("   - Restart SQL Server Express service")
    print("")
    print("2. Configure SQL Server Authentication:")
    print("   - Open SQL Server Management Studio")
    print("   - Connect to your instance")
    print("   - Right-click server > Properties > Security")
    print("   - Select 'SQL Server and Windows Authentication mode'")
    print("   - Restart SQL Server service")
    print("")
    print("3. Create/Reset SA Password:")
    print("   - In SSMS, expand Security > Logins")
    print("   - Right-click 'sa' > Properties")
    print("   - Set password to: Ea@12345")
    print("   - Uncheck 'Enforce password policy'")
    print("   - On Status tab, set Login to 'Enabled'")
    print("")
    print("4. Create WMS_DB Database:")
    print("   - In SSMS, right-click Databases > New Database")
    print("   - Database name: WMS_DB")
    print("   - Click OK")
    print("")
    print("5. Configure Windows Firewall:")
    print("   - Allow SQL Server through Windows Firewall")
    print("   - Default port: 1433")

def create_sql_test_script():
    """Create a script to test SQL Server connectivity"""
    test_script = """
import pyodbc
import os

def test_sql_connection():
    # Test configurations
    configs = [
        f"{os.environ.get('COMPUTERNAME', 'localhost')}\\\\SQLEXPRESS",
        ".\\\\SQLEXPRESS", 
        "localhost\\\\SQLEXPRESS",
        "(local)\\\\SQLEXPRESS"
    ]
    
    for server in configs:
        try:
            print(f"Testing: {server}")
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};UID=sa;PWD=Ea@12345;TrustServerCertificate=yes"
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            result = cursor.fetchone()
            print(f"✅ SUCCESS: {server}")
            print(f"   Version: {result[0][:50]}...")
            conn.close()
            break
        except Exception as e:
            print(f"❌ FAILED: {server} - {e}")
    
if __name__ == "__main__":
    test_sql_connection()
"""
    
    try:
        with open('test_sql_connection.py', 'w') as f:
            f.write(test_script)
        print("✅ Created test_sql_connection.py script")
        return True
    except Exception as e:
        print(f"❌ Error creating test script: {e}")
        return False

def main():
    """Main function"""
    print_header("SQL Server Local Environment Fix")
    print(f"Detected system: {platform.system()} {platform.release()}")
    print("")
    
    # Check services
    running_services = check_sql_server_services()
    
    # Test connections
    working_configs = test_sql_connections()
    
    # Create environment file
    create_local_env_file()
    
    # Create test script
    create_sql_test_script()
    
    print("")
    print_header("Summary and Next Steps")
    
    if running_services:
        print("✅ SQL Server services are running")
    else:
        print("❌ No SQL Server services detected as running")
        print("   Please start SQL Server Express service")
    
    if working_configs:
        print("✅ Found accessible SQL Server connections")
    else:
        print("❌ No accessible SQL Server connections found")
        suggest_sql_server_fixes()
    
    print("")
    print("📋 To test your configuration:")
    print("1. Run: python test_sql_connection.py")
    print("2. Run: python main.py")
    print("3. Check for successful database connection in logs")
    print("")
    print("💡 If issues persist, try running WMS in SQLite mode:")
    print("   - Comment out all MSSQL_ variables in .env")
    print("   - The app will automatically use SQLite")

if __name__ == "__main__":
    main()