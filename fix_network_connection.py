#!/usr/bin/env python3
"""
Network Connection Fix for Remote SQL Server
This script helps diagnose and fix network connectivity issues with remote SQL Server.
"""

import os
import sys
import subprocess
import socket
import telnetlib
from urllib.parse import quote_plus

def test_network_connectivity():
    """Test network connectivity to remote SQL Server"""
    server = os.environ.get('MSSQL_SERVER', '192.168.1.5\\SQLEXPRESS')
    
    # Extract IP address from server name
    if '\\' in server:
        ip_address = server.split('\\')[0]
        instance_name = server.split('\\')[1]
    else:
        ip_address = server
        instance_name = 'MSSQLSERVER'
    
    print(f"🔍 Testing network connectivity to {ip_address}")
    print(f"Instance: {instance_name}")
    print("=" * 50)
    
    # Test 1: Ping the server
    print("\n1. Testing ping connectivity...")
    try:
        result = subprocess.run(['ping', '-n', '1', ip_address], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ping successful to {ip_address}")
        else:
            print(f"❌ Ping failed to {ip_address}")
            print("   - Check if server is online")
            print("   - Check firewall settings")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Ping timeout to {ip_address}")
        return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False
    
    # Test 2: Test SQL Server Browser Service (port 1434)
    print("\n2. Testing SQL Server Browser Service (port 1434)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.connect((ip_address, 1434))
        sock.close()
        print(f"✅ SQL Server Browser Service is accessible on {ip_address}:1434")
    except Exception as e:
        print(f"❌ SQL Server Browser Service not accessible: {e}")
        print("   - SQL Server Browser service may not be running")
        print("   - Port 1434 may be blocked by firewall")
    
    # Test 3: Test common SQL Server ports
    print("\n3. Testing common SQL Server ports...")
    common_ports = [1433, 1434, 1435, 1436, 49152, 49153, 49154, 49155]
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip_address, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port} is open")
            else:
                print(f"❌ Port {port} is closed/filtered")
        except Exception as e:
            print(f"❌ Error testing port {port}: {e}")
    
    # Test 4: Test SQL Server instance port
    print(f"\n4. Testing SQL Server instance port for {instance_name}...")
    try:
        # Try to resolve instance port using sqlcmd
        result = subprocess.run(['sqlcmd', '-L'], 
                              capture_output=True, text=True, timeout=10)
        if server in result.stdout:
            print(f"✅ SQL Server instance {server} is visible in network")
        else:
            print(f"❌ SQL Server instance {server} is not visible in network")
            print("   - SQL Server Browser service may not be running")
            print("   - Instance may not be configured for remote connections")
    except Exception as e:
        print(f"❌ Could not check SQL Server instances: {e}")
    
    return True

def suggest_network_fixes():
    """Suggest network-related fixes"""
    print("\n🔧 Network Connectivity Solutions:")
    print("=" * 50)
    
    print("\n1. Enable SQL Server Browser Service (on SQL Server machine):")
    print("   - Open Services (services.msc)")
    print("   - Find 'SQL Server Browser'")
    print("   - Set startup type to 'Automatic'")
    print("   - Start the service")
    
    print("\n2. Configure SQL Server for Remote Connections:")
    print("   - Open SQL Server Configuration Manager")
    print("   - Go to 'SQL Server Network Configuration'")
    print("   - Enable 'TCP/IP' protocol")
    print("   - Right-click TCP/IP → Properties")
    print("   - Go to 'IP Addresses' tab")
    print("   - Set 'TCP Port' to 1433 for 'IP All'")
    print("   - Restart SQL Server service")
    
    print("\n3. Configure Windows Firewall (on SQL Server machine):")
    print("   - Open Windows Firewall with Advanced Security")
    print("   - Create inbound rule for port 1433 (TCP)")
    print("   - Create inbound rule for port 1434 (UDP)")
    print("   - Allow 'sqlservr.exe' through firewall")
    
    print("\n4. Check SQL Server Authentication:")
    print("   - Open SQL Server Management Studio")
    print("   - Connect to SQL Server instance")
    print("   - Right-click server → Properties → Security")
    print("   - Select 'SQL Server and Windows Authentication mode'")
    print("   - Restart SQL Server service")
    
    print("\n5. Create SQL Server Login:")
    print("   - In SSMS, expand 'Security' → 'Logins'")
    print("   - Right-click 'Logins' → 'New Login'")
    print("   - Enter login name (sa)")
    print("   - Select 'SQL Server authentication'")
    print("   - Enter password")
    print("   - Go to 'User Mapping' → Select 'WMS_DB'")
    print("   - Assign 'db_owner' role")
    
    print("\n6. Test Connection String Alternatives:")
    print("   Try these server formats:")
    print("   - 192.168.1.5,1433")
    print("   - 192.168.1.5\\SQLEXPRESS,1433")
    print("   - tcp:192.168.1.5,1433")

def create_local_fallback_env():
    """Create a fallback .env file for local SQL Server"""
    print("\n🔄 Creating local fallback configuration...")
    
    fallback_env = """# Local SQL Server Fallback Configuration
# Use this if remote connection fails
MSSQL_SERVER=localhost\\SQLEXPRESS
MSSQL_DATABASE=WMS_DB
MSSQL_USERNAME=sa
MSSQL_PASSWORD=your_local_password

# Or use these environment variables to disable MSSQL
# and use SQLite instead:
# MSSQL_SERVER=
# MSSQL_DATABASE=
# MSSQL_USERNAME=
# MSSQL_PASSWORD=

# Session Secret
SESSION_SECRET=your-secret-key-change-in-production

# SAP B1 Configuration
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=Ea@12345
SAP_B1_COMPANY_DB=Test_Hutchinson
"""
    
    with open('.env.local', 'w') as f:
        f.write(fallback_env)
    
    print("✅ Created .env.local file with local SQL Server configuration")
    print("   Copy this to .env if you want to use local SQL Server instead")
    print("   Or clear the MSSQL variables to use SQLite")

def main():
    """Main diagnostic function"""
    print("🌐 Remote SQL Server Connection Diagnostics")
    print("=" * 60)
    
    server = os.environ.get('MSSQL_SERVER', 'Not set')
    database = os.environ.get('MSSQL_DATABASE', 'Not set')
    username = os.environ.get('MSSQL_USERNAME', 'Not set')
    
    print(f"Target Server: {server}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    
    if server == 'Not set':
        print("\n❌ MSSQL_SERVER environment variable not set")
        print("Run: python setup_local_env.py")
        return
    
    # Test network connectivity
    if test_network_connectivity():
        print("\n✅ Network connectivity tests completed")
    else:
        print("\n❌ Network connectivity issues detected")
    
    # Suggest fixes
    suggest_network_fixes()
    
    # Create fallback configuration
    create_local_fallback_env()
    
    print("\n📋 Next Steps:")
    print("1. If remote SQL Server is not accessible:")
    print("   - Work with your network administrator")
    print("   - Configure firewall and SQL Server settings")
    print("   - Or use local SQL Server installation")
    print("\n2. For quick development:")
    print("   - Clear MSSQL environment variables to use SQLite")
    print("   - Or install local SQL Server Express")
    print("\n3. Test again after making changes:")
    print("   - python fix_mssql_connection.py")

if __name__ == "__main__":
    main()