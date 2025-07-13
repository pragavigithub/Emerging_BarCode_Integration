#!/usr/bin/env python3
"""
Quick fix to disable MSSQL and use SQLite
This script updates the .env file to disable MSSQL connection.
"""

import os

def disable_mssql():
    """Disable MSSQL by clearing environment variables"""
    print("🔧 Disabling MSSQL connection...")
    
    # Read current .env file
    env_content = ""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
    
    # Update MSSQL variables to empty values
    updated_content = []
    for line in env_content.split('\n'):
        if line.startswith('MSSQL_'):
            # Clear MSSQL variables
            key = line.split('=')[0] if '=' in line else line
            updated_content.append(f"{key}=")
        else:
            updated_content.append(line)
    
    # Write updated content
    with open('.env', 'w') as f:
        f.write('\n'.join(updated_content))
    
    print("✅ MSSQL connection disabled")
    print("📋 Updated .env file:")
    print("   MSSQL_SERVER=")
    print("   MSSQL_DATABASE=")
    print("   MSSQL_USERNAME=")
    print("   MSSQL_PASSWORD=")
    print()
    print("🎉 Your application will now use SQLite for local development")
    print("Run: python main.py")

if __name__ == "__main__":
    disable_mssql()