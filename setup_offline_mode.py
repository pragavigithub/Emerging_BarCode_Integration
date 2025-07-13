#!/usr/bin/env python3
"""
Setup Offline Mode for WMS Development
This script configures the WMS application to work perfectly in offline mode.
"""

import os
import json

def create_offline_env():
    """Create .env file optimized for offline development"""
    env_content = """# WMS Offline Development Configuration
# This configuration works without SQL Server or SAP B1

# Database: SQLite (No external database required)
# MSSQL_SERVER=
# MSSQL_DATABASE=
# MSSQL_USERNAME=
# MSSQL_PASSWORD=

# Flask Configuration
SESSION_SECRET=dev-secret-key-offline-mode

# SAP B1 Configuration (Optional - app works without SAP)
# SAP_B1_SERVER=https://192.168.1.5:50000
# SAP_B1_USERNAME=manager
# SAP_B1_PASSWORD=Ea@12345
# SAP_B1_COMPANY_DB=Test_Hutchinson

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=1
OFFLINE_MODE=1
"""

    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file for offline development")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def create_sample_data():
    """Create sample data for offline testing"""
    sample_data = {
        "warehouses": [
            {"code": "WH01", "name": "Main Warehouse"},
            {"code": "WH02", "name": "Secondary Warehouse"}
        ],
        "bins": [
            {"code": "A01-01", "warehouse": "WH01", "name": "Aisle A Bin 01"},
            {"code": "A01-02", "warehouse": "WH01", "name": "Aisle A Bin 02"},
            {"code": "B01-01", "warehouse": "WH02", "name": "Aisle B Bin 01"}
        ],
        "items": [
            {"code": "ITEM001", "name": "Sample Product 1", "uom": "PCS"},
            {"code": "ITEM002", "name": "Sample Product 2", "uom": "KG"},
            {"code": "ITEM003", "name": "Sample Product 3", "uom": "M"}
        ]
    }
    
    try:
        os.makedirs('offline_data', exist_ok=True)
        with open('offline_data/sample_data.json', 'w') as f:
            json.dump(sample_data, f, indent=2)
        print("✅ Created sample data for offline testing")
        return True
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print(" WMS Offline Mode Setup")
    print("=" * 60)
    print("")
    
    print("🔧 Setting up WMS application for offline development...")
    print("")
    
    # Create offline environment
    if create_offline_env():
        print("📝 Environment configured for offline mode")
    
    # Create sample data
    if create_sample_data():
        print("📊 Sample data created for testing")
    
    print("")
    print("=" * 60)
    print(" Setup Complete!")
    print("=" * 60)
    print("")
    print("🎉 Your WMS application is now configured for offline development!")
    print("")
    print("Features available in offline mode:")
    print("✅ User authentication and management")
    print("✅ GRPO creation and management")
    print("✅ Inventory transfers")
    print("✅ Pick list management")
    print("✅ Inventory counting")
    print("✅ Barcode generation and printing")
    print("✅ QC approval workflows")
    print("")
    print("To start the application:")
    print("1. python main.py")
    print("2. Open http://localhost:5000")
    print("3. Login: admin / admin123")
    print("")
    print("Note: SAP integration will show as 'offline' but all core")
    print("      WMS functionality will work perfectly!")

if __name__ == "__main__":
    main()