#!/usr/bin/env python3
"""
MySQL Migration Runner - Simple interface to run the complete MySQL migration
"""

import subprocess
import sys
import os

def main():
    print("🚀 Running Complete MySQL Migration for WMS")
    print("=" * 50)
    
    # Check if pymysql is installed
    try:
        import pymysql
        print("✅ PyMySQL is available")
    except ImportError:
        print("❌ PyMySQL not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql"])
        print("✅ PyMySQL installed")
    
    # Set MySQL environment variables if not set
    if not os.environ.get("MYSQL_HOST"):
        print("⚠️  MySQL environment variables not found.")
        print("Please set the following environment variables:")
        print("MYSQL_HOST=localhost")
        print("MYSQL_USER=root") 
        print("MYSQL_PASSWORD=your_password")
        print("MYSQL_DATABASE=wms_db_dev")
        print("\nOr export them before running this script:")
        print("export MYSQL_HOST=localhost")
        print("export MYSQL_USER=root")
        print("export MYSQL_PASSWORD=your_password")
        print("export MYSQL_DATABASE=wms_db_dev")
        return
    
    # Run the migration
    try:
        result = subprocess.run([sys.executable, "mysql_complete_migration.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("🎉 Migration completed successfully!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to run migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()