#!/usr/bin/env python3
"""
Quick runner script for MySQL Inventory Transfer Migration
"""

import subprocess
import sys
import os

def main():
    """Run the MySQL inventory transfer migration"""
    
    print("🚀 Running MySQL Inventory Transfer Migration")
    print("=" * 50)
    
    # Check if migration file exists
    migration_file = "mysql_inventory_transfer_migration.py"
    if not os.path.exists(migration_file):
        print(f"❌ Migration file '{migration_file}' not found!")
        sys.exit(1)
    
    try:
        # Run the migration script
        result = subprocess.run([sys.executable, migration_file], 
                              capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("Errors:", result.stderr)
        
        # Check result
        if result.returncode == 0:
            print("\n✅ Migration completed successfully!")
        else:
            print(f"\n❌ Migration failed with exit code: {result.returncode}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running migration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()