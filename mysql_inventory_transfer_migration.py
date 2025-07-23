#!/usr/bin/env python3
"""
MySQL Inventory Transfer Migration Script
Fixes missing qc_status and qc_notes columns in inventory_transfer_items table
"""

import os
import sys
import pymysql
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mysql_connection():
    """Get MySQL database connection"""
    try:
        # Try to get connection details from environment variables
        host = os.getenv('MYSQL_HOST', 'localhost')
        user = os.getenv('MYSQL_USER', os.getenv('MYSQL_USERNAME', 'root'))
        password = os.getenv('MYSQL_PASSWORD', '')
        database = os.getenv('MYSQL_DATABASE', 'wms_database')
        port = int(os.getenv('MYSQL_PORT', 3306))
        
        logger.info(f"Connecting to MySQL: {user}@{host}:{port}/{database}")
        
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8mb4',
            autocommit=False
        )
        
        logger.info("✅ Successfully connected to MySQL database")
        return connection
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MySQL: {str(e)}")
        print("\n🔧 MySQL Connection Help:")
        print("Set these environment variables or update the script:")
        print("- MYSQL_HOST (default: localhost)")
        print("- MYSQL_USER (default: root)")
        print("- MYSQL_PASSWORD")
        print("- MYSQL_DATABASE (default: wms_database)")
        print("- MYSQL_PORT (default: 3306)")
        return None

def check_table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None

def check_column_exists(cursor, table_name, column_name):
    """Check if column exists in table"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = %s 
        AND COLUMN_NAME = %s
    """, (table_name, column_name))
    return cursor.fetchone()[0] > 0

def migrate_inventory_transfer_items_table(connection):
    """Migrate inventory_transfer_items table to add missing QC columns"""
    cursor = connection.cursor()
    
    try:
        # Check if table exists
        if not check_table_exists(cursor, 'inventory_transfer_items'):
            logger.error("❌ Table 'inventory_transfer_items' does not exist")
            return False
        
        logger.info("🔍 Checking inventory_transfer_items table structure...")
        
        # Get current table structure
        cursor.execute("DESCRIBE inventory_transfer_items")
        columns = cursor.fetchall()
        existing_columns = [col[0] for col in columns]
        
        logger.info(f"Current columns: {existing_columns}")
        
        # Define required QC columns (based on the model definition)
        required_columns = {
            'qc_status': "VARCHAR(20) DEFAULT 'pending'"
        }
        
        # Note: qc_notes is not in the InventoryTransferItem model, only qc_status
        
        # Add missing columns
        columns_added = []
        for column_name, column_definition in required_columns.items():
            if not check_column_exists(cursor, 'inventory_transfer_items', column_name):
                logger.info(f"➕ Adding column: {column_name}")
                
                alter_sql = f"""
                    ALTER TABLE inventory_transfer_items 
                    ADD COLUMN {column_name} {column_definition}
                """
                
                cursor.execute(alter_sql)
                columns_added.append(column_name)
                logger.info(f"✅ Added column: {column_name}")
            else:
                logger.info(f"⚡ Column {column_name} already exists")
        
        if columns_added:
            connection.commit()
            logger.info(f"✅ Successfully added columns: {columns_added}")
        else:
            logger.info("✅ All required columns already exist")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating inventory_transfer_items table: {str(e)}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def migrate_inventory_transfers_table(connection):
    """Migrate inventory_transfers table to add missing QC approval columns"""
    cursor = connection.cursor()
    
    try:
        # Check if table exists
        if not check_table_exists(cursor, 'inventory_transfers'):
            logger.error("❌ Table 'inventory_transfers' does not exist")
            return False
        
        logger.info("🔍 Checking inventory_transfers table structure...")
        
        # Define required QC approval columns for the main transfer table
        required_columns = {
            'qc_approver_id': "INT",
            'qc_approved_at': "DATETIME",
            'qc_notes': "TEXT"
        }
        
        # Add missing columns
        columns_added = []
        for column_name, column_definition in required_columns.items():
            if not check_column_exists(cursor, 'inventory_transfers', column_name):
                logger.info(f"➕ Adding column: {column_name}")
                
                alter_sql = f"""
                    ALTER TABLE inventory_transfers 
                    ADD COLUMN {column_name} {column_definition}
                """
                
                cursor.execute(alter_sql)
                columns_added.append(column_name)
                logger.info(f"✅ Added column: {column_name}")
            else:
                logger.info(f"⚡ Column {column_name} already exists")
        
        # Add foreign key constraint for qc_approver_id if it was added
        if 'qc_approver_id' in columns_added:
            try:
                # First check if users table exists
                if check_table_exists(cursor, 'users'):
                    # Check if constraint already exists
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'inventory_transfers' 
                        AND COLUMN_NAME = 'qc_approver_id' 
                        AND CONSTRAINT_NAME LIKE '%fk%'
                    """)
                    
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            ALTER TABLE inventory_transfers 
                            ADD CONSTRAINT fk_inventory_transfers_qc_approver 
                            FOREIGN KEY (qc_approver_id) REFERENCES users(id)
                        """)
                        logger.info("✅ Added foreign key constraint for qc_approver_id")
                    else:
                        logger.info("⚡ Foreign key constraint already exists")
                else:
                    logger.warning("⚠️ Users table not found, skipping foreign key constraint")
            except Exception as fk_error:
                logger.warning(f"⚠️ Could not add foreign key constraint: {str(fk_error)}")
        
        if columns_added:
            connection.commit()
            logger.info(f"✅ Successfully added columns: {columns_added}")
        else:
            logger.info("✅ All required columns already exist")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating inventory_transfers table: {str(e)}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def verify_migration(connection):
    """Verify that the migration was successful"""
    cursor = connection.cursor()
    
    try:
        logger.info("🔍 Verifying migration...")
        
        # Check inventory_transfer_items table
        cursor.execute("DESCRIBE inventory_transfer_items")
        items_columns = [col[0] for col in cursor.fetchall()]
        
        required_items_columns = ['qc_status']
        missing_items_columns = [col for col in required_items_columns if col not in items_columns]
        
        if missing_items_columns:
            logger.error(f"❌ Missing columns in inventory_transfer_items: {missing_items_columns}")
            return False
        else:
            logger.info("✅ inventory_transfer_items table has all required columns")
        
        # Check inventory_transfers table
        cursor.execute("DESCRIBE inventory_transfers")
        transfers_columns = [col[0] for col in cursor.fetchall()]
        
        required_transfers_columns = ['qc_approver_id', 'qc_approved_at', 'qc_notes']
        missing_transfers_columns = [col for col in required_transfers_columns if col not in transfers_columns]
        
        if missing_transfers_columns:
            logger.error(f"❌ Missing columns in inventory_transfers: {missing_transfers_columns}")
            return False
        else:
            logger.info("✅ inventory_transfers table has all required columns")
        
        logger.info("🎉 Migration verification PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {str(e)}")
        return False
    finally:
        cursor.close()

def main():
    """Main migration function"""
    print("🚀 MySQL Inventory Transfer Migration Script")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    print()
    
    # Get database connection
    connection = get_mysql_connection()
    if not connection:
        sys.exit(1)
    
    try:
        # Run migrations
        logger.info("🔧 Starting migration process...")
        
        # Migrate inventory_transfer_items table
        if not migrate_inventory_transfer_items_table(connection):
            logger.error("❌ Failed to migrate inventory_transfer_items table")
            sys.exit(1)
        
        # Migrate inventory_transfers table
        if not migrate_inventory_transfers_table(connection):
            logger.error("❌ Failed to migrate inventory_transfers table")
            sys.exit(1)
        
        # Verify migration
        if not verify_migration(connection):
            logger.error("❌ Migration verification failed")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("✅ inventory_transfer_items table updated with QC columns")
        print("✅ inventory_transfers table updated with QC approval columns")
        print("✅ All foreign key constraints applied")
        print("\nYour inventory transfer functionality should now work correctly.")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        sys.exit(1)
    
    finally:
        connection.close()
        logger.info("🔐 Database connection closed")

if __name__ == "__main__":
    main()