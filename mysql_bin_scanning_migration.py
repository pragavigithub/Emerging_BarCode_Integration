#!/usr/bin/env python3
"""
MySQL Migration Script for Bin Scanning Module
This script creates the necessary database tables and fields for bin scanning functionality.
"""

import mysql.connector
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_mysql_connection():
    """Get MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', 'root@123'),
            database=os.environ.get('MYSQL_DATABASE', 'wms_db_dev'),
            autocommit=True
        )
        logging.info("✅ Connected to MySQL database successfully")
        return connection
    except mysql.connector.Error as e:
        logging.error(f"❌ Error connecting to MySQL: {e}")
        return None

def create_bin_scanning_tables(connection):
    """Create tables for bin scanning functionality"""
    cursor = connection.cursor()
    
    try:
        # Create bin_locations table for storing bin information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bin_locations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bin_code VARCHAR(100) NOT NULL UNIQUE,
                warehouse_code VARCHAR(50) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                is_system_bin BOOLEAN DEFAULT FALSE,
                max_capacity DECIMAL(10,3) DEFAULT 0,
                current_capacity DECIMAL(10,3) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_bin_code (bin_code),
                INDEX idx_warehouse_code (warehouse_code)
            ) ENGINE=InnoDB
        """)
        logging.info("✅ Created bin_locations table")
        
        # Create bin_items table for real-time SAP B1 bin scanning integration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bin_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bin_code VARCHAR(100) NOT NULL,
                item_code VARCHAR(100) NOT NULL,
                item_name VARCHAR(255),
                batch_number VARCHAR(100),
                quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
                available_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
                committed_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
                uom VARCHAR(20) DEFAULT 'EA',
                expiry_date DATE,
                manufacturing_date DATE,
                admission_date DATE,
                warehouse_code VARCHAR(50),
                sap_abs_entry INT,
                sap_system_number INT,
                sap_doc_entry INT,
                batch_attribute1 VARCHAR(100),
                batch_attribute2 VARCHAR(100),
                batch_status VARCHAR(50) DEFAULT 'bdsStatus_Released',
                last_sap_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_bin_item (bin_code, item_code),
                INDEX idx_item_code (item_code),
                INDEX idx_batch_number (batch_number),
                INDEX idx_warehouse_code (warehouse_code),
                INDEX idx_batch_attribute2 (batch_attribute2),
                INDEX idx_sap_sync (last_sap_sync),
                UNIQUE KEY unique_bin_item_batch (bin_code, item_code, batch_number)
            ) ENGINE=InnoDB
        """)
        logging.info("✅ Created bin_items table")
        
        # Create bin_scanning_logs table for audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bin_scanning_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bin_code VARCHAR(100) NOT NULL,
                user_id INT,
                scan_type ENUM('BIN_SCAN', 'ITEM_SCAN', 'QR_SCAN') DEFAULT 'BIN_SCAN',
                scan_data TEXT,
                items_found INT DEFAULT 0,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(100),
                INDEX idx_bin_code (bin_code),
                INDEX idx_user_id (user_id),
                INDEX idx_scan_timestamp (scan_timestamp),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)
        logging.info("✅ Created bin_scanning_logs table")
        
        # Add any missing columns to existing tables
        add_missing_columns(cursor)
        
        connection.commit()
        logging.info("🎉 All bin scanning tables created successfully!")
        
    except mysql.connector.Error as e:
        logging.error(f"❌ Error creating tables: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

def add_missing_columns(cursor):
    """Add any missing columns to existing tables"""
    try:
        # Add SAP integration fields to existing tables if they don't exist
        missing_columns = [
            # GRPO documents - add SAP fields if missing
            ("grpo_documents", "sap_doc_entry", "INT"),
            ("grpo_documents", "sap_doc_num", "VARCHAR(50)"),
            ("grpo_documents", "warehouse_code", "VARCHAR(50)"),
            
            # GRPO items - add bin location and SAP fields
            ("grpo_items", "bin_location", "VARCHAR(100)"),
            ("grpo_items", "sap_line_num", "INT"),
            ("grpo_items", "sap_abs_entry", "INT"),
            
            # Inventory transfers - add bin scanning support
            ("inventory_transfer_items", "from_bin_code", "VARCHAR(100)"),
            ("inventory_transfer_items", "to_bin_code", "VARCHAR(100)"),
            ("inventory_transfer_items", "sap_system_number", "INT"),
        ]
        
        for table_name, column_name, column_type in missing_columns:
            try:
                # Check if column exists
                cursor.execute(f"""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = '{table_name}' 
                    AND COLUMN_NAME = '{column_name}'
                """)
                
                if cursor.fetchone()[0] == 0:
                    # Column doesn't exist, add it
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                    logging.info(f"✅ Added {column_name} to {table_name}")
                else:
                    logging.info(f"ℹ️ Column {column_name} already exists in {table_name}")
                    
            except mysql.connector.Error as e:
                logging.warning(f"⚠️ Could not add {column_name} to {table_name}: {e}")
                
    except Exception as e:
        logging.error(f"❌ Error adding missing columns: {e}")

def insert_sample_bin_data(connection):
    """Insert sample bin location data based on your SAP B1 examples"""
    cursor = connection.cursor()
    
    try:
        # Real bin codes from your SAP B1 data
        sample_bins = [
            ('7000-FG-SYSTEM-BIN-LOCATION', '7000-FG', 'System bin location for finished goods', True, True),
            ('7000-FG-C411', '7000-FG', 'Finished goods bin C411', True, False),
            ('7000-FG-C511', '7000-FG', 'Finished goods bin C511', True, False),
            ('7000-FG-C810', '7000-FG', 'Finished goods bin C810', True, False),
            ('WH001-BIN-01', 'WH001', 'Main warehouse bin 01', True, False),
            ('WH001-BIN-02', 'WH001', 'Main warehouse bin 02', True, False),
        ]
        
        for bin_code, warehouse_code, description, is_active, is_system_bin in sample_bins:
            cursor.execute("""
                INSERT IGNORE INTO bin_locations 
                (bin_code, warehouse_code, description, is_active, is_system_bin) 
                VALUES (%s, %s, %s, %s, %s)
            """, (bin_code, warehouse_code, description, is_active, is_system_bin))
        
        # Insert sample bin items based on your BatchNumberDetails data
        sample_items = [
            ('7000-FG-C411', '1248-109226', 'Araymond-9.00 x 2.00-7SF2081', '483108857', 25.0, 'EA'),
            ('7000-FG-C511', '1248-109234', 'Araymond-9.60 x 2.50-7SF2081', '483125004', 18.0, 'EA'),
            ('7000-FG-C810', '1248-109242', 'Araymond-9.60 x 2.00-6DF1882', '483229468', 22.0, 'EA'),
            ('7000-FG-SYSTEM-BIN-LOCATION', 'CO0726Y', 'COATED LOWER PLATE', '20220729', 12.0, 'EA'),
            ('7000-FG-SYSTEM-BIN-LOCATION', 'CO0098Y', 'Big Aluminium Insert Coated RR AC0101', '20220729', 8.5, 'EA'),
        ]
        
        for bin_code, item_code, item_name, batch_number, quantity, uom in sample_items:
            cursor.execute("""
                INSERT IGNORE INTO bin_items 
                (bin_code, item_code, item_name, batch_number, quantity, available_quantity, uom, warehouse_code, batch_attribute2) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (bin_code, item_code, item_name, batch_number, quantity, quantity, uom, '7000-FG', bin_code))
        
        logging.info("✅ Sample bin location and item data inserted")
        connection.commit()
        
    except mysql.connector.Error as e:
        logging.error(f"❌ Error inserting sample data: {e}")
    finally:
        cursor.close()

def main():
    """Main migration function"""
    print("🚀 Starting MySQL Bin Scanning Migration...")
    print(f"📅 Migration started at: {datetime.now()}")
    
    # Get database connection
    connection = get_mysql_connection()
    if not connection:
        print("❌ Failed to connect to database. Please check your MySQL configuration.")
        return False
    
    try:
        # Create tables
        create_bin_scanning_tables(connection)
        
        # Insert sample data
        insert_sample_bin_data(connection)
        
        print("🎉 Bin scanning migration completed successfully!")
        print("📋 Tables created:")
        print("   - bin_locations: Store bin information")
        print("   - bin_items: Track items in bins with SAP integration")
        print("   - bin_scanning_logs: Audit trail for bin scans")
        print("🔧 Missing columns added to existing tables")
        print("📦 Sample bin data inserted for testing")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Migration failed: {e}")
        return False
        
    finally:
        connection.close()
        logging.info("🔌 Database connection closed")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)