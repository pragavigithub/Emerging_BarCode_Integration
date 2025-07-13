#!/usr/bin/env python3
"""
SQL Server Connection Fix Script
This script provides multiple solutions for the MSSQL connection error.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def solution_1_enable_tcp_ip():
    """Solution 1: Enable TCP/IP Protocol"""
    print_header("SOLUTION 1: Enable TCP/IP Protocol")
    print("The error indicates Named Pipes connection failed. Enable TCP/IP:")
    print()
    print("1. Open SQL Server Configuration Manager")
    print("   - Search for 'SQL Server Configuration Manager' in Start menu")
    print()
    print("2. Navigate to Network Configuration")
    print("   - Expand 'SQL Server Network Configuration'")
    print("   - Click 'Protocols for SQLEXPRESS' (or your instance name)")
    print()
    print("3. Enable TCP/IP")
    print("   - Right-click on 'TCP/IP' protocol")
    print("   - Select 'Enable'")
    print("   - Click 'OK'")
    print()
    print("4. Restart SQL Server Service")
    print("   - Go to 'SQL Server Services' in Configuration Manager")
    print("   - Right-click 'SQL Server (SQLEXPRESS)'")
    print("   - Select 'Restart'")
    print()
    print("5. Check if port 1433 is enabled")
    print("   - Right-click 'TCP/IP' → Properties")
    print("   - Go to 'IP Addresses' tab")
    print("   - Set 'TCP Port' to 1433 for IPAll")

def solution_2_connection_string():
    """Solution 2: Fix Connection String"""
    print_header("SOLUTION 2: Update Connection String")
    print("Try different server name formats:")
    print()
    print("Current server: DESKTOP-PLFK2B5\\SQLEXPRESS")
    print("Try these alternatives:")
    print()
    print("1. localhost\\SQLEXPRESS")
    print("2. .\\SQLEXPRESS") 
    print("3. (local)\\SQLEXPRESS")
    print("4. 127.0.0.1\\SQLEXPRESS")
    print("5. DESKTOP-PLFK2B5,1433")
    print()
    print("Update your environment variables:")
    print("MSSQL_SERVER=localhost\\SQLEXPRESS")
    print("or")
    print("MSSQL_SERVER=.\\SQLEXPRESS")

def solution_3_sql_authentication():
    """Solution 3: Configure SQL Server Authentication"""
    print_header("SOLUTION 3: Configure SQL Server Authentication")
    print("Enable SQL Server Authentication mode:")
    print()
    print("1. Open SQL Server Management Studio (SSMS)")
    print("2. Connect to your SQL Server instance")
    print("3. Right-click server name → Properties")
    print("4. Go to 'Security' page")
    print("5. Select 'SQL Server and Windows Authentication mode'")
    print("6. Click OK and restart SQL Server service")
    print()
    print("Create/Enable SQL Server Login:")
    print("1. Expand 'Security' → 'Logins'")
    print("2. Right-click 'Logins' → New Login")
    print("3. Set Login name (your MSSQL_USERNAME)")
    print("4. Select 'SQL Server authentication'")
    print("5. Set password (your MSSQL_PASSWORD)")
    print("6. Uncheck 'Enforce password policy' if needed")
    print("7. Go to 'User Mapping' tab")
    print("8. Check 'WMS_DB' database")
    print("9. Assign 'db_owner' role")
    print("10. Click OK")

def solution_4_firewall():
    """Solution 4: Configure Windows Firewall"""
    print_header("SOLUTION 4: Configure Windows Firewall")
    print("Allow SQL Server through Windows Firewall:")
    print()
    print("1. Open Windows Firewall with Advanced Security")
    print("2. Click 'Inbound Rules' → 'New Rule'")
    print("3. Select 'Port' → Next")
    print("4. Select 'TCP' and 'Specific local ports'")
    print("5. Enter port: 1433")
    print("6. Select 'Allow the connection'")
    print("7. Apply to all profiles")
    print("8. Name: 'SQL Server'")
    print("9. Click Finish")
    print()
    print("Alternative: Disable Windows Firewall temporarily to test")

def solution_5_service_startup():
    """Solution 5: Configure SQL Server Service"""
    print_header("SOLUTION 5: Configure SQL Server Service")
    print("Ensure SQL Server service is running:")
    print()
    print("1. Open Services (services.msc)")
    print("2. Find 'SQL Server (SQLEXPRESS)'")
    print("3. Right-click → Properties")
    print("4. Set 'Startup type' to 'Automatic'")
    print("5. Click 'Start' if not running")
    print("6. Click OK")
    print()
    print("Also check 'SQL Server Browser' service:")
    print("1. Find 'SQL Server Browser' in services")
    print("2. Set startup type to 'Automatic'")
    print("3. Start the service")

def solution_6_create_database():
    """Solution 6: Create WMS_DB Database"""
    print_header("SOLUTION 6: Create WMS_DB Database")
    print("Create the WMS_DB database if it doesn't exist:")
    print()
    print("1. Open SQL Server Management Studio")
    print("2. Connect to your SQL Server instance")
    print("3. Right-click 'Databases' → New Database")
    print("4. Database name: WMS_DB")
    print("5. Click OK")
    print()
    print("SQL Command alternative:")
    print("CREATE DATABASE WMS_DB;")

def solution_7_test_connection():
    """Solution 7: Test Connection"""
    print_header("SOLUTION 7: Test Connection")
    print("Test your connection before starting the app:")
    print()
    print("1. Run the diagnostic script:")
    print("   python fix_mssql_connection.py")
    print()
    print("2. Or test manually in Python:")
    print("   import pyodbc")
    print("   conn = pyodbc.connect(")
    print("       'DRIVER={ODBC Driver 17 for SQL Server};'")
    print("       'SERVER=localhost\\SQLEXPRESS;'")
    print("       'DATABASE=WMS_DB;'")
    print("       'UID=your_username;'")
    print("       'PWD=your_password;'")
    print("       'TrustServerCertificate=yes;'")
    print("   )")
    print("   cursor = conn.cursor()")
    print("   cursor.execute('SELECT @@VERSION')")
    print("   print(cursor.fetchone())")

def solution_8_environment_variables():
    """Solution 8: Set Environment Variables"""
    print_header("SOLUTION 8: Set Environment Variables")
    print("Set these environment variables in your system:")
    print()
    print("MSSQL_SERVER=localhost\\SQLEXPRESS")
    print("MSSQL_DATABASE=WMS_DB")
    print("MSSQL_USERNAME=your_sql_username")
    print("MSSQL_PASSWORD=your_sql_password")
    print()
    print("How to set environment variables:")
    print("1. Search 'Environment Variables' in Start menu")
    print("2. Click 'Edit environment variables for your account'")
    print("3. Click 'New' in User variables")
    print("4. Add each variable name and value")
    print("5. Click OK")
    print("6. Restart your command prompt/IDE")

def main():
    """Main function to display all solutions"""
    print("🔧 SQL Server Connection Error Solutions")
    print("Error: Named Pipes Provider: Could not open a connection to SQL Server")
    print()
    print("This error typically occurs when:")
    print("- TCP/IP protocol is disabled")
    print("- SQL Server service is not running")
    print("- Windows Firewall blocks the connection")
    print("- Incorrect server name or connection string")
    print()
    print("Try these solutions in order:")
    
    # Display all solutions
    solution_1_enable_tcp_ip()
    solution_2_connection_string()
    solution_3_sql_authentication()
    solution_4_firewall()
    solution_5_service_startup()
    solution_6_create_database()
    solution_7_test_connection()
    solution_8_environment_variables()
    
    print_header("QUICK FIX SUMMARY")
    print("Most common fixes (try in this order):")
    print()
    print("1. Enable TCP/IP in SQL Server Configuration Manager")
    print("2. Restart SQL Server service")
    print("3. Change server name to: localhost\\SQLEXPRESS")
    print("4. Create WMS_DB database")
    print("5. Test connection with diagnostic script")
    print()
    print("After fixing, your app should connect to MSSQL successfully!")
    print()
    print("Run: python fix_mssql_connection.py")
    print("to test your connection before starting the app.")

if __name__ == "__main__":
    main()