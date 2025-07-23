#!/usr/bin/env python3
"""
MySQL Environment Setup and Migration Script
==========================================

This script helps you set up MySQL environment variables and run the migration.
"""

import os
import sys

def setup_mysql_environment():
    """Interactive setup for MySQL environment variables"""
    
    print("=" * 60)
    print("   MySQL Environment Setup")
    print("=" * 60)
    print()
    
    # Get MySQL configuration from user
    print("Please enter your MySQL database connection details:")
    print()
    
    mysql_host = input("MySQL Host (default: localhost): ").strip()
    if not mysql_host:
        mysql_host = "localhost"
    
    mysql_user = input("MySQL Username (default: root): ").strip()
    if not mysql_user:
        mysql_user = "root"
    
    mysql_password = input("MySQL Password: ").strip()
    
    mysql_database = input("MySQL Database Name (default: wms_database): ").strip()
    if not mysql_database:
        mysql_database = "wms_database"
    
    # Set environment variables
    os.environ['MYSQL_HOST'] = mysql_host
    os.environ['MYSQL_USER'] = mysql_user
    os.environ['MYSQL_PASSWORD'] = mysql_password
    os.environ['MYSQL_DATABASE'] = mysql_database
    
    print()
    print("✅ Environment variables set successfully!")
    print(f"   Host: {mysql_host}")
    print(f"   User: {mysql_user}")
    print(f"   Database: {mysql_database}")
    print()
    
    return True

def run_migration():
    """Run the MySQL migration"""
    
    print("🔧 Starting MySQL database migration...")
    print()
    
    # Import and run the migration
    try:
        # Import the migration script as a module
        import importlib.util
        spec = importlib.util.spec_from_file_location("migration", "complete_mysql_migration.py")
        migration_module = importlib.util.module_from_spec(spec)
        
        # Execute the migration
        spec.loader.exec_module(migration_module)
        migration_module.main()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

def main():
    """Main function"""
    
    # Setup environment variables
    if not setup_mysql_environment():
        print("❌ Failed to setup environment variables")
        sys.exit(1)
    
    # Run migration
    if not run_migration():
        print("❌ Migration failed")
        sys.exit(1)
    
    print()
    print("🎉 Setup and migration completed successfully!")
    print()
    print("You can now run your Flask application without database errors.")

if __name__ == "__main__":
    main()