#!/usr/bin/env python3
"""
MSSQL Connection Fix Script
This script helps diagnose and fix MSSQL connection issues.
"""

import os
import sys
import logging
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def check_sql_server_service():
    """Check if SQL Server service is running"""
    try:
        import subprocess
        result = subprocess.run(['sc', 'query', 'MSSQLSERVER'], 
                              capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            logging.info("✅ SQL Server (MSSQLSERVER) service is running")
            return True
        else:
            logging.warning("❌ SQL Server (MSSQLSERVER) service is not running")
            
        # Check for SQL Server Express
        result = subprocess.run(['sc', 'query', 'MSSQL$SQLEXPRESS'], 
                              capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            logging.info("✅ SQL Server Express service is running")
            return True
        else:
            logging.warning("❌ SQL Server Express service is not running")
            
        return False
    except Exception as e:
        logging.error(f"Error checking SQL Server service: {e}")
        return False

def check_tcp_ip_enabled():
    """Check if TCP/IP is enabled for SQL Server"""
    logging.info("📋 To enable TCP/IP for SQL Server:")
    logging.info("1. Open SQL Server Configuration Manager")
    logging.info("2. Go to SQL Server Network Configuration")
    logging.info("3. Select Protocols for your SQL Server instance")
    logging.info("4. Enable TCP/IP protocol")
    logging.info("5. Restart SQL Server service")

def test_basic_connection():
    """Test basic connection to SQL Server"""
    server = os.environ.get('MSSQL_SERVER', 'DESKTOP-PLFK2B5\\SQLEXPRESS')
    database = os.environ.get('MSSQL_DATABASE', 'WMS_DB')
    username = os.environ.get('MSSQL_USERNAME', '')
    password = os.environ.get('MSSQL_PASSWORD', '')
    
    if not username or not password:
        logging.error("❌ MSSQL username or password not set in environment variables")
        return False
    
    try:
        import pyodbc
        logging.info("✅ pyodbc module available")
        
        # List available drivers
        drivers = pyodbc.drivers()
        sql_drivers = [d for d in drivers if 'SQL Server' in d]
        
        if not sql_drivers:
            logging.error("❌ No SQL Server ODBC drivers found")
            logging.info("Install ODBC Driver 17 for SQL Server from Microsoft")
            return False
        
        logging.info(f"✅ Available SQL Server drivers: {sql_drivers}")
        
        # Test connection configurations
        configs = [
            {
                'name': 'TCP/IP Connection',
                'conn_str': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
            },
            {
                'name': 'Named Pipes Connection',
                'conn_str': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Pipe=SQL\\Query;"
            },
            {
                'name': 'SQL Server Driver',
                'conn_str': f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
            }
        ]
        
        for config in configs:
            try:
                logging.info(f"Testing {config['name']}...")
                conn = pyodbc.connect(config['conn_str'], timeout=10)
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                logging.info(f"✅ {config['name']} successful!")
                logging.info(f"   SQL Server version: {version[:50]}...")
                conn.close()
                return True
            except Exception as e:
                logging.warning(f"❌ {config['name']} failed: {e}")
                continue
        
        return False
        
    except ImportError:
        logging.error("❌ pyodbc not installed. Run: pip install pyodbc")
        return False
    except Exception as e:
        logging.error(f"❌ Connection test failed: {e}")
        return False

def suggest_solutions():
    """Suggest solutions for common connection issues"""
    logging.info("\n🔧 Common Solutions:")
    logging.info("1. Enable TCP/IP Protocol:")
    logging.info("   - Open SQL Server Configuration Manager")
    logging.info("   - Enable TCP/IP in Network Configuration")
    logging.info("   - Restart SQL Server service")
    
    logging.info("\n2. Check SQL Server Authentication:")
    logging.info("   - Enable SQL Server and Windows Authentication mode")
    logging.info("   - Create/enable SQL Server login user")
    
    logging.info("\n3. Check Firewall:")
    logging.info("   - Allow SQL Server through Windows Firewall")
    logging.info("   - Default port: 1433")
    
    logging.info("\n4. Check SQL Server Service:")
    logging.info("   - Ensure SQL Server service is running")
    logging.info("   - Check service startup type")
    
    logging.info("\n5. Connection String Format:")
    logging.info("   - Server: DESKTOP-PLFK2B5\\SQLEXPRESS")
    logging.info("   - Or try: localhost\\SQLEXPRESS")
    logging.info("   - Or try: .\\SQLEXPRESS")

def main():
    """Main diagnostic function"""
    logging.info("🔍 MSSQL Connection Diagnostics")
    logging.info("=" * 50)
    
    # Check environment variables
    server = os.environ.get('MSSQL_SERVER')
    database = os.environ.get('MSSQL_DATABASE')
    username = os.environ.get('MSSQL_USERNAME')
    password = os.environ.get('MSSQL_PASSWORD')
    
    logging.info(f"Server: {server}")
    logging.info(f"Database: {database}")
    logging.info(f"Username: {username}")
    logging.info(f"Password: {'*' * len(password) if password else 'Not set'}")
    
    if not all([server, database, username, password]):
        logging.error("❌ Missing environment variables")
        logging.info("Set: MSSQL_SERVER, MSSQL_DATABASE, MSSQL_USERNAME, MSSQL_PASSWORD")
        return
    
    # Run diagnostics
    logging.info("\n🔍 Running diagnostics...")
    
    # Check SQL Server service
    check_sql_server_service()
    
    # Check TCP/IP configuration
    check_tcp_ip_enabled()
    
    # Test connection
    if test_basic_connection():
        logging.info("\n✅ Connection test successful!")
        logging.info("Your MSSQL connection should work now.")
    else:
        logging.error("\n❌ Connection test failed!")
        suggest_solutions()

if __name__ == "__main__":
    main()