#!/usr/bin/env python3
"""
Fix MySQL bin_location Column Size Issue
This script specifically fixes the "Data too long for column 'bin_location'" error
by increasing the column size from VARCHAR(20) to VARCHAR(100) in MySQL.
"""

import mysql.connector
import pymysql
import os
from dotenv import load_dotenv

def fix_mysql_bin_location():
    """Fix the bin_location column size issue in MySQL"""
    load_dotenv()
    
    # MySQL connection parameters
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'warehouse_management'),
        'charset': 'utf8mb4'
    }
    
    print("🔧 Starting MySQL bin_location column fix...")
    
    try:
        # Try PyMySQL first
        connection = pymysql.connect(**mysql_config)
        print("✅ Connected to MySQL database using PyMySQL")
        
        with connection.cursor() as cursor:
            # Fix grn_items table
            print("📝 Fixing grn_items.bin_location column...")
            cursor.execute("""
                ALTER TABLE grn_items 
                MODIFY COLUMN bin_location VARCHAR(100) NOT NULL
            """)
            print("✅ Fixed grn_items.bin_location column size")
            
            # Fix pick_list_items table if exists
            print("📝 Fixing pick_list_items.bin_location column...")
            try:
                cursor.execute("""
                    ALTER TABLE pick_list_items 
                    MODIFY COLUMN bin_location VARCHAR(100) NOT NULL
                """)
                print("✅ Fixed pick_list_items.bin_location column size")
            except Exception as e:
                print(f"⚠️ pick_list_items table may not exist: {e}")
            
            # Fix inventory_transfer_items table if exists
            print("📝 Fixing inventory_transfer_items.bin_location column...")
            try:
                cursor.execute("""
                    ALTER TABLE inventory_transfer_items 
                    MODIFY COLUMN bin_location VARCHAR(100)
                """)
                print("✅ Fixed inventory_transfer_items.bin_location column size")
            except Exception as e:
                print(f"⚠️ inventory_transfer_items table may not exist: {e}")
                
            # Add missing columns if they don't exist
            print("📝 Adding missing columns to grn_items...")
            try:
                cursor.execute("""
                    ALTER TABLE grn_items 
                    ADD COLUMN IF NOT EXISTS po_line_number INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS po_quantity DECIMAL(15,3),
                    ADD COLUMN IF NOT EXISTS open_quantity DECIMAL(15,3),
                    ADD COLUMN IF NOT EXISTS unit_price DECIMAL(15,4),
                    ADD COLUMN IF NOT EXISTS supplier_barcode VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS generated_barcode VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS barcode_printed BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS qc_status VARCHAR(20) DEFAULT 'pending',
                    ADD COLUMN IF NOT EXISTS qc_notes TEXT
                """)
                print("✅ Added missing columns to grn_items")
            except Exception as e:
                print(f"⚠️ Some columns may already exist: {e}")
            
        connection.commit()
        connection.close()
        print("🎉 MySQL bin_location fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing MySQL bin_location: {e}")
        print("\n🔍 Troubleshooting steps:")
        print("1. Make sure MySQL is running")
        print("2. Check your .env file has correct MySQL credentials:")
        print("   MYSQL_HOST=localhost")
        print("   MYSQL_USER=root") 
        print("   MYSQL_PASSWORD=your_password")
        print("   MYSQL_DATABASE=warehouse_management")
        print("3. Make sure the database exists")
        return False

if __name__ == "__main__":
    print("🚀 Starting MySQL bin_location Column Fix...")
    
    if fix_mysql_bin_location():
        print("\n✅ Fix completed! You can now add GRN items without the column size error.")
        print("The bin_location column has been increased to VARCHAR(100) in all relevant tables.")
    else:
        print("\n❌ Fix failed. Please check the error messages above and try again.")