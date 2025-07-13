#!/usr/bin/env python3
"""
EMERGENCY MySQL Database Fix
This will fix the missing 'notes' column issue immediately
"""

import os
import sys

def emergency_fix():
    """Emergency fix for MySQL missing columns"""
    
    print("EMERGENCY MySQL Database Fix")
    print("="*50)
    
    try:
        import pymysql
        
        # Connection parameters with defaults
        config = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ.get('MYSQL_PASSWORD', ''),
            'database': os.environ.get('MYSQL_DATABASE', 'wms_db'),
            'charset': 'utf8mb4'
        }
        
        print(f"Connecting to MySQL at {config['host']}:{config['port']}")
        print(f"Database: {config['database']}")
        
        connection = pymysql.connect(**config)
        cursor = connection.cursor()
        
        # Fix the immediate issue - add notes column
        print("\n1. Adding missing 'notes' column...")
        try:
            cursor.execute("ALTER TABLE grpo_documents ADD COLUMN notes TEXT")
            print("   ✓ Added 'notes' column to grpo_documents")
        except pymysql.Error as e:
            if "Duplicate column name" in str(e):
                print("   ✓ 'notes' column already exists")
            else:
                print(f"   ✗ Error: {e}")
        
        # Add other critical columns
        critical_fixes = [
            ("grpo_documents", "qc_notes", "TEXT"),
            ("grpo_documents", "draft_or_post", "VARCHAR(10) DEFAULT 'draft'"),
            ("grpo_items", "generated_barcode", "VARCHAR(100)"),
            ("grpo_items", "barcode_printed", "BOOLEAN DEFAULT FALSE"),
            ("grpo_items", "qc_status", "VARCHAR(20) DEFAULT 'pending'"),
            ("grpo_items", "qc_notes", "TEXT"),
        ]
        
        print("\n2. Adding other essential columns...")
        for table, column, column_type in critical_fixes:
            try:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
                cursor.execute(sql)
                print(f"   ✓ Added '{column}' to {table}")
            except pymysql.Error as e:
                if "Duplicate column name" in str(e):
                    print(f"   ✓ '{column}' already exists in {table}")
                else:
                    print(f"   ⚠ Could not add '{column}' to {table}: {e}")
        
        connection.commit()
        
        print("\n3. Verifying table structure...")
        cursor.execute("DESCRIBE grpo_documents")
        columns = cursor.fetchall()
        
        required_columns = ['notes', 'qc_notes', 'draft_or_post']
        found_columns = [col[0] for col in columns]
        
        print("   grpo_documents columns:")
        for col in found_columns:
            status = "✓" if col in required_columns else " "
            print(f"   {status} {col}")
        
        missing = [col for col in required_columns if col not in found_columns]
        if missing:
            print(f"\n   ⚠ Still missing: {missing}")
        else:
            print(f"\n   ✓ All required columns present!")
        
        cursor.close()
        connection.close()
        
        print("\n" + "="*50)
        print("✓ EMERGENCY FIX COMPLETED!")
        print("✓ Your application should now work without errors")
        print("="*50)
        
        return True
        
    except ImportError:
        print("✗ PyMySQL not installed")
        print("Run: pip install pymysql")
        return False
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify MySQL is running")
        print("2. Check your environment variables:")
        print("   export MYSQL_HOST=localhost")
        print("   export MYSQL_USER=root")
        print("   export MYSQL_PASSWORD=your_password")
        print("   export MYSQL_DATABASE=wms_db")
        print("3. Ensure the database 'wms_db' exists")
        return False

if __name__ == "__main__":
    success = emergency_fix()
    sys.exit(0 if success else 1)