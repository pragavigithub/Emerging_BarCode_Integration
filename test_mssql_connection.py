#!/usr/bin/env python3
"""
Test MSSQL Connection Script
Run this to test your MSSQL connection before starting the main application
"""

import os
import sys
from urllib.parse import quote_plus

def test_mssql_connection():
    """Test MSSQL connection with various configurations"""
    
    # Configuration
    mssql_server = os.environ.get("MSSQL_SERVER", "DESKTOP-PLFK2B5\\SQLEXPRESS")
    mssql_database = os.environ.get("MSSQL_DATABASE", "WMS_DB")
    mssql_username = os.environ.get("MSSQL_USERNAME", "sa")
    mssql_password = os.environ.get("MSSQL_PASSWORD", "Ea@12345")
    
    print(f"Testing connection to: {mssql_server}/{mssql_database}")
    print(f"Username: {mssql_username}")
    print("-" * 50)
    
    try:
        import pyodbc
        print("✓ pyodbc module found")
    except ImportError:
        print("✗ pyodbc not installed. Run: pip install pyodbc")
        return False
    
    # Test 1: List available drivers
    print("\nAvailable ODBC drivers:")
    drivers = pyodbc.drivers()
    for driver in drivers:
        if 'SQL Server' in driver:
            print(f"  ✓ {driver}")
    
    if not any('SQL Server' in driver for driver in drivers):
        print("  ✗ No SQL Server drivers found")
        return False
    
    # Test 2: Try direct pyodbc connection
    test_configs = [
        {
            'driver': 'ODBC Driver 17 for SQL Server',
            'server': mssql_server,
            'database': mssql_database,
            'username': mssql_username,
            'password': mssql_password,
            'trusted_connection': 'no'
        },
        {
            'driver': 'SQL Server',
            'server': mssql_server,
            'database': mssql_database,
            'username': mssql_username,
            'password': mssql_password,
            'trusted_connection': 'no'
        },
        {
            'driver': 'ODBC Driver 17 for SQL Server',
            'server': mssql_server,
            'database': mssql_database,
            'trusted_connection': 'yes'
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\nTest {i}: {config['driver']}")
        try:
            if config.get('trusted_connection') == 'yes':
                conn_str = (
                    f"Driver={{{config['driver']}}};"
                    f"Server={config['server']};"
                    f"Database={config['database']};"
                    f"Trusted_Connection=yes;"
                )
            else:
                conn_str = (
                    f"Driver={{{config['driver']}}};"
                    f"Server={config['server']};"
                    f"Database={config['database']};"
                    f"UID={config['username']};"
                    f"PWD={config['password']};"
                    f"TrustServerCertificate=yes;"
                )
            
            print(f"  Connection string: {conn_str.replace(mssql_password, '***')}")
            
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            print(f"  ✓ Connection successful!")
            print(f"  SQL Server version: {version[:50]}...")
            conn.close()
            
            # Test SQLAlchemy format
            print(f"\nTesting SQLAlchemy format...")
            try:
                from sqlalchemy import create_engine, text
                
                encoded_server = quote_plus(config['server'])
                if config.get('trusted_connection') == 'yes':
                    sa_url = f"mssql+pyodbc://{encoded_server}/{config['database']}?driver={quote_plus(config['driver'])}&trusted_connection=yes"
                else:
                    encoded_username = quote_plus(config['username'])
                    encoded_password = quote_plus(config['password'])
                    sa_url = f"mssql+pyodbc://{encoded_username}:{encoded_password}@{encoded_server}/{config['database']}?driver={quote_plus(config['driver'])}&TrustServerCertificate=yes"
                
                print(f"  SQLAlchemy URL: {sa_url.replace(quote_plus(mssql_password), '***')}")
                
                engine = create_engine(sa_url)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    print(f"  ✓ SQLAlchemy connection successful!")
                    return True
                    
            except Exception as sa_error:
                print(f"  ✗ SQLAlchemy error: {sa_error}")
                continue
                
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
            continue
    
    print("\n" + "="*50)
    print("All connection attempts failed!")
    print("Troubleshooting suggestions:")
    print("1. Verify SQL Server is running and accepting connections")
    print("2. Check if SQL Server Browser service is running")
    print("3. Verify the instance name (SQLEXPRESS)")
    print("4. Check Windows Firewall settings")
    print("5. Enable TCP/IP protocol in SQL Server Configuration Manager")
    print("6. Try connecting with SQL Server Management Studio first")
    return False

if __name__ == "__main__":
    success = test_mssql_connection()
    sys.exit(0 if success else 1)