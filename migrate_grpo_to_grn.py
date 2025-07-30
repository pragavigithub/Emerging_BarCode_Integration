#!/usr/bin/env python3
"""
Migrate GRPO to GRN (Goods Received Note) Script
Changes all GRPO terminology to GRN throughout the application
"""

import os
import mysql.connector
from mysql.connector import Error

def migrate_database_tables():
    """Migrate database tables from GRPO to GRN"""
    
    # Database connection details
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', '3306'))
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', 'root@123')
    database = os.environ.get('MYSQL_DATABASE', 'wms_test')
    
    try:
        print("🔧 Connecting to MySQL database...")
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        print("📝 Step 1: Check if GRPO tables exist...")
        
        # Check if grpo_documents table exists
        cursor.execute("SHOW TABLES LIKE 'grpo_documents'")
        grpo_docs_exists = cursor.fetchone()
        
        cursor.execute("SHOW TABLES LIKE 'grpo_items'")
        grpo_items_exists = cursor.fetchone()
        
        if grpo_docs_exists:
            print("📝 Step 2: Rename grpo_documents to grn_documents...")
            cursor.execute("RENAME TABLE grpo_documents TO grn_documents")
            print("✅ grpo_documents renamed to grn_documents")
        
        if grpo_items_exists:
            print("📝 Step 3: Rename grpo_items to grn_items...")
            cursor.execute("RENAME TABLE grpo_items TO grn_items")
            print("✅ grpo_items renamed to grn_items")
            
            print("📝 Step 4: Update column names in grn_items...")
            cursor.execute("ALTER TABLE grn_items CHANGE COLUMN grpo_document_id grn_document_id INT NOT NULL")
            print("✅ grpo_document_id renamed to grn_document_id")
            
            # Update foreign key constraint
            cursor.execute("ALTER TABLE grn_items DROP FOREIGN KEY IF EXISTS grn_items_ibfk_1")
            cursor.execute("ALTER TABLE grn_items ADD CONSTRAINT grn_items_ibfk_1 FOREIGN KEY (grn_document_id) REFERENCES grn_documents(id) ON DELETE CASCADE")
            print("✅ Foreign key constraint updated")
        
        print("📝 Step 5: Update document number series...")
        cursor.execute("UPDATE document_number_series SET document_type = 'GRN', prefix = 'GRN-' WHERE document_type = 'GRPO'")
        print("✅ Document number series updated from GRPO to GRN")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n🎉 Database migration from GRPO to GRN completed successfully!")
        return True
        
    except Error as e:
        print(f"❌ Database migration error: {e}")
        return False

def update_permission_references():
    """Update permission references in user table"""
    
    # Database connection details
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', '3306'))
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', '')
    database = os.environ.get('MYSQL_DATABASE', 'wms_db')
    
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        print("📝 Updating user permissions from 'grpo' to 'grn'...")
        cursor.execute("UPDATE users SET permissions = REPLACE(permissions, '\"grpo\"', '\"grn\"') WHERE permissions LIKE '%grpo%'")
        print("✅ User permissions updated")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Permission update error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("   GRPO to GRN Migration Script")
    print("=" * 60)
    print()
    
    # Migrate database tables
    if migrate_database_tables():
        print("✅ Database migration successful")
    else:
        print("❌ Database migration failed")
        exit(1)
    
    # Update permission references
    if update_permission_references():
        print("✅ Permission updates successful")
    else:
        print("❌ Permission updates failed")
    
    print("\n🚀 GRPO to GRN migration completed!")
    print("📌 Please restart your Flask application to see the changes.")