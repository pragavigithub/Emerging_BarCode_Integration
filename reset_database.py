#!/usr/bin/env python3
"""
Simple Database Reset Script for WMS Application
This script will recreate your database with the correct schema.
WARNING: This will delete all existing data!
"""

import os
import sys
from datetime import datetime

def get_database_path():
    """Get the SQLite database path"""
    # Common SQLite database locations
    possible_paths = [
        'instance/database.db',
        'database.db',
        'wms.db',
        'app.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If no database found, use the default Flask instance path
    return 'instance/database.db'

def backup_database(db_path):
    """Create a backup of the current database"""
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        
        # Copy the database file
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path
    return None

def main():
    """Main reset function"""
    print("WMS Database Reset Tool")
    print("=" * 40)
    print("⚠️  WARNING: This will DELETE ALL DATA in your database!")
    print()
    
    # Get user confirmation
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    if response != 'yes':
        print("Operation cancelled.")
        sys.exit(0)
    
    # Get database path
    db_path = get_database_path()
    print(f"Database path: {db_path}")
    
    # Create backup if database exists
    if os.path.exists(db_path):
        backup_path = backup_database(db_path)
        
        # Delete the old database
        os.remove(db_path)
        print(f"✓ Old database deleted: {db_path}")
    else:
        print("No existing database found.")
    
    # Create instance directory if it doesn't exist
    instance_dir = os.path.dirname(db_path)
    if instance_dir and not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"✓ Created directory: {instance_dir}")
    
    print()
    print("✅ Database reset completed!")
    print()
    print("Next steps:")
    print("1. Start your Flask application")
    print("2. The database will be recreated with the correct schema")
    print("3. You can then create a new admin user and start using the system")
    print()
    print("To create an admin user, use the following credentials when you first login:")
    print("Username: admin")
    print("Password: admin123")

if __name__ == "__main__":
    main()