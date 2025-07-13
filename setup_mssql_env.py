#!/usr/bin/env python3
"""
MSSQL Environment Setup Script for WMS Application
This script helps you configure the MSSQL database connection for Replit deployment.
"""

import os
import sys

def main():
    print("=== WMS MSSQL Database Configuration ===")
    print()
    print("To connect to your MSSQL database, please provide the following information:")
    print()
    
    # Get MSSQL connection details
    mssql_server = input("Enter MSSQL Server (e.g., localhost, 192.168.1.100): ").strip()
    mssql_database = input("Enter Database Name (e.g., WMS_DB): ").strip()
    mssql_username = input("Enter Username: ").strip()
    mssql_password = input("Enter Password: ").strip()
    
    if not all([mssql_server, mssql_database, mssql_username, mssql_password]):
        print("❌ All fields are required!")
        return
    
    print("\n=== Configuration Summary ===")
    print(f"Server: {mssql_server}")
    print(f"Database: {mssql_database}")
    print(f"Username: {mssql_username}")
    print(f"Password: {'*' * len(mssql_password)}")
    print()
    
    confirm = input("Is this information correct? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Setup cancelled.")
        return
    
    print("\n=== Setting Environment Variables ===")
    print()
    print("To configure your MSSQL database in Replit, follow these steps:")
    print()
    print("1. Go to your Replit project")
    print("2. Open the 'Secrets' tab (lock icon in the left sidebar)")
    print("3. Add the following environment variables:")
    print()
    print(f"   MSSQL_SERVER = {mssql_server}")
    print(f"   MSSQL_DATABASE = {mssql_database}")
    print(f"   MSSQL_USERNAME = {mssql_username}")
    print(f"   MSSQL_PASSWORD = {mssql_password}")
    print()
    print("4. After adding all variables, restart your application")
    print("5. Your WMS will now connect to your MSSQL database")
    print()
    print("✅ Configuration complete!")
    print()
    print("Note: Make sure your MSSQL server is accessible from Replit")
    print("and has the necessary ODBC drivers installed.")

if __name__ == "__main__":
    main()