#!/usr/bin/env python3
"""
Enable TCP/IP for SQL Server Express and configure static port
This script automates the SQL Server configuration needed for WMS
"""

import winreg
import subprocess
import time
import os

def print_header(title):
    """Print formatted header"""
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_admin_privileges():
    """Check if running as administrator"""
    try:
        # Try to access a registry key that requires admin privileges
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion"):
            return True
    except PermissionError:
        return False

def enable_sql_server_tcp():
    """Enable TCP/IP protocol for SQL Server Express"""
    try:
        print("Configuring SQL Server Express TCP/IP settings...")
        
        # Registry path for SQL Server Express network configuration
        reg_path = r"SOFTWARE\Microsoft\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQLServer\SuperSocketNetLib\Tcp"
        
        # Enable TCP/IP protocol
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 1)
            print("TCP/IP protocol enabled")
        
        # Configure static port 1433
        ip_all_path = reg_path + r"\IPAll"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ip_all_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "TcpPort", 0, winreg.REG_SZ, "1433")
            winreg.SetValueEx(key, "TcpDynamicPorts", 0, winreg.REG_SZ, "")
            print("Static port 1433 configured")
        
        return True
    except Exception as e:
        print(f"Error configuring TCP/IP: {e}")
        return False

def restart_sql_server_service():
    """Restart SQL Server Express service"""
    try:
        print("Restarting SQL Server Express service...")
        
        # Stop the service
        result = subprocess.run(['net', 'stop', 'MSSQL$SQLEXPRESS'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("SQL Server Express service stopped")
        else:
            print(f"Warning: Could not stop service - {result.stderr}")
        
        # Wait a moment
        time.sleep(3)
        
        # Start the service
        result = subprocess.run(['net', 'start', 'MSSQL$SQLEXPRESS'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("SQL Server Express service started")
            return True
        else:
            print(f"Error starting service: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error restarting service: {e}")
        return False

def configure_sql_authentication():
    """Configure SQL Server for mixed authentication"""
    try:
        print("Configuring SQL Server authentication...")
        
        # Registry path for authentication mode
        reg_path = r"SOFTWARE\Microsoft\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQLServer"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            # Set to mixed authentication (2 = SQL Server and Windows Authentication)
            winreg.SetValueEx(key, "LoginMode", 0, winreg.REG_DWORD, 2)
            print("Mixed authentication mode enabled")
        
        return True
    except Exception as e:
        print(f"Error configuring authentication: {e}")
        return False

def create_firewall_rule():
    """Create Windows Firewall rule for SQL Server"""
    try:
        print("Creating Windows Firewall rule...")
        
        # Create inbound rule for port 1433
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=SQL Server Express',
            'dir=in',
            'action=allow',
            'protocol=TCP',
            'localport=1433'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("Firewall rule created for port 1433")
            return True
        else:
            print(f"Warning: Could not create firewall rule - {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error creating firewall rule: {e}")
        return False

def test_configuration():
    """Test the new configuration"""
    try:
        import socket
        
        print("Testing TCP/IP connection...")
        
        # Test port 1433
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 1433))
        sock.close()
        
        if result == 0:
            print("SUCCESS: Port 1433 is accessible")
            return True
        else:
            print("Port 1433 is not accessible yet")
            return False
            
    except Exception as e:
        print(f"Error testing configuration: {e}")
        return False

def main():
    """Main function"""
    print_header("SQL Server Express TCP/IP Configuration")
    
    # Check admin privileges
    if not check_admin_privileges():
        print("ERROR: This script must be run as Administrator")
        print("Right-click Command Prompt and select 'Run as administrator'")
        print("Then run: python enable_sql_server_tcp.py")
        return
    
    print("Running as Administrator - proceeding with configuration...")
    print("")
    
    success_count = 0
    
    # Enable TCP/IP
    if enable_sql_server_tcp():
        success_count += 1
    
    # Configure authentication
    if configure_sql_authentication():
        success_count += 1
    
    # Create firewall rule
    if create_firewall_rule():
        success_count += 1
    
    # Restart service
    if restart_sql_server_service():
        success_count += 1
        
        # Wait for service to fully start
        print("Waiting for service to initialize...")
        time.sleep(10)
        
        # Test configuration
        if test_configuration():
            success_count += 1
    
    print("")
    print_header("Configuration Results")
    print(f"Completed {success_count}/5 configuration steps")
    
    if success_count >= 4:
        print("SQL Server Express is now configured for TCP/IP connections!")
        print("")
        print("Next steps:")
        print("1. Run: python test_sql_connection.py")
        print("2. In SQL Server Management Studio:")
        print("   - Connect to DESKTOP-PLFK2B5\\SQLEXPRESS")
        print("   - Enable 'sa' login with password: Ea@12345")
        print("   - Create database 'WMS_DB'")
        print("3. Run: python main.py")
    else:
        print("Configuration incomplete. Manual steps may be required.")
        print("Please follow the SQL Server Configuration Manager steps:")
        print("1. Open SQL Server Configuration Manager")
        print("2. Go to SQL Server Network Configuration > Protocols for SQLEXPRESS")
        print("3. Enable TCP/IP protocol")
        print("4. Set static port 1433 in TCP/IP Properties > IP Addresses > IPAll")
        print("5. Restart SQL Server Express service")

if __name__ == "__main__":
    main()